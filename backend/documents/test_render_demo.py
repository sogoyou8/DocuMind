"""Public interactive Render demonstration — no real D2/D3/D4 execution."""
from django.test import SimpleTestCase, override_settings


class RenderInteractiveDemoTests(SimpleTestCase):
    @override_settings(DEMO_READONLY=True)
    def test_home_is_accessible_and_transparent(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DocuMind V1.0")
        self.assertContains(response, "Simulation publique")
        self.assertContains(response, "scénario préenregistré")
        self.assertContains(response, "Les API D1 restent en lecture seule")
        self.assertContains(response, "Aucune IA live")

    @override_settings(DEMO_READONLY=True)
    def test_five_sections_are_present_without_external_analytics_or_ai(self):
        response = self.client.get("/")
        for tab in ("overview", "documents", "analytics", "assistant", "history"):
            self.assertContains(response, 'data-page="' + tab + '"')
        self.assertContains(response, "Import (local uniquement)")
        self.assertContains(response, "1 344,00 €")
        self.assertContains(response, "demo-d2-facture-valide.csv")
        self.assertNotContains(response, '<script src="https://')
