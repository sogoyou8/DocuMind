"""D5: local browser session + trusted BI/audit contracts and demo isolation."""
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from .models import Document


@override_settings(DEMO_READONLY=True, DOCUMIND_AI_ENABLED=False)
class PublicDemoContracts(TestCase):
    def test_demo_session_never_leaks_user_or_enables_operations(self):
        status = self.client.get("/api/v1/session/")
        self.assertEqual(status.status_code, 200)
        data = status.json()
        self.assertEqual(data["mode"], "synthetic-demo")
        self.assertFalse(data["authenticated"])
        self.assertFalse(data["operator"])
        self.assertFalse(data["ai_enabled"])
        self.assertTrue(data["csrf_token"])

    def test_demo_login_is_forbidden(self):
        result = self.client.post(
            "/api/v1/session/login/",
            data='{"username":"fake","password":"fake"}',
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 403)

    def test_demo_analytics_never_invents_financial_results(self):
        call_command("seed_demo", verbosity=0)
        result = self.client.get("/api/v1/analytics/")
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertFalse(data["available"])
        for key in ("currencies", "monthly", "suppliers", "statuses", "issues"):
            self.assertEqual(data[key], [])
        self.assertNotIn("1344", str(data))

    def test_demo_audit_never_exposes_private_uploads(self):
        unexpected = Document.objects.create(
            original_name="secret-private.csv", sha256="a" * 64,
            file_type="CSV", size_bytes=1, source=Document.Source.UPLOAD,
        )
        self.assertEqual(self.client.get("/api/v1/audit/").json(),
                         {"count": 0, "results": []})
        documents = self.client.get("/api/v1/documents/").json()
        self.assertEqual(documents["count"], 0)
        self.assertNotIn(str(unexpected.id), str(documents))


@override_settings(DEMO_READONLY=False)
class BrowserAuthContracts(TestCase):
    def setUp(self):
        self.password = "local-unique-test-password-12345"
        self.user = get_user_model().objects.create_user(
            username="local-test", password=self.password,
        )
        group = Group.objects.create(name="documind_operator")
        self.user.groups.add(group)

    def test_login_rejects_missing_csrf_and_accepts_real_token(self):
        browser = Client(enforce_csrf_checks=True)
        status = browser.get("/api/v1/session/")
        self.assertEqual(status.status_code, 200)
        token = status.json()["csrf_token"]
        self.assertFalse(status.json()["authenticated"])
        payload = '{"username":"local-test","password":"local-unique-test-password-12345"}'
        self.assertEqual(browser.post(
            "/api/v1/session/login/", data=payload,
            content_type="application/json",
        ).status_code, 403)
        logged = browser.post(
            "/api/v1/session/login/", data=payload,
            content_type="application/json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(logged.status_code, 200, logged.content)
        self.assertTrue(logged.json()["operator"])
        current = browser.get("/api/v1/session/")
        self.assertTrue(current.json()["authenticated"])
        self.assertEqual(current.json()["username"], "local-test")
        logout = browser.post(
            "/api/v1/session/logout/", data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=current.json()["csrf_token"],
        )
        self.assertEqual(logout.status_code, 200)
        self.assertFalse(browser.get("/api/v1/session/").json()["authenticated"])

    def test_wrong_password_never_opens_session(self):
        browser = Client(enforce_csrf_checks=True)
        token = browser.get("/api/v1/session/").json()["csrf_token"]
        result = browser.post(
            "/api/v1/session/login/",
            data='{"username":"local-test","password":"incorrect"}',
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(result.status_code, 401)
        self.assertFalse(browser.get("/api/v1/session/").json()["authenticated"])

    def test_unauthenticated_analytics_and_audit_are_forbidden(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.get("/api/v1/analytics/").status_code, 403)
        self.assertEqual(anonymous.get("/api/v1/audit/").status_code, 403)

    def test_bootstrap_local_operator_is_idempotent(self):
        secret = "localsecret2026-0123456789-unique"
        with patch.dict("os.environ", {"DOCUMIND_LOCAL_PASSWORD": secret}):
            call_command("bootstrap_local_user", verbosity=0)
            account = get_user_model().objects.get(username="documind-local")
            self.assertTrue(account.check_password(secret))
            self.assertFalse(account.is_superuser)
            self.assertFalse(account.is_staff)
            self.assertTrue(account.groups.filter(name="documind_operator").exists())
            call_command("bootstrap_local_user", verbosity=0)
            self.assertEqual(
                get_user_model().objects.filter(username="documind-local").count(), 1,
            )


@skipUnless(connection.vendor == "postgresql", "D5 SQL views require PostgreSQL")
@override_settings(DEMO_READONLY=False)
class D5AnalyticsContracts(TestCase):
    def setUp(self):
        import tempfile
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        override = override_settings(MEDIA_ROOT=Path(self.folder.name))
        override.enable()
        self.addCleanup(override.disable)
        call_command("seed_d3", process=True, verbosity=0)
        user = get_user_model().objects.create_user(
            username="d5-analyst", password="local-analyst-tests",
        )
        self.client = APIClient()
        self.client.force_authenticate(user)

    def test_api_kpis_are_sql_values_not_frontend_fixture(self):
        response = self.client.get("/api/v1/analytics/")
        self.assertEqual(response.status_code, 200, response.data)
        data = response.data
        self.assertTrue(data["available"])
        euros = next(c for c in data["currencies"] if c["currency"] == "EUR")
        self.assertEqual(euros["invoice_count"], 15)
        self.assertEqual(Decimal(euros["total"]), Decimal("1344.00"))
        self.assertEqual(len([m for m in data["monthly"] if m["currency"] == "EUR"]), 5)
        self.assertEqual(
            sum(Decimal(m["total"]) for m in data["monthly"] if m["currency"] == "EUR"),
            Decimal("1344.00"),
        )
        self.assertEqual(
            sum(Decimal(s["total"]) for s in data["suppliers"] if s["currency"] == "EUR"),
            Decimal("1344.00"),
        )
        self.assertEqual(sum(s["count"] for s in data["issues"]), 2)

    def test_status_and_audit_are_real_and_private(self):
        overview = self.client.get("/api/v1/overview/").data
        report = self.client.get("/api/v1/analytics/").data
        self.assertEqual(overview["total"], 9)
        self.assertEqual(overview["processed"], 7)
        statuses = {row["state"]: row["count"] for row in report["statuses"]}
        self.assertEqual(statuses["REJECTED"], 2)
        self.assertEqual(statuses["ACCEPTED"], 7)
        audit = self.client.get("/api/v1/audit/").data
        self.assertGreaterEqual(audit["count"], 9)
        self.assertTrue(all("blob" not in row and "raw_fields" not in row
                            for row in audit["results"]))
        self.assertTrue(all(row["document_name"] for row in audit["results"]))

    def test_invalid_audit_uuid_is_rejected(self):
        result = self.client.get("/api/v1/audit/?document=not-a-uuid")
        self.assertEqual(result.status_code, 400)
