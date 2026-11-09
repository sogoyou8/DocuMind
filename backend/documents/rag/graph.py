"""Explicit LangGraph RAG: retrieve -> generate -> verify or abstain."""
import json
import re
from decimal import Decimal, InvalidOperation
from typing import TypedDict

from . import ABSTENTION
from .security import hostile_instruction, require_d4


class RAGState(TypedDict, total=False):
    question: str
    evidence: list[dict]
    raw_answer: str
    answer: str
    citations: list[dict]
    status: str


def _numbers(text: str):
    numbers = set()
    for token in re.findall(r"(?<![\w])\d+(?:[.,]\d+)?(?![\w])", text):
        try:
            numbers.add(Decimal(token.replace(",", ".")).normalize())
        except InvalidOperation:
            pass
    return numbers


def _validate(raw: str, evidence: list[dict]):
    """No model-origin citation is trusted: identifiers are server allowlisted."""
    try:
        result = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(result, dict):
        return None
    response = result.get("answer")
    used = result.get("evidence_ids")
    if (not isinstance(response, str) or not 1 <= len(response.strip()) <= 650
            or not isinstance(used, list) or not used or len(used) > 4
            or any(not isinstance(ref, str) for ref in used)):
        return None
    if hostile_instruction(response) or re.search(r"https?://|(?:api[_ -]?key|password|mot de passe)", response, re.I):
        return None
    known = {item["id"]: item for item in evidence}
    if len(set(used)) != len(used) or any(item not in known for item in used):
        return None
    referenced = [known[key] for key in used]
    # Reject numbers not visible in the retrieved, validated source passages.
    grounded_numbers = _numbers(" ".join(item["text"] for item in referenced))
    if _numbers(response) - grounded_numbers:
        return None
    citations = [
        {
            "id": item["id"], "document_id": item["document_id"],
            "document": item["document"],
            "source_locator": item["source_locator"],
            "excerpt": item["excerpt"],
        }
        for item in referenced
    ]
    return response.strip(), citations


def answer_question(question: str, *, store=None, model=None, retriever=None):
    require_d4()
    if not isinstance(question, str) or not 4 <= len(question.strip()) <= 500:
        raise ValueError("Question attendue entre 4 et 500 caractères.")
    if hostile_instruction(question):
        return {"status": "abstained", "answer": ABSTENTION, "citations": []}

    # D4 is source QA, not a free-form SQL calculator. Financial aggregates
    # must come from audited D3 SQL, not model-generated arithmetic.
    if re.search(r"(?i)\b(?:somme|total\s+(?:global|des|de\s+toutes)|additionne|"
                 r"moyenne\s+globale|aggregate|sum\s+of\s+all)\b", question):
        return {"status": "abstained", "answer": ABSTENTION, "citations": []}

    if model is None:
        from .ollama import LocalOllama
        model = LocalOllama()
    if retriever is None:
        from .search import search
        retriever = lambda q: search(q, store=store, model=model)

    from langgraph.graph import StateGraph, START, END

    def retrieve(state: RAGState):
        results = retriever(state["question"])
        # Unknown references and invoice numbers are not answered by analogy.
        identifiers = re.findall(
            r"\b[A-Za-z]{2,}[A-Za-z0-9]*[-_]\d+[A-Za-z0-9-]*\b",
            state["question"],
        )
        if identifiers and not any(
            all(token.casefold() in e["text"].casefold() for token in identifiers)
            for e in results
        ):
            results = []
        return {"evidence": results}

    def route(state: RAGState):
        return "generate" if state.get("evidence") else "abstain"

    def abstain(state: RAGState):
        return {"status": "abstained", "answer": ABSTENTION, "citations": []}

    def generate(state: RAGState):
        return {
            "raw_answer": model.generate(state["question"], state["evidence"]),
        }

    def verify(state: RAGState):
        result = _validate(state.get("raw_answer", ""), state["evidence"])
        if result is None:
            return {"status": "abstained", "answer": ABSTENTION, "citations": []}
        answer, citations = result
        return {"status": "answered", "answer": answer, "citations": citations}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("abstain", abstain)
    graph.add_node("generate", generate)
    graph.add_node("verify", verify)
    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges("retrieve", route, {
        "generate": "generate", "abstain": "abstain",
    })
    graph.add_edge("generate", "verify")
    graph.add_edge("verify", END)
    graph.add_edge("abstain", END)
    output = graph.compile().invoke({"question": question.strip()})
    return {
        "status": output["status"],
        "answer": output["answer"],
        "citations": output["citations"],
    }
