"""Idempotent D2 worker entrypoint for local Airflow or manual batch processing."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from documents.models import Document
from documents.pipeline.runner import process_document


class Command(BaseCommand):
    help = "Process received local documents, maximum 50 per execution."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **opts):
        if settings.DEMO_READONLY:
            raise CommandError("Le pipeline est interdit sur Render en mode demo.")
        limit = opts["limit"]
        if not 1 <= limit <= 50:
            raise CommandError("La limite doit être entre 1 et 50.")
        ids = list(Document.objects.filter(
            state=Document.State.RECEIVED,
            source=Document.Source.UPLOAD,
        ).order_by("created_at").values_list("id", flat=True)[:limit])
        accepted = rejected = 0
        for document_id in ids:
            run, skipped = process_document(document_id)
            if skipped:
                continue
            if run.status == run.Status.SUCCEEDED:
                accepted += 1
            elif run.status == run.Status.REJECTED:
                rejected += 1
        self.stdout.write(self.style.SUCCESS(
            f"D2 processed={accepted + rejected} accepted={accepted} rejected={rejected}"
        ))
        return None
