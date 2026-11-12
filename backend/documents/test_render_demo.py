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
        self.assertContains(response, "aucune IA exécutée")

    @override_settings(DEMO_READONLY=True)
    def test_five_sections_are_present_without_external_analytics_or_ai(self):
        response = self.client.get("/")
        for tab in ("overview", "documents", "analytics", "assistant", "history"):
            self.assertContains(response, 'data-page="' + tab + '"')
        self.assertContains(response, "Importer (local uniquement)")
        self.assertContains(response, "1 344,00 €")
        self.assertContains(response, "demo-d2-facture-valide.csv")
        self.assertNotContains(response, '<script src="https://')

    @override_settings(DEMO_READONLY=True)
    def test_desktop_monoscreen_and_mobile_fallback_are_defined(self):
        page = self.client.get("/").content.decode("utf-8")
        self.assertIn("@media (min-width:1081px) and (min-height:700px)", page)
        self.assertIn("height:100dvh;min-height:0;overflow:hidden", page)
        for view in ("overview", "documents", "analytics", "assistant", "history"):
            self.assertIn('#screen[data-view="' + view + '"]', page)
        self.assertIn("el.dataset.view=state.page", page)
        self.assertIn("overflow-y:auto", page)
        self.assertIn("@media(max-width:700px)", page)
