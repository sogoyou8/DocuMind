"""Verify that BI login can SELECT views but cannot read or write source tables."""
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Prove the SQL account used by Metabase is restricted to BI views."

    def handle(self, *args, **kwargs):
        if settings.DEMO_READONLY or connection.vendor != "postgresql":
            raise CommandError("The BI role check is available only on local PostgreSQL.")
        secret = os.environ.get("DOCUMIND_BI_PASSWORD")
        if not secret:
            raise CommandError("DOCUMIND_BI_PASSWORD is required.")
        import psycopg
        cfg = connection.settings_dict
        try:
            with psycopg.connect(
                dbname=cfg["NAME"],
                host=cfg.get("HOST") or "postgres",
                port=int(cfg.get("PORT") or 5432),
                user="documind_bi",
                password=secret,
                connect_timeout=10,
                autocommit=True,
            ) as db:
                with db.cursor() as cur:
                    cur.execute(
                        "SELECT has_table_privilege(current_user, 'bi.validated_invoices', 'SELECT'), "
                        "has_table_privilege(current_user, 'bi.validated_invoices', 'INSERT'), "
                        "has_table_privilege(current_user, 'public.documents_invoice', 'SELECT'), "
                        "has_table_privilege(current_user, 'public.documents_document', 'SELECT')"
                    )
                    access = cur.fetchone()
                    if tuple(access) != (True, False, False, False):
                        raise CommandError("BI role has incorrect SQL permissions.")
                    cur.execute("SELECT COUNT(*) FROM bi.validated_invoices")
                    if cur.fetchone()[0] < 15:
                        raise CommandError("BI login cannot see the expected validated corpus.")
                    cur.execute("SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user")
                    if tuple(cur.fetchone()) != (False, False, False):
                        raise CommandError("BI role must not have superuser or database/role creation rights.")
        except psycopg.Error as exc:
            raise CommandError("BI reader login/queries failed; check isolated SQL credentials.") from exc
        self.stdout.write(self.style.SUCCESS(
            "D3 SQL ROLE VERIFIED: bi SELECT allowed; raw document tables and writes forbidden."
        ))
        return None
