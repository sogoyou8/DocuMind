from django.contrib import admin
from .models import (Document, AuditEvent, ProcessingRun, ExtractedRecord, QualityIssue, Supplier, Invoice)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "source", "state", "file_type", "created_at")
    list_filter = ("state", "source")
    search_fields = ("original_name", "sha256")

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("document", "action", "actor", "created_at")
    readonly_fields = ("document", "actor", "action", "created_at")


@admin.register(ProcessingRun)
class ProcessingRunAdmin(admin.ModelAdmin):
    list_display = ("document", "status", "pipeline_version", "attempt_number", "finished_at")
    list_filter = ("status", "pipeline_version")
    readonly_fields = ("document", "pipeline_version", "status", "attempt_number",
                       "error_summary", "started_at", "finished_at")


@admin.register(ExtractedRecord)
class ExtractedRecordAdmin(admin.ModelAdmin):
    list_display = ("document", "source_locator", "run")
    readonly_fields = ("document", "run", "source_locator", "raw_fields", "normalized_fields")


@admin.register(QualityIssue)
class QualityIssueAdmin(admin.ModelAdmin):
    list_display = ("code", "field_name", "source_locator", "run", "severity")
    list_filter = ("code", "severity")
    readonly_fields = ("run", "record", "source_locator", "code", "field_name",
                       "severity", "message", "created_at")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "canonical_key")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "supplier", "issued_on", "currency", "total", "document")
    list_filter = ("currency", "issued_on")
    readonly_fields = ("document", "run", "record", "supplier",
                       "invoice_number", "issued_on", "currency",
                       "subtotal", "tax", "total")
