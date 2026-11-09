"""Local-only D4 vector worker. Idempotent by validated run and chunk version."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from documents.models import Document
from documents.rag.indexer import index_document


class Command(BaseCommand):
    help = "Index at most 20 accepted D2 documents in local Ollama + Chroma."

    def add_arguments(self, parser):
        parser.add_argument("--limit", default=15, type=int)

    def handle(self, *args, **opts):
        if settings.DEMO_READONLY or not settings.DOCUMIND_AI_ENABLED:
            raise CommandError("D4 disabled outside the local AI service.")
        limit = opts["limit"]
        if not 1 <= limit <= 20:
            raise CommandError("Limit 1..20 only.")
        ids = list(Document.objects.filter(
            source=Document.Source.UPLOAD, state=Document.State.ACCEPTED,
        ).order_by("created_at").values_list("id", flat=True)[:limit])
        done = 0
        for document_id in ids:
            result = index_document(document_id)
            if not result["skipped"]:
                done += 1
        self.stdout.write(self.style.SUCCESS(
            f"D4 indexed_documents={done} eligible_candidates={len(ids)}"
        ))
