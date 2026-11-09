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
