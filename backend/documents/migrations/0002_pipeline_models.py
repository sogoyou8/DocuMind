"""D2: normalized invoice processing, provenance and quality audit."""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ProcessingRun",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("pipeline_version", models.CharField(max_length=32)),
                ("status", models.CharField(max_length=12, default="RUNNING", choices=[
                    ("RUNNING", "En traitement"), ("SUCCEEDED", "Validé"),
                    ("REJECTED", "Rejeté"), ("FAILED", "Erreur technique"),
                ])),
                ("attempt_number", models.PositiveIntegerField(default=1)),
                ("error_summary", models.CharField(max_length=500, blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("document", models.ForeignKey(
                    to="documents.document", on_delete=django.db.models.deletion.CASCADE,
                    related_name="processing_runs")),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="ExtractedRecord",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("source_locator", models.CharField(max_length=200)),
                ("raw_fields", models.JSONField(default=dict)),
                ("normalized_fields", models.JSONField(default=dict)),
                ("document", models.ForeignKey(
                    to="documents.document", on_delete=django.db.models.deletion.CASCADE,
                    related_name="extracted_records")),
                ("run", models.ForeignKey(
                    to="documents.processingrun", on_delete=django.db.models.deletion.CASCADE,
                    related_name="records")),
            ],
            options={"ordering": ["source_locator"]},
        ),
        migrations.CreateModel(
            name="QualityIssue",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("source_locator", models.CharField(max_length=200, blank=True)),
                ("code", models.CharField(max_length=40)),
                ("severity", models.CharField(max_length=10, default="ERROR")),
                ("field_name", models.CharField(max_length=60, blank=True)),
                ("message", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("record", models.ForeignKey(
                    to="documents.extractedrecord", related_name="issues",
                    null=True, blank=True, on_delete=django.db.models.deletion.CASCADE)),
                ("run", models.ForeignKey(
                    to="documents.processingrun", related_name="issues",
                    on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={"ordering": ["code", "source_locator"]},
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=150)),
                ("canonical_key", models.CharField(max_length=150, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("invoice_number", models.CharField(max_length=100)),
                ("issued_on", models.DateField()),
                ("currency", models.CharField(max_length=3)),
                ("subtotal", models.DecimalField(max_digits=12, decimal_places=2)),
                ("tax", models.DecimalField(max_digits=12, decimal_places=2)),
                ("total", models.DecimalField(max_digits=12, decimal_places=2)),
                ("document", models.ForeignKey(
                    to="documents.document", related_name="invoices",
                    on_delete=django.db.models.deletion.CASCADE)),
                ("run", models.ForeignKey(
                    to="documents.processingrun", related_name="invoices",
                    on_delete=django.db.models.deletion.CASCADE)),
                ("record", models.OneToOneField(
                    to="documents.extractedrecord", related_name="invoice",
                    on_delete=django.db.models.deletion.CASCADE)),
                ("supplier", models.ForeignKey(
                    to="documents.supplier", related_name="invoices",
                    on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={"ordering": ["-issued_on", "invoice_number"]},
        ),
        migrations.AddConstraint(
            model_name="processingrun",
            constraint=models.UniqueConstraint(
                fields=["document", "pipeline_version"],
                name="one_processing_run_per_document_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="extractedrecord",
            constraint=models.UniqueConstraint(
                fields=["run", "source_locator"],
                name="one_record_per_run_source_locator",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                fields=["supplier", "invoice_number", "issued_on"],
                name="unique_invoice_supplier_number_date",
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["issued_on", "currency"], name="documind_invoice_date_ccy"),
        ),
    ]
