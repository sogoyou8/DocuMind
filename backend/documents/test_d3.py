"""D3 integration and regression suite. PostgreSQL only for SQL view tests."""
import hashlib
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest import skipUnless

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings

from .bi.fixtures import d3_example_files, synthetic_expected_monthly
from .models import Document, Invoice, QualityIssue
from .pipeline.runner import process_document


@skipUnless(connection.vendor == "postgresql", "PostgreSQL BI views only")
@override_settings(DEMO_READONLY=False)
class D3AnalyticsTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        media = override_settings(MEDIA_ROOT=Path(self.tmp.name))
        media.enable()
        self.addCleanup(media.disable)

    def test_sql_views_and_orm_reconcile(self):
        call_command("seed_d3", process=True, verbosity=0)
        call_command("verify_d3", verbosity=0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*), SUM(total) FROM bi.validated_invoices")
            self.assertEqual(cursor.fetchone(), (15, Decimal("1344.00")))
            cursor.execute("SELECT COUNT(*) FROM bi.document_quality")
            self.assertEqual(cursor.fetchone()[0], 9)
            cursor.execute("SELECT COUNT(*) FROM bi.quality_issues")
            self.assertEqual(cursor.fetchone()[0], 2)
            cursor.execute("SELECT COUNT(*) FROM bi.currency_totals")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_sql_monthly_is_exact_and_replays_do_not_inflate(self):
        call_command("seed_d3", process=True, verbosity=0)
        call_command("seed_d3", process=True, verbosity=0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_char(month,'YYYY-MM'),total FROM bi.spending_monthly ORDER BY month")
            self.assertEqual(dict(cursor.fetchall()), synthetic_expected_monthly())
        self.assertEqual(Invoice.objects.count(), 15)
        call_command("verify_d3", verbosity=0)

    def test_rejected_document_does_not_create_financial_kpi(self):
        call_command("seed_d3", process=True, verbosity=0)
        faulty = Document.objects.get(original_name="documind-d3-anomalie.csv")
        self.assertEqual(faulty.state, Document.State.REJECTED)
        self.assertFalse(Invoice.objects.filter(document=faulty).exists())
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bi.validated_invoices WHERE document_id=%s", [faulty.id])
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute("SELECT issue_code FROM bi.quality_issues WHERE document_id=%s", [faulty.id])
            self.assertEqual(cursor.fetchone()[0], "TOTAL_MISMATCH")

    def test_supplier_and_currency_no_double_count(self):
        call_command("seed_d3", process=True, verbosity=0)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT supplier_name, SUM(total) FROM bi.validated_invoices "
                "GROUP BY supplier_name ORDER BY supplier_name"
            )
            self.assertEqual(
                dict(cursor.fetchall()),
                {
                    "Atelier Fictif": Decimal("588.00"),
                    "Imprimerie Fictive": Decimal("270.00"),
                    "Librairie Fictive": Decimal("486.00"),
                },
            )
            cursor.execute("SELECT SUM(total) FROM bi.spending_suppliers")
            self.assertEqual(cursor.fetchone()[0], Decimal("1344.00"))
            cursor.execute("SELECT SUM(total) FROM bi.spending_monthly")
            self.assertEqual(cursor.fetchone()[0], Decimal("1344.00"))

    def test_additional_currency_is_separate_not_converted(self):
        call_command("seed_d3", process=True, verbosity=0)
        raw = (
            b"supplier,invoice_number,date,currency,subtotal,tax,total\n"
            b"Test Vendor,D3-USD-1,2026-10-15,USD,10,2,12\n"
        )
        doc = Document.objects.create(
            original_name="d3-extra-usd.csv", file_type="CSV",
            sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw), blob=ContentFile(raw, name="d3-extra-usd.csv"),
        )
        process_document(doc.pk)
        with connection.cursor() as cursor:
            cursor.execute("SELECT currency, total FROM bi.currency_totals")
            self.assertEqual(
                dict(cursor.fetchall()),
                {"EUR": Decimal("1344.00"), "USD": Decimal("12.00")},
            )
            cursor.execute("SELECT COUNT(*) FROM bi.validated_invoices")
            self.assertEqual(cursor.fetchone()[0], 16)
        call_command("verify_d3", verbosity=0)

    def test_multiple_issues_do_not_duplicate_documents_or_invoices(self):
        call_command("seed_d3", process=True, verbosity=0)
        faulty = Document.objects.get(original_name="documind-d3-anomalie.csv")
        run = faulty.processing_runs.get()
        QualityIssue.objects.create(
            run=run, code="ADDITIONAL_WARNING", severity="ERROR",
            field_name="file", message="Synthetic secondary diagnostic",
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bi.document_quality WHERE document_id=%s", [faulty.id])
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor.execute("SELECT issue_count FROM bi.document_quality WHERE document_id=%s", [faulty.id])
            self.assertEqual(cursor.fetchone()[0], 2)
            cursor.execute("SELECT COUNT(*) FROM bi.validated_invoices")
            self.assertEqual(cursor.fetchone()[0], 15)
