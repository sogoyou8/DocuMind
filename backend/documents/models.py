"""D1: metadata and audit; actual extraction arrives at D2."""
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
