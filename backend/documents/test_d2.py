"""D2 regression tests. Run locally with PostgreSQL, without GitHub Actions."""
import hashlib
from decimal import Decimal
from io import StringIO
from pathlib import Path
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from .models import Document, ProcessingRun, ExtractedRecord, QualityIssue, Invoice
from .pipeline.extraction import ExtractionError, extract_records
from .pipeline.fixtures import example_files, make_text_pdf
from .pipeline.normalization import normalize_invoice
from .pipeline.runner import ProcessingNotAllowed, process_document


class NormalizationTests(SimpleTestCase):
    def test_french_aliases_and_comma_decimals(self):
        row = normalize_invoice({
            "Fournisseur": "Exemple SARL", "Numéro facture": "INV-123",
            "Date facture": "09/11/2026", "Devise": "eur",
            "Total HT": "1 000,00", "TVA": "200,00", "Total TTC": "1 200,00",
        })
        self.assertTrue(row.valid, row.issues)
        self.assertEqual(row.fields["total"], "1200.00")
        self.assertEqual(row.fields["issued_on"], "2026-11-09")
        self.assertEqual(row.fields["supplier_key"], "exemple_sarl")

    def test_missing_required_field_rejected_without_invention(self):
        row = normalize_invoice({"supplier": "Test"})
        self.assertFalse(row.valid)
        self.assertIn("MISSING_FIELD", {issue["code"] for issue in row.issues})
        self.assertNotIn("total", row.fields)

    def test_incoherent_ht_tva_ttc(self):
        row = normalize_invoice({
            "supplier": "Test", "invoice_number": "A-10",
            "date": "2026-11-09", "currency": "EUR",
            "subtotal": "10", "tax": "2", "total": "30",
        })
        self.assertIn("TOTAL_MISMATCH", {issue["code"] for issue in row.issues})

    def test_invalid_currency_and_date(self):
        row = normalize_invoice({
            "supplier": "Test", "invoice_number": "A-10",
            "date": "2026-99-99", "currency": "CAD",
            "subtotal": "10", "tax": "2", "total": "12",
        })
        self.assertEqual(
            {"INVALID_DATE", "INVALID_CURRENCY"},
            {issue["code"] for issue in row.issues},
        )


class ExtractionTests(SimpleTestCase):
    def test_three_real_file_formats(self):
        samples = example_files()
        self.assertEqual(len(samples), 4)
        for filename, payload in samples[:3]:
            with self.subTest(filename=filename):
                ext = filename.rsplit(".", 1)[-1].upper()
                rows = extract_records(payload, ext)
                self.assertEqual(len(rows), 1)
                self.assertTrue(rows[0].source_locator.startswith(ext.lower() + ":"))
                self.assertTrue(normalize_invoice(rows[0].fields).valid)

    def test_pdf_without_text_is_rejected(self):
        from pypdf import PdfWriter
        from io import BytesIO
        out = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        writer.write(out)
        with self.assertRaises(ExtractionError) as error:
            extract_records(out.getvalue(), "PDF")
        self.assertEqual(error.exception.code, "PDF_NO_TEXT")

    def test_csv_bad_header_rejected(self):
        with self.assertRaises(ExtractionError) as error:
            extract_records(b"supplier,,date\nA,B,C\n", "CSV")
        self.assertEqual(error.exception.code, "INVALID_HEADER")

    def test_row_limit(self):
        raw = b"invoice\n" + b"any-value\n" * 5001
        with self.assertRaises(ExtractionError) as error:
            extract_records(raw, "CSV")
        self.assertEqual(error.exception.code, "ROW_LIMIT")


@override_settings(DEMO_READONLY=False)
class PipelineTests(TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        override = override_settings(MEDIA_ROOT=Path(self.folder.name))
        override.enable()
        self.addCleanup(override.disable)
        self.sample_files = {name: data for name, data in example_files()}

    def create_doc(self, filename, data=None):
        data = self.sample_files[filename] if data is None else data
        return Document.objects.create(
            original_name=filename, sha256=hashlib.sha256(data).hexdigest(),
            file_type=filename.rsplit(".", 1)[-1].upper(),
            size_bytes=len(data), source=Document.Source.UPLOAD,
            blob=ContentFile(data, name=filename),
        )

    def test_success_pdf_csv_xlsx_and_provenance(self):
        for name in list(self.sample_files)[:3]:
            doc = self.create_doc(name)
            run, skipped = process_document(doc.id)
            self.assertFalse(skipped)
            self.assertEqual(run.status, ProcessingRun.Status.SUCCEEDED)
            self.assertEqual(run.records.count(), 1)
            self.assertEqual(run.invoices.count(), 1)
            self.assertEqual(run.issues.count(), 0)
            doc.refresh_from_db()
            self.assertEqual(doc.state, Document.State.ACCEPTED)
        self.assertEqual(Invoice.objects.count(), 3)
        self.assertEqual(ExtractedRecord.objects.count(), 3)
        self.assertEqual(Decimal(str(sum(invoice.total for invoice in Invoice.objects.all()))),
                         Decimal("240.00"))

    def test_repeat_and_forced_retry_are_idempotent(self):
        name = "demo-d2-facture-valide.csv"
        doc = self.create_doc(name)
        first, skipped = process_document(doc.pk)
        self.assertFalse(skipped)
        second, skipped = process_document(doc.pk)
        self.assertTrue(skipped)
        self.assertEqual(first.pk, second.pk)
        third, skipped = process_document(doc.pk, force=True)
        self.assertFalse(skipped)
        self.assertEqual(third.pk, first.pk)
        self.assertEqual(third.attempt_number, 2)
        self.assertEqual(ProcessingRun.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(ExtractedRecord.objects.count(), 1)

    def test_anomaly_quarantines_document_and_excludes_invoice(self):
        doc = self.create_doc("demo-d2-facture-anomalie.csv")
        run, _ = process_document(doc.id)
        self.assertEqual(run.status, ProcessingRun.Status.REJECTED)
        self.assertIn("TOTAL_MISMATCH", set(run.issues.values_list("code", flat=True)))
        self.assertEqual(run.records.count(), 1)
        self.assertEqual(run.invoices.count(), 0)
        doc.refresh_from_db()
        self.assertEqual(doc.state, Document.State.REJECTED)

    def test_duplicate_invoice_across_documents_rejected(self):
        source = self.sample_files["demo-d2-facture-valide.csv"]
        first = self.create_doc("demo-d2-facture-valide.csv")
        process_document(first.pk)
        other = source.replace(b"120.00\n", b"120.00\n\n")
        second = self.create_doc("other.csv", other)
        run, _ = process_document(second.id)
        self.assertEqual(run.status, ProcessingRun.Status.REJECTED)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertIn("DUPLICATE_IN_DATABASE",
                      set(run.issues.values_list("code", flat=True)))

    def test_sha256_tampering_detected(self):
        doc = self.create_doc("demo-d2-facture-valide.csv")
        doc.sha256 = "0" * 64
        doc.save(update_fields=["sha256"])
        run, _ = process_document(doc.pk)
        self.assertEqual(run.status, ProcessingRun.Status.REJECTED)
        self.assertIn("SOURCE_HASH_MISMATCH",
                      set(run.issues.values_list("code", flat=True)))

    def test_operator_process_api_and_traceable_read_endpoints(self):
        doc = self.create_doc("demo-d2-facture-valide.csv")
        user = get_user_model().objects.create_user(username="operator-d2", password="secret-unique-test")
        group, _ = Group.objects.get_or_create(name="documind_operator")
        user.groups.add(group)
        client = APIClient()
        client.force_authenticate(user)
        result = client.post(f"/api/v1/documents/{doc.pk}/process/", {}, format="json")
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["status"], "SUCCEEDED")
        self.assertEqual(result.data["invoices_count"], 1)
        for path in ("processing-runs", "records", "quality-issues", "invoices"):
            res = client.get(f"/api/v1/{path}/?document={doc.pk}")
            self.assertEqual(res.status_code, 200, (path, res.data))
        self.assertEqual(client.get(f"/api/v1/invoices/?document={doc.pk}").data["count"], 1)
        self.assertEqual(client.get(f"/api/v1/quality-issues/?document={doc.pk}").data["count"], 0)

    def test_seed_and_batch_are_repeatable(self):
        with self.settings(DEMO_READONLY=False):
            call_command("seed_d2", process=True, stdout=StringIO())
            self.assertEqual(Invoice.objects.count(), 3)
            self.assertEqual(Document.objects.filter(state=Document.State.REJECTED).count(), 1)
            call_command("seed_d2", process=True, stdout=StringIO())
            call_command("process_pending", limit=20, stdout=StringIO())
            self.assertEqual(Invoice.objects.count(), 3)
            self.assertEqual(Document.objects.count(), 4)

    def test_public_demo_never_exposes_d2_records_and_rejects_processing(self):
        doc = self.create_doc("demo-d2-facture-valide.csv")
        process_document(doc.id)
        client = APIClient()
        with self.settings(DEMO_READONLY=True):
            self.assertEqual(client.get("/api/v1/invoices/").data["count"], 0)
            self.assertEqual(client.get("/api/v1/records/").data["count"], 0)
            self.assertEqual(client.get("/api/v1/processing-runs/").data["count"], 0)
            self.assertEqual(client.get("/api/v1/quality-issues/").data["count"], 0)
            self.assertEqual(client.post(f"/api/v1/documents/{doc.id}/process/", {}, format="json").status_code, 403)
            with self.assertRaises(ProcessingNotAllowed):
                process_document(doc.id)

    def test_nonoperator_cannot_start_processing(self):
        doc = self.create_doc("demo-d2-facture-valide.csv")
        user = get_user_model().objects.create_user(username="analyst-d2", password="secret-unique-test")
        client = APIClient()
        client.force_authenticate(user)
        res = client.post(f"/api/v1/documents/{doc.pk}/process/", {}, format="json")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(ProcessingRun.objects.count(), 0)

    def test_invalid_document_uuid_filter_is_400(self):
        user = get_user_model().objects.create_user(username="analyst-uuid", password="secret-unique-test")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/v1/invoices/?document=invalid").status_code, 400)
