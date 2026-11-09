"""Create governed PostgreSQL BI views; Render Free SQLite demo is untouched.

The SQL contract is frozen in documents/bi/views_v1.sql. If it changes,
create a new migration rather than rewriting historical migrations.
"""
from pathlib import Path
from django.db import migrations


def apply_bi_views(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    path = Path(__file__).resolve().parent.parent / "bi" / "views_v1.sql"
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(path.read_text(encoding="utf-8"))


def drop_bi_views(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA IF EXISTS bi CASCADE")


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_pipeline_models")]
    operations = [migrations.RunPython(apply_bi_views, reverse_code=drop_bi_views)]
