from django.contrib import admin
from .models import Document, AuditEvent

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "source", "state", "file_type", "created_at")
    list_filter = ("state", "source")
    search_fields = ("original_name", "sha256")

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("document", "action", "actor", "created_at")
    readonly_fields = ("document", "actor", "action", "created_at")
