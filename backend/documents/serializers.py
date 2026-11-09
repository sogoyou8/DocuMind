"""D1: bounded upload + signature checks, not semantic PDF extraction."""
import hashlib
from pathlib import Path
import zipfile

from rest_framework import serializers
from django.db import transaction
from .models import Document, AuditEvent

MAX_BYTES = 5 * 1024 * 1024
FORMATS = {".pdf": "PDF", ".csv": "CSV", ".xlsx": "XLSX"}

def validate_uploaded_file(upload):
    name = Path(upload.name).name
    suffix = Path(name).suffix.lower()
    if not name or len(name) > 200 or suffix not in FORMATS:
        raise serializers.ValidationError("Fichier PDF, CSV ou XLSX requis (nom limité à 200 caractères).")
    if upload.size == 0 or upload.size > MAX_BYTES:
        raise serializers.ValidationError("Taille du fichier attendue : 1 octet à 5 Mio.")
    upload.seek(0)
    if suffix == ".pdf" and not upload.read(8).startswith(b"%PDF-"):
        raise serializers.ValidationError("Signature PDF invalide.")
    upload.seek(0)
    if suffix == ".csv":
        raw = upload.read(MAX_BYTES + 1)
        if b"\x00" in raw:
            raise serializers.ValidationError("CSV binaire refusé.")
        try:
            raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise serializers.ValidationError("CSV attendu en UTF-8.")
    if suffix == ".xlsx":
        if not zipfile.is_zipfile(upload):
            raise serializers.ValidationError("Archive XLSX non valide.")
        try:
            with zipfile.ZipFile(upload) as archive:
                names = archive.namelist()
                if "xl/workbook.xml" not in names or any(
                    "vbaproject.bin" in n.lower() or ".." in n.split("/") for n in names
                ):
                    raise serializers.ValidationError("Classeur XLSX non conforme ou macro détectée.")
        except (OSError, zipfile.BadZipFile):
            raise serializers.ValidationError("Classeur corrompu.")
    upload.seek(0)
    return FORMATS[suffix]


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok"])
    service = serializers.CharField()


class HealthUnavailableSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["unavailable"])


class OverviewResponseSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["synthetic-demo", "local"])
    total = serializers.IntegerField(min_value=0)
    received = serializers.IntegerField(min_value=0)
    rejected = serializers.IntegerField(min_value=0)
    processed = serializers.IntegerField(min_value=0)
    airflow_enabled = serializers.BooleanField()
    ai_enabled = serializers.BooleanField()
    note = serializers.CharField()


class DocumentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "original_name", "sha256", "file_type",
                  "size_bytes", "state", "source", "created_at"]
        read_only_fields = fields

class DocumentCreateSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, upload):
        validate_uploaded_file(upload)
        return upload

    @transaction.atomic
    def create(self, validated_data):
        upload = validated_data["file"]
        hasher = hashlib.sha256()
        upload.seek(0)
        for chunk in upload.chunks():
            hasher.update(chunk)
        upload.seek(0)
        digest = hasher.hexdigest()
        if Document.objects.filter(sha256=digest).exists():
            raise serializers.ValidationError({"file": "SHA-256 déjà enregistré."})
        doc = Document.objects.create(
            original_name=Path(upload.name).name,
            sha256=digest,
            file_type=FORMATS[Path(upload.name).suffix.lower()],
            size_bytes=upload.size,
            blob=upload,
            source=Document.Source.UPLOAD,
            uploaded_by=self.context["request"].user,
        )
        AuditEvent.objects.create(document=doc, actor=self.context["request"].user,
                                  action="DOCUMENT_RECEIVED")
        return doc


# D2 processing read contracts. Never include private blob paths or direct download URLs.
from .models import ProcessingRun, ExtractedRecord, QualityIssue, Invoice


class ProcessOptionsSerializer(serializers.Serializer):
    force = serializers.BooleanField(required=False, default=False)


class ProcessResultSerializer(serializers.Serializer):
    run_id = serializers.UUIDField()
    status = serializers.CharField()
    attempt_number = serializers.IntegerField()
    skipped = serializers.BooleanField()
    records_count = serializers.IntegerField()
    issues_count = serializers.IntegerField()
    invoices_count = serializers.IntegerField()


class ProcessingRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingRun
        fields = [
            "id", "document", "pipeline_version", "status", "attempt_number",
            "error_summary", "started_at", "finished_at",
        ]
        read_only_fields = fields


class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedRecord
        fields = [
            "id", "document", "run", "source_locator",
            "raw_fields", "normalized_fields",
        ]
        read_only_fields = fields


class QualityIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityIssue
        fields = [
            "id", "run", "record", "source_locator",
            "code", "severity", "field_name", "message", "created_at",
        ]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    source_locator = serializers.CharField(source="record.source_locator", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "document", "run", "record", "source_locator", "supplier_name",
            "invoice_number", "issued_on", "currency",
            "subtotal", "tax", "total",
        ]
        read_only_fields = fields


# D4 local assistant: model returns text but server selects verified source citations.
class AskDocumentSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=4, max_length=500, trim_whitespace=True)


class AssistantCitationSerializer(serializers.Serializer):
    id = serializers.CharField()
    document_id = serializers.UUIDField()
    document = serializers.CharField()
    source_locator = serializers.CharField()
    excerpt = serializers.CharField()


class AssistantAnswerSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["answered", "abstained"])
    answer = serializers.CharField()
    citations = AssistantCitationSerializer(many=True)


class AssistantStatusSerializer(serializers.Serializer):
    mode = serializers.CharField()
    enabled = serializers.BooleanField()
    embedding_model = serializers.CharField()
    generation_model = serializers.CharField()
    indexed_chunks = serializers.IntegerField()


class IndexResultSerializer(serializers.Serializer):
    indexed_chunks = serializers.IntegerField()
    skipped = serializers.BooleanField()
