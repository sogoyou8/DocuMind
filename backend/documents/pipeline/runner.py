"""D2 processing coordinator: database-locked, repeatable and traceable.

All persistent changes for one document version share a transaction. Any
ERROR quarantines the whole document: no partial invoice enters reporting.
"""
import hashlib
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from documents.models import (
    AuditEvent, Document, ExtractedRecord, Invoice, ProcessingRun,
    QualityIssue, Supplier,
)
from . import PIPELINE_VERSION
from .extraction import ExtractionError, MAX_SOURCE_BYTES, extract_records
from .normalization import normalize_invoice


class ProcessingNotAllowed(ValueError):
    """Raised for a forbidden or impossible D2 operation."""


@transaction.atomic
def process_document(document_id, *, force=False, actor=None):
    """Return (run, skipped); idempotency key: document + pipeline version.

    The document row is locked for PostgreSQL concurrency. Reprocessing only
    occurs when force=True, and then replaces all previous derived rows
    atomically. Historical audit events remain intact.
    """
    if settings.DEMO_READONLY:
        raise ProcessingNotAllowed("Le serveur public de démonstration n'exécute aucun pipeline.")

    document = Document.objects.select_for_update().get(pk=document_id)
    if document.source != Document.Source.UPLOAD or not document.blob.name:
        raise ProcessingNotAllowed("Seuls les imports locaux avec fichier privé sont traités.")

    run, created = ProcessingRun.objects.get_or_create(
        document=document, pipeline_version=PIPELINE_VERSION,
        defaults={"status": ProcessingRun.Status.RUNNING},
    )
    if not created:
        if not force:
            return run, True
        run.attempt_number += 1

    run.status = ProcessingRun.Status.RUNNING
    run.error_summary = ""
    run.finished_at = None
    run.save(update_fields=["status", "error_summary", "finished_at", "attempt_number"])
    document.state = Document.State.VALIDATING
    document.save(update_fields=["state"])
    # Cascades clear prior invoice and issue rows for this exact version.
    run.records.all().delete()
    run.issues.all().delete()

    problems: list[tuple[ExtractedRecord | None, str, dict]] = []
    staged: list[tuple[ExtractedRecord, dict[str, str]]] = []

    try:
        with document.blob.storage.open(document.blob.name, "rb") as source:
            source_bytes = source.read(MAX_SOURCE_BYTES + 1)
        if len(source_bytes) != document.size_bytes:
            raise ExtractionError("SOURCE_SIZE_MISMATCH", "Taille modifiée depuis l'import.")
        if hashlib.sha256(source_bytes).hexdigest() != document.sha256:
            raise ExtractionError("SOURCE_HASH_MISMATCH", "Empreinte SHA-256 modifiée depuis l'import.")
        extracted = extract_records(source_bytes, document.file_type)
        seen_keys: set[tuple[str, str, str]] = set()
        for item in extracted:
            normalized = normalize_invoice(item.fields)
            record = ExtractedRecord.objects.create(
                document=document, run=run, source_locator=item.source_locator,
                raw_fields=item.fields, normalized_fields=normalized.fields,
            )
            for detail in normalized.issues:
                problems.append((record, item.source_locator, detail))
            if normalized.issues:
                continue

            values = normalized.fields
            key = (values["supplier_key"], values["number"], values["issued_on"])
            if key in seen_keys:
                problems.append((record, item.source_locator, {
                    "code": "DUPLICATE_IN_DOCUMENT", "field": "number",
                    "severity": "ERROR", "message": "Facture déjà présente dans ce document.",
                }))
                continue
            seen_keys.add(key)
            if Invoice.objects.filter(
                supplier__canonical_key=key[0], invoice_number=key[1],
                issued_on=date.fromisoformat(key[2]),
            ).exclude(run=run).exists():
                problems.append((record, item.source_locator, {
                    "code": "DUPLICATE_IN_DATABASE", "field": "number",
                    "severity": "ERROR", "message": "Facture déjà validée dans un autre document.",
                }))
                continue
            staged.append((record, values))
    except ExtractionError as exc:
        problems.append((None, "", {
            "code": exc.code, "field": "file", "severity": "ERROR",
            "message": str(exc),
        }))
    except (OSError, IOError) as exc:
        problems.append((None, "", {
            "code": "SOURCE_UNAVAILABLE", "field": "file", "severity": "ERROR",
            "message": "Fichier privé indisponible ou illisible.",
        }))

    for record, locator, detail in problems:
        QualityIssue.objects.create(
            run=run, record=record, source_locator=locator,
            code=detail["code"], field_name=detail["field"],
            severity=detail["severity"], message=detail["message"],
        )

    if problems:
        document.state = Document.State.REJECTED
        run.status = ProcessingRun.Status.REJECTED
        run.error_summary = problems[0][2]["message"][:500]
        action = "PROCESSING_REJECTED"
    else:
        for record, values in staged:
            supplier, _ = Supplier.objects.get_or_create(
                canonical_key=values["supplier_key"],
                defaults={"name": values["supplier"]},
            )
            Invoice.objects.create(
                document=document, run=run, record=record, supplier=supplier,
                invoice_number=values["number"],
                issued_on=date.fromisoformat(values["issued_on"]),
                currency=values["currency"],
                subtotal=Decimal(values["subtotal"]), tax=Decimal(values["tax"]),
                total=Decimal(values["total"]),
            )
        document.state = Document.State.ACCEPTED
        run.status = ProcessingRun.Status.SUCCEEDED
        action = "PROCESSING_ACCEPTED"

    run.finished_at = timezone.now()
    run.save(update_fields=["status", "error_summary", "finished_at"])
    document.save(update_fields=["state"])
    AuditEvent.objects.create(
        document=document, actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
    )
    return run, False
