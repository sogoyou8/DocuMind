import { describe, expect, it } from "vitest";
import { beginnerRoute, discoveryPage, discoveryPages, discoveryRoute } from "./discovery-data";

describe("DocuMind discovery is a faithful practical guide", () => {
  it("covers precisely the existing five application pages", () => {
    expect(discoveryPages.map(item => item.id)).toEqual(discoveryRoute);
    expect(discoveryRoute).toEqual(["overview", "documents", "analytics", "assistant", "activity"]);
    expect(discoveryPages.every(item => item.purpose && item.steps.length >= 2)).toBe(true);
    expect(beginnerRoute).toEqual(["documents", "overview", "analytics", "assistant", "activity"]);
    expect(discoveryPages.reduce((count, item) => count + item.steps.length, 0)).toBe(15);
  });

  it("gives each step a real interface target, a concrete action and an expected outcome", () => {
    for (const page of discoveryPages) {
      for (const step of page.steps) {
        expect(step.target.startsWith(".")).toBe(true);
        expect(step.action.length).toBeGreaterThan(18);
        expect(step.outcome.length).toBeGreaterThan(15);
        expect(step.title.length).toBeGreaterThan(6);
        expect(step.target).not.toContain("api/");
      }
    }
  });

  it("separates upload, D2 validation, and AI indexing", () => {
    const instructions = discoveryPage("documents").steps;
    expect(instructions.map(step => step.title)).toEqual([
      "Choisir un fichier", "Lancer l'import",
      "Ouvrir la fiche documentaire", "Traiter puis indexer si possible",
    ]);
    expect(instructions[0].action).toContain("5 Mio");
    expect(instructions[1].outcome).toContain("pas encore automatiquement validé");
    expect(instructions[3].action).toContain("Traiter avec D2");
    expect(instructions[3].action).toContain("Indexer pour l'IA");
    expect(instructions[3].caution).toContain("rejeté");
  });

  it("never promises fictitious analytics, AI responses or unavailable actions", () => {
    const analytics = discoveryPage("analytics").steps.map(step => step.action + step.outcome).join(" ");
    const assistant = discoveryPage("assistant").steps.map(step => step.outcome).join(" ");
    const history = discoveryPage("activity").steps.map(step => step.action + step.outcome).join(" ");
    expect(analytics).toContain("devises");
    expect(assistant).toContain("s'abstenir");
    expect(history).toContain("actuellement chargés");
    expect(discoveryPage("assistant").steps[0].action).toContain("sans envoyer");
    const data = JSON.stringify(discoveryPages);
    expect(data).not.toMatch(/1\\s?344|4\\s?560|faker|setTimeout|fetch\\(/);
  });
});
