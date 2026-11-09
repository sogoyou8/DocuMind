import { expect, test } from "@playwright/test";

const username = "documind-local";
const password = process.env.DOCUMIND_E2E_PASSWORD;

test("real PostgreSQL session, documents, SQL analytics and cited local AI", async ({ page }, testInfo) => {
  test.skip(!password, "The private local operator password was not supplied.");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /votre workspace/i })).toBeVisible();

  await page.getByLabel("Identifiant").fill(username);
  await page.getByLabel("Mot de passe local").fill(password!);
  await page.getByRole("button", { name: /Accéder à DocuMind/i }).click();

  await expect(page.getByRole("heading", { name: /Vos documents/i })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("local-overview.png"), fullPage: true });
  await page.getByRole("button", { name: "Documents", exact: true }).click();
  await expect(page.getByText("demo-d2-facture-valide.csv")).toBeVisible();
  await page.getByRole("button", { name: "demo-d2-facture-valide.csv" }).click();
  const drawer = page.getByRole("dialog", { name: /demo-d2-facture-valide.csv/ });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByText("DM-2026-001")).toBeVisible();
  await drawer.getByRole("button", { name: "Fermer" }).click();

  await page.getByRole("button", { name: "Analyse & KPI" }).click();
  await expect(page.getByText("Réconciliation par devise")).toBeVisible();
  await expect(page.getByText("1 344", { exact: false }).first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("local-analytics.png"), fullPage: true });

  await page.getByRole("button", { name: "Assistant IA" }).click();
  await expect(page.getByText("Ollama local prêt")).toBeVisible();
  await page.getByRole("textbox", { name: "Poser une question documentaire" })
    .fill("Quel est le montant TTC de la facture DM-2026-001 ?");
  await page.getByRole("button", { name: "Envoyer la question" }).click();
  await expect(page.getByText("Réponse sourcée")).toBeVisible({ timeout: 165000 });
  await expect(page.getByText("demo-d2-facture-valide.csv")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("local-assistant-cited.png"), fullPage: true });
});
