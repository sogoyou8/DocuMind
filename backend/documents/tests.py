import hashlib
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings, TestCase
from rest_framework.test import APIClient
from .models import Document, AuditEvent

class ApiD1Tests(TestCase):
    def test_upload_storage_aliases_are_configured(self):
        from django.conf import settings
        self.assertEqual(
            settings.STORAGES["default"]["BACKEND"],
            "django.core.files.storage.FileSystemStorage",
        )
        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
        )

    def test_container_static_assets_are_stable(self):
        import os
        from django.conf import settings
        from pathlib import Path

        container_static_root = os.environ.get("DJANGO_STATIC_ROOT")
        if not container_static_root:
            self.skipTest("No Docker static root configured (Render or CI).")
        self.assertEqual(settings.STATIC_ROOT, Path(container_static_root))
        self.assertNotEqual(settings.STATIC_ROOT, settings.BASE_DIR / "staticfiles")
        self.assertTrue((settings.STATIC_ROOT / "admin/css/base.css").is_file())

    def test_openapi_health_and_overview_have_explicit_schema(self):
        from io import StringIO
        from django.core.management import call_command
        from drf_spectacular.generators import SchemaGenerator

        schema = SchemaGenerator().get_schema(request=None, public=True)
        for endpoint in ("/api/v1/health/", "/api/v1/overview/"):
            with self.subTest(endpoint=endpoint):
                response = schema["paths"][endpoint]["get"]["responses"]["200"]
                self.assertIn("application/json", response["content"])
        self.assertIn("503", schema["paths"]["/api/v1/health/"]["get"]["responses"])
        # This must fail on generator diagnostics, not only OpenAPI-format validation.
        call_command("spectacular", validate=True, fail_on_warn=True, stdout=StringIO())

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="operator", password="test-password-unique")
        self.group = Group.objects.create(name="documind_operator")

    def test_health_exposes_no_sensitive_config(self):
        r = self.client.get("/api/v1/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertNotIn("database", r.json())

    @override_settings(DEMO_READONLY=False)
    def test_local_requires_authentication(self):
        self.assertIn(self.client.get("/api/v1/documents/").status_code, (401, 403))
        self.assertIn(self.client.get("/api/v1/overview/").status_code, (401, 403))

    @override_settings(DEMO_READONLY=False)
    def test_authenticated_nonoperator_cannot_upload(self):
        self.client.force_authenticate(self.user)
        r = self.client.post("/api/v1/documents/", {
            "file": SimpleUploadedFile("ok.csv", b"invoice,total\nA,10\n")
        }, format="multipart")
        self.assertEqual(r.status_code, 403)

    @override_settings(DEMO_READONLY=False)
    def test_operator_upload_csv_creates_audit_and_rejects_same_hash(self):
        self.user.groups.add(self.group)
        self.client.force_authenticate(self.user)
        with tempfile.TemporaryDirectory() as temp:
            with override_settings(MEDIA_ROOT=Path(temp)):
                content = b"invoice,total\nA,10\n"
                r = self.client.post("/api/v1/documents/", {
                    "file": SimpleUploadedFile("sample.csv", content)
                }, format="multipart")
                self.assertEqual(r.status_code, 201, r.data)
                self.assertEqual(r.data["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(r.data["state"], "RECEIVED")
                self.assertEqual(AuditEvent.objects.count(), 1)
                self.assertEqual(Document.objects.count(), 1)
                second = self.client.post("/api/v1/documents/", {
                    "file": SimpleUploadedFile("repeat.csv", content)
                }, format="multipart")
                self.assertEqual(second.status_code, 400)
                self.assertEqual(Document.objects.count(), 1)

    @override_settings(DEMO_READONLY=False)
    def test_invalid_upload_fails_before_storage(self):
        self.user.groups.add(self.group)
        self.client.force_authenticate(self.user)
        invalid = [
            ("bad.exe", b"evil"),
            ("bad.pdf", b"not a pdf"),
            ("bad.csv", b"bad\x00bytes"),
            ("bad.xlsx", b"not-a-zip"),
        ]
        for filename, contents in invalid:
            with self.subTest(filename=filename):
                r = self.client.post("/api/v1/documents/", {
                    "file": SimpleUploadedFile(filename, contents)
                }, format="multipart")
                self.assertEqual(r.status_code, 400)
        self.assertEqual(Document.objects.count(), 0)

    @override_settings(DEMO_READONLY=True)
    def test_readonly_demo_allows_get_and_blocks_post(self):
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Document.objects.count(), 3)
        r = self.client.get("/api/v1/documents/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["results"]), 3)
        r2 = self.client.post("/api/v1/documents/", {
            "file": SimpleUploadedFile("ok.csv", b"a,b\n1,2\n")
        }, format="multipart")
        self.assertEqual(r2.status_code, 403)
        ov = self.client.get("/api/v1/overview/")
        self.assertEqual(ov.status_code, 200)
        self.assertEqual(ov.json()["processed"], 0)
        self.assertFalse(ov.json()["ai_enabled"])

    @override_settings(DEMO_READONLY=True)
    def test_demo_filters_unexpected_private_upload_rows(self):
        # Defense in depth if a private upload is accidentally present in
        # the disposable demo DB: anonymous users see DEMO metadata only.
        call_command("seed_demo", verbosity=0)
        unexpected = Document.objects.create(
            original_name="PRIVATE-facture.pdf",
            file_type="PDF", size_bytes=10, sha256="f" * 64,
            source=Document.Source.UPLOAD,
        )
        docs = self.client.get("/api/v1/documents/")
        self.assertEqual(docs.status_code, 200)
        self.assertEqual(docs.data["count"], 3)
        self.assertTrue(all(
            row["source"] == "DEMO" for row in docs.data["results"]
        ))
        self.assertEqual(
            self.client.get(f"/api/v1/documents/{unexpected.id}/").status_code,
            404,
        )
        overview = self.client.get("/api/v1/overview/")
        self.assertEqual(overview.data["total"], 3)

    @override_settings(DEMO_READONLY=False)
    def test_seed_denied_in_local_mode(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("seed_demo", verbosity=0)

    @override_settings(DEMO_READONLY=True)
    def test_demo_does_not_expose_real_upload_urls(self):
        call_command("seed_demo", verbosity=0)
        data = self.client.get("/api/v1/documents/").json()["results"]
        self.assertTrue(all("blob" not in record for record in data))
        self.assertTrue(all(item["source"] == "DEMO" for item in data))
        self.assertEqual(self.client.get("/private-not-served/x").status_code, 404)
