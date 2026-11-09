"""Versioned idempotent indexer, tied to accepted D2 document+run+record."""
import uuid
from django.db import transaction

from documents.models import AuditEvent, ChunkReference, Document, ProcessingRun
from . import INDEX_VERSION
from .security import require_d4
from .sources import MAX_CHUNKS_PER_DOCUMENT, source_text, split_passages, digest


class IndexNotAllowed(ValueError):
    pass


@transaction.atomic
def index_document(document_id, *, force=False, store=None, model=None):
    """Index accepted source records. Dangling Chroma vectors never grant access.

    Database state is authoritative, so a failed/changing index is never used
    for answers. Document and its processing run are validated under row lock.
    """
    require_d4()
    doc = Document.objects.select_for_update().get(pk=document_id)
    if doc.source != Document.Source.UPLOAD or doc.state not in (
        Document.State.ACCEPTED, Document.State.INDEXED
    ):
        raise IndexNotAllowed("Seuls les documents validés peuvent être indexés.")
    run = doc.processing_runs.filter(
        status=ProcessingRun.Status.SUCCEEDED
    ).order_by("-started_at").first()
    if run is None:
        raise IndexNotAllowed("Aucun traitement D2 validé pour ce document.")
    records = list(run.records.order_by("source_locator", "id"))
    if not records:
        raise IndexNotAllowed("Le document ne contient aucun extrait D2 validé.")
    if store is None:
        from .store import collection
        store = collection()
    if model is None:
        from .ollama import LocalOllama
        model = LocalOllama()

    chunks = []
    for record in records:
        text = source_text(record)
        if not text:
            raise IndexNotAllowed("Extrait vide : indexation refusée.")
        for number, passage in enumerate(split_passages(text)):
            chunks.append((
                record, number, passage,
                str(uuid.uuid5(uuid.NAMESPACE_URL,
                    f"documind:{record.id}:{INDEX_VERSION}:{number}")),
            ))
            if len(chunks) > MAX_CHUNKS_PER_DOCUMENT:
                raise IndexNotAllowed("Un document ne peut dépasser 160 extraits.")
    if not chunks:
        raise IndexNotAllowed("Aucun texte exploitable.")
    expected_ids = [c[3] for c in chunks]
    refs = ChunkReference.objects.filter(
        document=doc, run=run, index_version=INDEX_VERSION,
        embedding_model=model.embed_model,
    )
    existing = {str(ref.id): ref for ref in refs}
    # On a Chroma volume loss, recreate the index automatically, even without
    # force; do not trust the historical INDEXED flag alone.
    stored_ids = set(store.get(ids=expected_ids)["ids"])
    if (not force and doc.state == Document.State.INDEXED
            and len(existing) == len(chunks) and
            stored_ids == set(expected_ids)
            and all(existing.get(item[3]) and
                    existing[item[3]].content_sha256 == digest(item[2])
                    for item in chunks)):
        return {"indexed_chunks": len(chunks), "skipped": True}

    # Embed before writing permanent pointers. A model outage cannot leave
    # document.state=INDEXED falsely after a transaction rollback.
    vectors = []
    for start in range(0, len(chunks), 8):
        vectors.extend(model.embed([item[2] for item in chunks[start:start + 8]]))
    if len(vectors) != len(chunks):
        raise IndexNotAllowed("Incohérence de la taille des embeddings.")

    docs = [item[2] for item in chunks]
    metadata = [{
        "document_id": str(doc.id), "document_sha256": doc.sha256,
        "record_id": str(rec.id), "run_id": str(run.id),
        "source_locator": rec.source_locator, "index_version": INDEX_VERSION,
        "content_sha256": digest(passage), "embedding_model": model.embed_model,
    } for rec, _, passage, _ in chunks]
    # Chroma writes and SQL are not a distributed transaction; a partial Chroma
    # write has no SQL reference and will be excluded by the retrieval gate.
    store.upsert(ids=expected_ids, embeddings=vectors,
                 documents=docs, metadatas=metadata)
    for rec, number, passage, ref_id in chunks:
        ChunkReference.objects.update_or_create(
            id=ref_id,
            defaults={
                "document": doc, "record": rec, "run": run,
                "source_locator": rec.source_locator,
                "chunk_index": number, "index_version": INDEX_VERSION,
                "embedding_model": model.embed_model,
                "content_sha256": digest(passage),
            },
        )
    # Prevent stale SQL pointers from being used after a re-index with changed
    # chunk counts. Foreign keys and source checks defend search separately.
    ChunkReference.objects.filter(document=doc, index_version=INDEX_VERSION).exclude(
        id__in=expected_ids
    ).delete()

    doc.state = Document.State.INDEXED
    doc.save(update_fields=["state"])
    AuditEvent.objects.create(document=doc, action="RAG_INDEXED")
    # Chroma dangling vectors from old versions remain inert: only current
    # valid SQL pointers and run/document status can authorize a citation.
    return {"indexed_chunks": len(chunks), "skipped": False}
