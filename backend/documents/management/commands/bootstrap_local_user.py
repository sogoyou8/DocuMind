"""Create a least-privilege local operator without logging credentials."""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Create or optionally reset the local DocuMind operator from an env secret."

    def add_arguments(self, parser):
        parser.add_argument("--reset-password", action="store_true")

    def handle(self, *args, **opts):
        if settings.DEMO_READONLY or connection.vendor != "postgresql":
            raise CommandError("Commande réservée à PostgreSQL local.")
        secret = os.getenv("DOCUMIND_LOCAL_PASSWORD", "")
        if not 24 <= len(secret) <= 128:
            raise CommandError("DOCUMIND_LOCAL_PASSWORD requis (24 à 128 caractères).")
        username = "documind-local"
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": False, "is_superuser": False},
        )
        if created or opts["reset_password"]:
            user.set_password(secret)
            user.save(update_fields=["password"])
        group, _ = Group.objects.get_or_create(name="documind_operator")
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(
            "Compte opérateur local disponible : documind-local (mot de passe privé)."
        ))
