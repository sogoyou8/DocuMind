"""Seed a repeatable *local-only* synthetic PDF/CSV/XLSX corpus."""
import hashlib
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from documents.models import Document, AuditEvent
from documents.pipeline.fixtures import example_files
from documents.pipeline.runner import process_document


class Command(BaseCommand):
    help = "Create 4 fictional documents; optionally process them with D2 engine."

    def add_arguments(self, parser):
        parser.add_argument("--process", action="store_true")

    def handle(self, *args, **opts):
        if settings.DEMO_READONLY:
            raise CommandError("Corps D2 interdit sur Render Free read-only.")
        for filename, content in example_files():
            digest = hashlib.sha256(content).hexdigest()
            doc = Document.objects.filter(sha256=digest).first()
            if doc is None:
                doc = Document.objects.create(
                    original_name=filename, sha256=digest,
                    file_type=filename.rsplit(".", 1)[-1].upper(),
                    size_bytes=len(content),
                    blob=ContentFile(content, name=filename),
                    source=Document.Source.UPLOAD,
                    state=Document.State.RECEIVED,
                )
                AuditEvent.objects.create(document=doc, action="SYNTHETIC_SEEDED")
            if opts["process"]:
                run, skipped = process_document(doc.id)
                self.stdout.write(
                    f"{filename}: {run.status} (skipped={skipped}, issues={run.issues.count()})"
                )
            else:
                self.stdout.write(f"{filename}: {doc.state}")
        return None
