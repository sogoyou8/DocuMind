"""Purely fictional metadata. No document bytes or analytic results are implied."""
import hashlib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from documents.models import Document

EXAMPLES = [
    ("Exemple-facture-001.pdf", "PDF"),
    ("Exemple-commandes-002.csv", "CSV"),
    ("Exemple-rapport-003.xlsx", "XLSX"),
]

class Command(BaseCommand):
    help = "Seed three clearly labelled synthetic metadata examples, only in demo mode."

    def handle(self, *args, **kwargs):
        if not settings.DEMO_READONLY:
            raise CommandError("DOCUMIND_DEMO_READONLY=1 is required for demo seed")
        for name, file_type in EXAMPLES:
            digest = hashlib.sha256(("documind-demo-d1:" + name).encode()).hexdigest()
            Document.objects.get_or_create(sha256=digest, defaults={
                "original_name": name, "file_type": file_type, "size_bytes": 0,
                "source": Document.Source.DEMO, "state": Document.State.RECEIVED,
            })
        self.stdout.write("Three synthetic document metadata examples are available.")
