"""Document metadata, D2 processing provenance and normalized invoice truth."""
import uuid
from django.conf import settings
from django.db import models

class Document(models.Model):
    class State(models.TextChoices):
        RECEIVED = "RECEIVED", "Reçu"
        VALIDATING = "VALIDATING", "En validation"
        ACCEPTED = "ACCEPTED", "Accepté"
        INDEXED = "INDEXED", "Indexé"
        REJECTED = "REJECTED", "Rejeté"

    class Source(models.TextChoices):
        UPLOAD = "UPLOAD", "Dépôt authentifié"
        DEMO = "DEMO", "Exemple synthétique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_name = models.CharField(max_length=200)
    sha256 = models.CharField(max_length=64, unique=True)
    file_type = models.CharField(max_length=8)
    size_bytes = models.PositiveBigIntegerField()
    blob = models.FileField(upload_to="raw/%Y/%m/%d/", blank=True)
    state = models.CharField(max_length=14, choices=State.choices, default=State.RECEIVED)
    source = models.CharField(max_length=6, choices=Source.choices, default=Source.UPLOAD)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="documind_documents")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["state", "created_at"], name="documind_state_date_idx")]

class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              blank=True, null=True)
    action = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]

class ProcessingRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "En traitement"
        SUCCEEDED = "SUCCEEDED", "Validé"
        REJECTED = "REJECTED", "Rejeté"
        FAILED = "FAILED", "Erreur technique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, related_name="processing_runs", on_delete=models.CASCADE)
    pipeline_version = models.CharField(max_length=32)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    attempt_number = models.PositiveIntegerField(default=1)
    error_summary = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["document", "pipeline_version"],
                                    name="one_processing_run_per_document_version"),
        ]


class ExtractedRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, related_name="extracted_records", on_delete=models.CASCADE)
    run = models.ForeignKey(ProcessingRun, related_name="records", on_delete=models.CASCADE)
    source_locator = models.CharField(max_length=200)
    raw_fields = models.JSONField(default=dict)
    normalized_fields = models.JSONField(default=dict)

    class Meta:
        ordering = ["source_locator"]
        constraints = [
            models.UniqueConstraint(fields=["run", "source_locator"],
                                    name="one_record_per_run_source_locator"),
        ]


class QualityIssue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(ProcessingRun, related_name="issues", on_delete=models.CASCADE)
    record = models.ForeignKey(ExtractedRecord, related_name="issues",
                               on_delete=models.CASCADE, null=True, blank=True)
    source_locator = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=40)
    severity = models.CharField(max_length=10, default="ERROR")
    field_name = models.CharField(max_length=60, blank=True)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "source_locator"]


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    canonical_key = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, related_name="invoices", on_delete=models.CASCADE)
    run = models.ForeignKey(ProcessingRun, related_name="invoices", on_delete=models.CASCADE)
    record = models.OneToOneField(ExtractedRecord, related_name="invoice", on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, related_name="invoices", on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=100)
    issued_on = models.DateField()
    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["-issued_on", "invoice_number"]
        constraints = [
            models.UniqueConstraint(fields=["supplier", "invoice_number", "issued_on"],
                                    name="unique_invoice_supplier_number_date"),
        ]
        indexes = [models.Index(fields=["issued_on", "currency"],
                                name="documind_invoice_date_ccy")]
