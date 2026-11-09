"""Similarity retrieval is subject to a PostgreSQL source-of-truth gate."""
import re
import unicodedata
from uuid import UUID

from documents.models import ChunkReference, Document, ProcessingRun
from . import INDEX_VERSION
from .security import hostile_instruction, safe_excerpt

MAX_DISTANCE = 0.65
STOPWORDS = {
    "avec", "dans", "dont", "pour", "quel", "quelle", "quels", "quelles",
    "combien", "est", "sont", "les", "des", "une", "un", "la", "le",
    "du", "de", "sur", "qui", "quoi", "date", "document", "documents",
    "donne", "donnez", "moi", "cette", "ce", "the", "what", "is",
}


def _tokens(text: str):
    normalized = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return {
        token for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) >= 3 and token not in STOPWORDS
    }


def search(question, *, store=None, model=None, limit=4, max_distance=MAX_DISTANCE):
    if store is None:
        from .store import collection
        store = collection()
    if model is None:
        from .ollama import LocalOllama
        model = LocalOllama()
    size = store.count()
    if not size:
        return []
    vector = model.embed([question])[0]
    result = store.query(
        query_embeddings=[vector], n_results=min(max(limit * 3, 4), size),
        include=["documents", "metadatas", "distances"],
    )
    ids = (result.get("ids") or [[]])[0]
    texts = (result.get("documents") or [[]])[0]
    metadata = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    try:
        valid_uuids = [UUID(id_) for id_ in ids]
    except (TypeError, ValueError, AttributeError):
        # Malformed vector IDs must never be accepted as evidence.
        return []
    refs = {
        str(row.id): row
        for row in ChunkReference.objects.select_related(
            "document", "run", "record"
        ).filter(id__in=valid_uuids)
    }
    words = _tokens(question)
    found = []
    for id_, passage, meta, distance in zip(ids, texts, metadata, distances):
        ref = refs.get(str(id_))
        if not ref or not isinstance(passage, str) or not isinstance(meta, dict):
            continue
        if not isinstance(distance, (int, float)) or not 0 <= distance <= max_distance:
            continue
        doc, run, record = ref.document, ref.run, ref.record
        if not (
            doc.source == Document.Source.UPLOAD
            and doc.state == Document.State.INDEXED
            and run.status == ProcessingRun.Status.SUCCEEDED
            and run.document_id == doc.id
            and record.document_id == doc.id
            and record.run_id == run.id
            and ref.run_id == run.id
            and ref.record_id == record.id
            and ref.index_version == INDEX_VERSION
            and ref.embedding_model == model.embed_model
            and ref.content_sha256 == meta.get("content_sha256")
            and doc.sha256 == meta.get("document_sha256")
            and str(doc.id) == meta.get("document_id")
            and str(run.id) == meta.get("run_id")
            and str(record.id) == meta.get("record_id")
            and ref.source_locator == meta.get("source_locator")
        ):
            continue
        # Basic lexical relevance is a SECOND filter on top of cosine score.
        # This blocks unsupported unknown invoice IDs even if vectors are close.
        if words and not words.intersection(_tokens(passage)):
            continue
        if hostile_instruction(passage):
            continue
        found.append({
            "id": f"E{len(found) + 1}", "document_id": str(doc.id),
            "document": doc.original_name, "source_locator": ref.source_locator,
            "text": passage, "excerpt": safe_excerpt(passage),
            "score": round(1.0 - float(distance), 4),
        })
        if len(found) == limit:
            break
    return found
