import { expect, test, type Page } from "@playwright/test";

const fixtures = [
  { id: "00000000-0000-4000-8000-000000000001", original_name: "Exemple-facture-001.pdf", file_type: "PDF", size_bytes: 0 },
  { id: "00000000-0000-4000-8000-000000000002", original_name: "Exemple-commandes-002.csv", file_type: "CSV", size_bytes: 0 },
  { id: "00000000-0000-4000-8000-000000000003", original_name: "Exemple-rapport-003.xlsx", file_type: "XLSX", size_bytes: 0 },
].map(item => ({
  ...item, sha256: "f".repeat(64), state: "RECEIVED", source: "DEMO",
  created_at: "2026-11-09T12:00:00Z",
}));

async function mockPublicAPI(page: Page) {
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    const data =
      path === "/api/v1/session/" ? {
        mode: "synthetic-demo", authenticated: false, username: null,
        operator: false, ai_enabled: false, csrf_token: "fixture-only",
      } : path === "/api/v1/overview/" ? {
        mode: "synthetic-demo", total: 3, received: 3,
        rejected: 0, processed: 0, airflow_enabled: false, ai_enabled: false,
        note: "Fictional metadata only",
      } : path === "/api/v1/documents/" ? {
        count: 3, next: null, previous: null, results: fixtures,
      } : path === "/api/v1/analytics/" ? {
        available: false, reason: "Demo metadata only",
        currencies: [], monthly: [], suppliers: [], statuses: [], issues: [],
      } : path === "/api/v1/audit/" ? {
        count: 0, results: [],
      } : undefined;
    if (method !== "GET" || !data) {
      await route.fulfill({ status: 403, contentType: "application/json",
        body: JSON.stringify({ detail: "Démo en lecture seule" }) });
    } else {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
    }
  });
}

test.beforeEach(async ({ page }) => {
  await mockPublicAPI(page);
});

test("public demo is transparent, navigable and has no fabricated KPIs", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Gérez, vérifiez, analysez et interrogez vos documents/i })).toBeVisible();
  await expect(page.getByText("3 fiches de démonstration fictives")).toBeVisible();
  await expect(page.getByText("Analyse indisponible dans la démo").first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("overview-desktop.png"), fullPage: true });

  await page.getByRole("button", { name: "Documents", exact: true }).click();
  await expect(page.getByText("Exemple-facture-001.pdf")).toBeVisible();
  await expect(page.getByRole("button", { name: /Importer un document/i })).toBeDisabled();
  await expect(page.locator("input[type=file]")).toBeDisabled();
  await page.screenshot({ path: testInfo.outputPath("documents-desktop.png"), fullPage: true });

  await page.getByRole("button", { name: "Analyse & KPI" }).click();
  await expect(page.getByText("Analyse indisponible dans cette instance")).toBeVisible();
  await expect(page.getByText("1 344 €")).toHaveCount(0);

  await page.getByRole("button", { name: "Assistant IA" }).click();
  await expect(page.getByText("Désactivé en démo")).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Poser une question documentaire" })).toBeDisabled();
  await page.screenshot({ path: testInfo.outputPath("assistant-demo.png"), fullPage: true });
});

test("mobile navigation remains usable with no horizontal overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Gérez, vérifiez, analysez et interrogez vos documents/i })).toBeVisible();
  await page.getByRole("button", { name: "Ouvrir la navigation" }).click();
  await page.getByRole("button", { name: "Documents", exact: true }).click();
  await expect(page.getByText("Exemple-commandes-002.csv")).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
  await page.screenshot({ path: testInfo.outputPath("documents-mobile.png"), fullPage: true });
});
