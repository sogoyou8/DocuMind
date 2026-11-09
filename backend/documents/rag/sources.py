"""Stable chunking of actual D2 validated records; never synthesize facts."""
import hashlib
from documents.rag import INDEX_VERSION

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80
MAX_CHUNKS_PER_RECORD = 16
MAX_CHUNKS_PER_DOCUMENT = 160


def source_text(record):
    raw = record.raw_fields or {}
    norm = record.normalized_fields or {}
    if "_page_text" in raw:
        # Native PDF text, page-local. Do not duplicate extracted key:value pairs.
        text = str(raw["_page_text"]).strip()
    else:
        text = "\n".join(
            f"{key}: {value}" for key, value in raw.items()
            if value is not None and str(value).strip()
        )
    # Grounded normalization from D2, never a generated or inferred amount.
    extras = []
    labels = {
        "supplier": "Fournisseur", "number": "Numéro facture",
        "issued_on": "Date facture", "currency": "Devise",
        "subtotal": "Montant HT", "tax": "TVA", "total": "Montant TTC",
    }
    for key, label in labels.items():
        if norm.get(key):
            extras.append(f"{label}: {norm[key]}")
    if extras:
        text = text + "\n" + "\n".join(extras)
    return text.strip()


def split_passages(text: str):
    """Deterministic overlapping windows, bounded for small local AI models."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    result = []
    start = 0
    while start < len(text) and len(result) < MAX_CHUNKS_PER_RECORD:
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            natural_break = max(text.rfind("\n", start + 300, end),
                                text.rfind(" ", start + 300, end))
            if natural_break > start + 300:
                end = natural_break
        segment = text[start:end].strip()
        if segment:
            result.append(segment)
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    if start < len(text) - CHUNK_SIZE and len(result) == MAX_CHUNKS_PER_RECORD:
        # Truncation is explicit rather than silently dropping source content.
        raise ValueError("La source dépasse la limite de 16 extraits par ligne/page.")
    return result


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
