"""D4: durable source-pointer records for local vector search."""
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("documents", "0003_bi_views")]

    operations = [
        migrations.CreateModel(
            name="ChunkReference",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4,
                                         editable=False, serialize=False)),
                ("source_locator", models.CharField(max_length=200)),
                ("chunk_index", models.PositiveIntegerField()),
                ("index_version", models.CharField(max_length=32, default="d4-v1")),
                ("embedding_model", models.CharField(max_length=100)),
                ("content_sha256", models.CharField(max_length=64)),
                ("indexed_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(to="documents.document",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunk_references")),
                ("run", models.ForeignKey(to="documents.processingrun",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunk_references")),
                ("record", models.ForeignKey(to="documents.extractedrecord",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chunk_references")),
            ],
            options={"ordering": ["document_id", "source_locator", "chunk_index"]},
        ),
        migrations.AddConstraint(
            model_name="chunkreference",
            constraint=models.UniqueConstraint(
                fields=["record", "index_version", "chunk_index"],
                name="unique_d4_chunk_per_record_index",
            ),
        ),
    ]
