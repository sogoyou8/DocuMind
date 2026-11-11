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
  // Success notices must disappear without manual interaction, unlike errors.
  const loginNotice = page.getByRole("button", { name: "Fermer la notification" });
  if (await loginNotice.isVisible()) await expect(loginNotice).toBeHidden({ timeout: 8000 });
  await page.screenshot({ path: testInfo.outputPath("local-overview.png"), fullPage: true });
  await page.getByRole("button", { name: "Documents", exact: true }).click();
  // Local databases may contain extra user-authorized uploads; the fixture
  // can therefore be on a later API page without indicating a regression.
  let found = false;
  for (let attempt = 0; attempt < 20; attempt++) {
    const fixture = page.getByRole("button", { name: /demo-d2-facture-valide.csv/ });
    if (await fixture.count()) {
      await fixture.first().click();
      found = true;
      break;
    }
    const next = page.getByRole("button", { name: "Page suivante" });
    if (!(await next.isEnabled())) break;
    await next.click();
  }
  expect(found).toBe(true);
  const drawer = page.getByRole("dialog", { name: /demo-d2-facture-valide.csv/ });
  await expect(drawer).toBeVisible();
  await drawer.getByRole("tab", { name: "Factures" }).click();
  await expect(drawer.getByText("DM-2026-001")).toBeVisible();
  await drawer.getByRole("button", { name: "Fermer" }).click();

  await page.getByRole("button", { name: "Analyse & KPI" }).click();
  await expect(page.getByText("Réconciliation par devise")).toBeVisible();
  await expect(page.getByText(/1.344/).first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("local-analytics.png"), fullPage: true });

  await page.getByRole("button", { name: "Assistant IA" }).click();
  await expect(page.getByText("Ollama local prêt")).toBeVisible();

  // Check D5.1 source is actually served by Vite, not a stale D5 process.
  // Verify the help shortcut and guide before the slower real Ollama request.
  await expect(page.getByRole("button", { name: "Découvrir DocuMind" })).toBeVisible();
  let askRequests = 0;
  page.on("request", request => {
    if (request.url().includes("/api/v1/assistant/ask")) askRequests += 1;
  });
  await page.getByRole("button", { name: "Découvrir DocuMind" }).click();
  await expect(page.getByRole("textbox", { name: "Poser une question documentaire" }))
    .toHaveValue("Que peux-tu faire ?");
  await page.getByRole("button", { name: "Envoyer la question" }).click();
  await expect(page.getByText("Guide de l'application")).toBeVisible();
  await expect(page.getByText(/Je peux rechercher des informations dans les documents locaux/)).toBeVisible();
  expect(askRequests, "Deterministic product help must not call Ollama/RAG").toBe(0);
  await page.screenshot({ path: testInfo.outputPath("local-assistant-guide.png"), fullPage: true });

  // The exact product-help phrasing observed in the visual review previously abstained.
  await page.getByRole("textbox", { name: "Poser une question documentaire" })
    .fill("on quoi consiste cette app ?");
  await page.getByRole("button", { name: "Envoyer la question" }).click();
  await expect(page.getByText(/DocuMind est une application locale d'analyse documentaire/)).toBeVisible();
  expect(askRequests, "Product description must not create an AI request").toBe(0);

  await page.getByRole("textbox", { name: "Poser une question documentaire" })
    .fill("Quel est le montant TTC de la facture DM-2026-001 ?");
  await page.getByRole("button", { name: "Envoyer la question" }).click();
  await expect(page.getByText("Réponse sourcée")).toBeVisible({ timeout: 165000 });
  await expect(page.getByText("demo-d2-facture-valide.csv")).toBeVisible();
  expect(askRequests, "Factual questions must still use the real RAG API").toBeGreaterThan(0);
  await page.screenshot({ path: testInfo.outputPath("local-assistant-cited.png"), fullPage: true });
});

test("D5.1 five views fit desktop and mobile and audit outcomes are not misleading", async ({ page }, testInfo) => {
  test.skip(!password, "Private local account credentials not available.");
  const nav = page.getByRole("navigation", { name: "Sections de DocuMind" });
  const pages = [
    ["Vue d'ensemble", "overview"],
    ["Documents", "documents"],
    ["Analyse & KPI", "analytics"],
    ["Assistant IA", "assistant"],
    ["Historique", "history"],
  ] as const;
  for (const viewport of [
    { width: 1920, height: 993 },
    { width: 1649, height: 928 },
    { width: 1440, height: 900 },
    { width: 1320, height: 742 }, // scaled mid-size laptop CSS viewport
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    if (!page.url().endsWith("/") || !(await page.locator(".workspace").count())) {
      await page.goto("/");
    }
    if (await page.getByLabel("Mot de passe local").count()) {
      await page.getByLabel("Mot de passe local").fill(password!);
      await page.getByRole("button", { name: /Accéder à DocuMind/i }).click();
      await expect(page.getByRole("heading", { name: /Vos documents/i })).toBeVisible();
    }
    // Screenshots must not be obstructed by the login success notice.
    const noticeClose = page.getByRole("button", { name: "Fermer la notification" });
    if (await noticeClose.isVisible()) await noticeClose.click();
    for (const [title, key] of pages) {
      if (viewport.width <= 875) {
        await page.getByRole("button", { name: "Ouvrir la navigation" }).click();
      }
      await nav.getByRole("button", { name: title, exact: true }).click();
      await expect(page.locator(".workspace-content .page-stack").first()).toBeVisible();
      if (key === "overview") {
        const hero = page.locator(".overview-hero");
        await expect(hero).toBeVisible();
        await expect(hero.getByRole("heading", { name: /Gérez, vérifiez, analysez et interrogez vos documents/i }))
          .toBeVisible();
        // Four genuine API-backed KPIs are part of the hero, not a separate row.
        await expect(hero.locator(".overview-hero-kpis .stat-card")).toHaveCount(4);
        await expect(hero.getByText("Documents suivis")).toBeVisible();
        await expect(hero.getByText("Validés ou indexés")).toBeVisible();
        await expect(hero.getByText("Montant TTC vérifié")).toBeVisible();
        await expect(hero.getByText("Documents rejetés")).toBeVisible();
        if (viewport.width >= 1200 && viewport.height >= 730) {
          const fitted = await hero.evaluate(el => {
            const frame = el.getBoundingClientRect();
            const metrics = el.querySelector<HTMLElement>(".overview-hero-kpis")?.getBoundingClientRect();
            return Boolean(metrics && metrics.left >= frame.left - 1 &&
              metrics.right <= frame.right + 1 && metrics.bottom <= frame.bottom + 1);
          });
          expect(fitted, "Hero KPI containment at " + viewport.width + "x" + viewport.height).toBe(true);
        }
      }

      if (key === "documents") {
        const hero = page.locator(".documents-hero");
        await expect(hero.getByRole("heading", { name: /Bibliothèque documentaire/ })).toBeVisible();
        await expect(hero.locator(".documents-overview-stat")).toHaveCount(4);
        await expect(hero.getByRole("button", { name: /Importer un document/i })).toBeVisible();
        await expect(page.locator(".documents-cockpit .document-table-pane")).toBeVisible();
        if (viewport.width >= 1120) {
          const inspector = page.locator(".documents-cockpit .documents-preview-layer");
          await expect(inspector).toBeVisible();
          const fitted = await page.evaluate(() => {
            const host = document.querySelector<HTMLElement>(".documents-cockpit");
            const catalogue = host?.querySelector<HTMLElement>(".document-table-pane");
            const detail = host?.querySelector<HTMLElement>(".documents-preview-layer");
            if (!host || !catalogue || !detail) return false;
            const outer = host.getBoundingClientRect();
            const left = catalogue.getBoundingClientRect();
            const right = detail.getBoundingClientRect();
            return left.right <= right.left + 1 && right.right <= outer.right + 1;
          });
          expect(fitted, "Catalogue and preview must not overlap").toBe(true);
        }
      }
      const dimensions = await page.evaluate(() => {
        const root = document.documentElement;
        const appShell = document.querySelector<HTMLElement>(".app-shell");
        const workspace = document.querySelector<HTMLElement>(".workspace");
        const main = document.querySelector<HTMLElement>(".workspace-content");
        const bound = main?.getBoundingClientRect();
        const protruding = bound ? [...main!.querySelectorAll<HTMLElement>("*")]
          .map(element => {
            const rect = element.getBoundingClientRect();
            return { element: element.tagName.toLowerCase(), className:
              typeof element.className === "string" ? element.className.slice(0, 75) : "",
              extra: Math.round(rect.right - bound.right), width: Math.round(rect.width) };
          })
          .filter(item => item.extra > 1 && item.width > 0)
          .sort((a, b) => b.extra - a.extra).slice(0, 8) : [];
        return {
          screen: window.innerWidth,
          viewportHeight: window.innerHeight,
          shellBottom: appShell?.getBoundingClientRect().bottom ?? null,
          workspaceBottom: workspace?.getBoundingClientRect().bottom ?? null,
          root: root.scrollWidth,
          mainClient: main?.clientWidth ?? 0,
          mainScroll: main?.scrollWidth ?? 0,
          mainHeight: main?.clientHeight ?? 0,
          mainScrollHeight: main?.scrollHeight ?? 0,
          protruding,
        };
      });
      expect(dimensions.root, `${key} at ${viewport.width} — root overflow`)
        .toBeLessThanOrEqual(dimensions.screen + 1);
      if (viewport.width >= 1100 && viewport.height >= 650) {
        expect(dimensions.shellBottom,
          `${key} at ${viewport.width}x${viewport.height} — shell extends beyond viewport`)
          .not.toBeNull();
        expect(dimensions.workspaceBottom,
          `${key} at ${viewport.width}x${viewport.height} — workspace extends beyond viewport (implicit CSS grid row)`)
          .toBeLessThanOrEqual(dimensions.viewportHeight + 1);
      }
      expect(dimensions.mainScroll, `${key} at ${viewport.width} — main overflow; protruding elements: ${JSON.stringify(dimensions.protruding)}`)
        .toBeLessThanOrEqual(dimensions.mainClient + 1);
      // On usable desktop heights, all dashboard modules should fit within
      // the viewport; documents and long audit logs scroll inside their panes.
      if (viewport.width >= 1200 && viewport.height >= 730 &&
          (key === "overview" || key === "analytics")) {
        expect(dimensions.mainScrollHeight,
          `${key} at ${viewport.width}x${viewport.height} — outer vertical scroll remains`)
          .toBeLessThanOrEqual(dimensions.mainHeight + 2);
      }
      // Always capture before layout assertions: on failure the precise
      // problematic viewport remains inspectable without rerunning Ollama.
      await page.screenshot({
        path: testInfo.outputPath(`d51-${key}-${viewport.width}x${viewport.height}.png`),
        fullPage: false,
      });
      if (key === "assistant" && viewport.width >= 1100 && viewport.height >= 650 && viewport.height <= 800) {
        // A real bottom-of-screen check, not just a scrollWidth assertion.
        const geometry = await page.evaluate(() => {
          const rect = (selector: string) => {
            const element = document.querySelector<HTMLElement>(selector);
            if (!element) return null;
            const bounds = element.getBoundingClientRect();
            return { top: Math.round(bounds.top), bottom: Math.round(bounds.bottom),
              height: Math.round(bounds.height), scrollHeight: element.scrollHeight,
              clientHeight: element.clientHeight };
          };
          return {
            viewport: window.innerHeight,
            shell: rect(".app-shell"),
            workspaceColumn: rect(".workspace"),
            workspace: rect(".workspace-content.is-assistant"),
            page: rect(".assistant-page"),
            grid: rect(".assistant-grid"),
            main: rect(".assistant-main"),
            composer: rect(".assistant-compose"),
            composeFooter: rect(".compose-footer"),
          };
        });
        expect(geometry.composeFooter, `Composer missing at ${viewport.width}x${viewport.height}`).not.toBeNull();
        expect(geometry.composeFooter!.bottom,
          `Assistant composer clipped at ${viewport.width}x${viewport.height}: ${JSON.stringify(geometry)}`)
          .toBeLessThanOrEqual(geometry.viewport - 2);
        await expect(page.locator(".compose-footer")).toBeInViewport({ ratio: 0.99 });
        await expect(page.getByRole("button", { name: "Envoyer la question" })).toBeInViewport();
      }
    }
  }
  await page.setViewportSize({ width: 1649, height: 928 });
  await nav.getByRole("button", { name: "Historique" }).click();
  await expect(page.locator(".timeline-danger").first()).toBeVisible();
  await expect(page.getByText("Traitement rejeté").first()).toBeVisible();
  await expect(page.getByText("Document indexé pour l'IA").first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("d51-audit-color-and-time.png") });

  await nav.getByRole("button", { name: "Documents", exact: true }).click();
  await page.getByRole("button", { name: /documind-d3-anomalie.csv/ }).first().click();
  const dialog = page.getByRole("dialog", { name: /documind-d3-anomalie.csv/ });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: /Retraiter le document/ })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Indexer pour l'IA" })).toHaveCount(0);
  await dialog.getByRole("tab", { name: "Anomalies" }).click();
  await expect(dialog.getByText(/TTC attendu/)).toBeVisible();
  await expect(dialog.getByText("Incohérence du montant TTC")).toBeVisible();
  await dialog.getByRole("button", { name: "Fermer" }).click();
});
