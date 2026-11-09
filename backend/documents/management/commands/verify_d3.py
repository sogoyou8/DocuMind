"""Independent SQL/ORM reconciliation of governed D3 BI views on PostgreSQL."""
import hashlib
from collections import Counter
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count, Sum

from documents.bi.fixtures import d3_example_files, synthetic_expected_monthly
from documents.models import Document, Invoice, QualityIssue
from documents.pipeline.fixtures import example_files


class Command(BaseCommand):
    help = "Validate D3 view grains, multi-month fixture, currency and source independence."

    def handle(self, *args, **options):
        if settings.DEMO_READONLY or connection.vendor != "postgresql":
            raise CommandError("D3 requires local PostgreSQL, never the Render demo.")
        fixture_ids = []
        for name, content in example_files() + d3_example_files():
            doc = Document.objects.filter(
                sha256=hashlib.sha256(content).hexdigest()
            ).first()
            if doc is None:
                raise CommandError(f"Missing fixture {name}; run seed_d3 --process")
            fixture_ids.append(doc.id)
        if len(set(fixture_ids)) != 9:
            raise CommandError("D3 requires nine distinct synthetic source documents.")

        valid_docs = Document.objects.filter(\n            id__in=fixture_ids, state__in=["ACCEPTED", "INDEXED"]\n        )
        rejected_docs = Document.objects.filter(id__in=fixture_ids, state="REJECTED")
        if valid_docs.count() != 7 or rejected_docs.count() != 2:
            raise CommandError("Expected seven accepted and two rejected documents.")
        invoices = Invoice.objects.filter(document_id__in=fixture_ids)
        if invoices.count() != 15 or invoices.aggregate(total=Sum("total"))["total"] != Decimal("1344.00"):
            raise CommandError("Expected exactly fifteen accepted synthetic invoices and 1344 EUR TTC.")
        if invoices.exclude(currency="EUR").exists():
            raise CommandError("Synthetic D3 fixtures must remain EUR only.")
        if QualityIssue.objects.filter(
            run__document_id__in=rejected_docs.values_list("id", flat=True),
            code="TOTAL_MISMATCH"
        ).count() != 2:
            raise CommandError("Both rejected fixtures must expose their reconciliation issue.")

        placeholders = ", ".join(["%s"] * len(fixture_ids))
        with connection.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*), COALESCE(SUM(total),0) "
                f"FROM bi.validated_invoices WHERE document_id IN ({placeholders})",
                fixture_ids,
            )
            count, amount = cur.fetchone()
            if (count, amount) != (15, Decimal("1344.00")):
                raise CommandError(f"BI fixture invoice aggregate diverges: {count}/{amount}")

            cur.execute(
                f"SELECT to_char(date_trunc('month', issued_on), 'YYYY-MM'), "
                f"COALESCE(SUM(total),0) FROM bi.validated_invoices "
                f"WHERE document_id IN ({placeholders}) "
                f"GROUP BY 1 ORDER BY 1",
                fixture_ids,
            )
            observed_months = dict(cur.fetchall())
            expected_months = synthetic_expected_monthly()
            if observed_months != expected_months:
                raise CommandError(
                    f"BI monthly numbers differ from the original CSV/XLSX/PDF corpus: "
                    f"{observed_months} != {expected_months}"
                )

            # Independent raw-table reconciliation: not derived from the BI views.
            base = list(Invoice.objects.filter(
                document__source="UPLOAD",
                document__state__in=["ACCEPTED", "INDEXED"],
                run__status="SUCCEEDED",
            ).values("currency").annotate(total=Sum("total"), n=Count("id")))
            expected_currencies = {
                item["currency"]: (item["n"], item["total"]) for item in base
            }
            cur.execute("SELECT currency, invoice_count, total FROM bi.currency_totals")
            actual_currencies = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
            if actual_currencies != expected_currencies:
                raise CommandError("Currency totals do not match independent Invoice ORM totals.")

            cur.execute(
                "SELECT currency, SUM(total) FROM bi.spending_monthly GROUP BY currency"
            )
            monthly = dict(cur.fetchall())
            if monthly != {k: v[1] for k, v in expected_currencies.items()}:
                raise CommandError("Monthly totals do not reconcile with currency totals.")
            cur.execute(
                "SELECT currency, SUM(total) FROM bi.spending_suppliers GROUP BY currency"
            )
            suppliers = dict(cur.fetchall())
            if suppliers != {k: v[1] for k, v in expected_currencies.items()}:
                raise CommandError("Supplier totals do not reconcile with currency totals.")

            cur.execute("SELECT COUNT(*) FROM bi.document_quality")
            documents_from_view = cur.fetchone()[0]
            if documents_from_view != Document.objects.filter(source="UPLOAD").count():
                raise CommandError("Document-quality view fan-out or missing documents.")

            cur.execute(
                f"SELECT COUNT(*) FROM bi.quality_issues "
                f"WHERE document_id IN ({placeholders})",
                fixture_ids,
            )
            if cur.fetchone()[0] != 2:
                raise CommandError("Expected two distinct synthetic quality issues.")

            cur.execute("SELECT COUNT(*) FROM bi.validated_invoices")
            if cur.fetchone()[0] != Invoice.objects.filter(
                document__source="UPLOAD",
                document__state__in=["ACCEPTED", "INDEXED"],
                run__status="SUCCEEDED",
            ).count():
                raise CommandError("Invoice BI view has row duplication or omission.")

        self.stdout.write(self.style.SUCCESS(
            "D3 SQL VERIFIED: 15 invoices / 7 accepted docs / 2 rejected docs / "
            "1344.00 EUR TTC / 5 monthly periods / currency, supplier and quality "
            "views reconciled independently."
        ))
        return None
