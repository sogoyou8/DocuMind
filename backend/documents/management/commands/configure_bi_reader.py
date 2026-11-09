"""Configure a least-privilege PostgreSQL login to SELECT ONLY from bi views."""
import re
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Grant read-only access to the bi schema; requires --password or env var."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=None)

    def handle(self, *args, **options):
        import os
        if settings.DEMO_READONLY or connection.vendor != "postgresql":
            raise CommandError("D3 reader role is local PostgreSQL only.")
        secret = options["password"] or os.environ.get("DOCUMIND_BI_PASSWORD", "")
        # Restrict password to generated URL-safe symbols before SQL quoting.
        if not re.fullmatch(r"[A-Za-z0-9_-]{30,128}", secret):
            raise CommandError("Use a generated 30+ character URL-safe secret.")
        safe = "'" + secret + "'"  # bounded no SQL syntax characters in input
        with connection.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'documind_bi'")
            if cur.fetchone() is None:
                cur.execute("CREATE ROLE documind_bi LOGIN")
            cur.execute(f"ALTER ROLE documind_bi LOGIN PASSWORD {safe}")
            cur.execute("GRANT USAGE ON SCHEMA bi TO documind_bi")
            cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA bi TO documind_bi")
            cur.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM documind_bi")
            cur.execute("REVOKE CREATE ON SCHEMA public FROM documind_bi")
            cur.execute(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA bi "
                "GRANT SELECT ON TABLES TO documind_bi"
            )
        self.stdout.write(self.style.SUCCESS(
            "D3 BI reader configured: SELECT on bi views only; no raw tables."
        ))
        return None
