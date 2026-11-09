"""Assert the exact, reproducible synthetic D2 pipeline invariants in the real DB."""
import hashlib
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from documents.models import Document, Invoice, ProcessingRun, QualityIssue
from documents.pipeline.fixtures import example_files
from documents.pipeline import PIPELINE_VERSION


class Command(BaseCommand):
    help = "Verify 3 accepted synthetic invoices, 1 quarantined anomaly and idempotence."

    def handle(self, *args, **opts):
        if settings.DEMO_READONLY:
            raise CommandError("D2 verification cannot run in the public read-only demo.")
        documents = []
        expected = {}
        for name, raw in example_files():
            digest = hashlib.sha256(raw).hexdigest()
            doc = Document.objects.filter(sha256=digest).first()
            if doc is None:
                raise CommandError(f"Fixture missing: {name}; run seed_d2 --process")
            documents.append(doc)
            expected[doc.pk] = "REJECTED" if "anomalie" in name else "ACCEPTED"
        for doc in documents:
            if doc.state != expected[doc.pk]:
                raise CommandError(f"{doc.original_name}: unexpected state {doc.state}")
            runs = ProcessingRun.objects.filter(document=doc, pipeline_version=PIPELINE_VERSION)
            if runs.count() != 1:
                raise CommandError(f"{doc.original_name}: expected one idempotent versioned run")
            if runs.first().attempt_number != 1:
                raise CommandError(f"{doc.original_name}: duplicate processing occurred")
        invoices = Invoice.objects.filter(document__in=documents)
        if invoices.count() != 3:
            raise CommandError(f"Expected 3 accepted invoices, got {invoices.count()}")
        total = sum((item.total for item in invoices), Decimal("0.00"))
        if total != Decimal("240.00"):
            raise CommandError(f"Expected exact synthetic TTC=240.00 EUR, got {total}")
        rejected = next(doc for doc in documents if doc.state == "REJECTED")
        if invoices.filter(document=rejected).exists():
            raise CommandError("Rejected data incorrectly contributes to invoices")
        if not QualityIssue.objects.filter(
            run__document=rejected, code="TOTAL_MISMATCH"
        ).exists():
            raise CommandError("The intentional mismatch must remain visible")
        self.stdout.write(self.style.SUCCESS(
            "D2 LOCAL VERIFIED: 3 accepted / 1 rejected / 3 invoices / TTC 240.00 EUR / replay idempotent"
        ))
        return None
