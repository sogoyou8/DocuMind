"""D3 corpus seed. Fictional only, reproducible, idempotent and local-only."""
import hashlib

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from documents.bi.fixtures import d3_example_files
from documents.models import AuditEvent, Document
from documents.pipeline.runner import process_document


class Command(BaseCommand):
    help = "Seed 4 valid multi-row monthly CSVs + 1 invalid CSV; D2 November included."

    def add_arguments(self, parser):
        parser.add_argument("--process", action="store_true")

    def handle(self, *args, **options):
        if settings.DEMO_READONLY:
            raise CommandError("D3 analytics never runs in public Render demo.")
        call_command("seed_d2", process=options["process"], verbosity=0)
        for filename, raw in d3_example_files():
            sha = hashlib.sha256(raw).hexdigest()
            document = Document.objects.filter(sha256=sha).first()
            if document is None:
                document = Document.objects.create(
                    original_name=filename, file_type="CSV", size_bytes=len(raw),
                    sha256=sha, source=Document.Source.UPLOAD,
                    state=Document.State.RECEIVED,
                    blob=ContentFile(raw, name=filename),
                )
                AuditEvent.objects.create(document=document, action="SYNTHETIC_SEEDED")
            if options["process"]:
                run, skipped = process_document(document.id)
                self.stdout.write(f"{filename}: {run.status} skipped={skipped}")
            else:
                self.stdout.write(f"{filename}: {document.state}")
        return None
