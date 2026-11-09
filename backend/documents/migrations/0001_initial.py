import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Document", fields=[
            ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ("original_name", models.CharField(max_length=200)),
            ("sha256", models.CharField(max_length=64, unique=True)),
            ("file_type", models.CharField(max_length=8)),
            ("size_bytes", models.PositiveBigIntegerField()),
            ("blob", models.FileField(upload_to="raw/%Y/%m/%d/", blank=True)),
            ("state", models.CharField(max_length=14, choices=[
                ("RECEIVED", "Reçu"), ("VALIDATING", "En validation"),
                ("ACCEPTED", "Accepté"), ("INDEXED", "Indexé"), ("REJECTED", "Rejeté")
            ], default="RECEIVED")),
            ("source", models.CharField(max_length=6, choices=[
                ("UPLOAD", "Dépôt authentifié"), ("DEMO", "Exemple synthétique")
            ], default="UPLOAD")),
            ("uploaded_by", models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL, related_name="documind_documents")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="AuditEvent", fields=[
            ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ("action", models.CharField(max_length=40)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("actor", models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True,
                null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ("document", models.ForeignKey(to="documents.document",
                related_name="audit_events", on_delete=django.db.models.deletion.CASCADE)),
        ], options={"ordering": ["-created_at"]}),
        migrations.AddIndex(model_name="document",
            index=models.Index(fields=["state", "created_at"], name="documind_state_date_idx")),
    ]
