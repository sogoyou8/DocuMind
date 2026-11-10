import { describe, expect, it } from "vitest";
import type { Citation, RecordRow } from "./types";
import {
  applicationHelp, displayedAnswer, eventDate, eventLabel, eventTone,
  fieldLabel, issueLabel, mismatchEvidence, runLabel, sourceLabel,
} from "./ux";

const rejectedRecord: RecordRow = {
  id: "row-1", document: "document-1", run: "run-1",
  source_locator: "csv:record:1", raw_fields: {},
  normalized_fields: {
    subtotal: "20.00", tax: "4.00", total: "30.00",
    currency: "EUR", number: "D3-2026-08-ERROR",
  },
};
const citation: Citation = {
  id: "E1", document_id: "doc-1", document: "demo-d2-facture-valide.csv",
  source_locator: "csv:record:1",
  excerpt: "ht: 100.00 ttc: 120.00 tva: 20.00 devise: EUR fournisseur: Atelier Fictif",
};

describe("D5.1 visual-review business contracts", () => {
  it("translates business names without changing technical source identifiers", () => {
    expect(fieldLabel("subtotal")).toBe("Montant HT");
    expect(fieldLabel("tax")).toBe("TVA");
    expect(fieldLabel("supplier_key")).toBe("Identifiant fournisseur");
    expect(sourceLabel("csv:record:1")).toBe("CSV · Enregistrement 1");
    expect(sourceLabel("pdf:page:3")).toBe("PDF · Page 3");
    expect(sourceLabel("xlsx:sheet:Feuil1:row:4")).toBe("Tableur · Ligne 4");
    expect(sourceLabel("unknown:1")).toBe("unknown:1");
  });
  it("distinguishes audit successes, rejections and neutral seed events", () => {
    expect(eventLabel("RAG_INDEXED")).toBe("Document indexé pour l'IA");
    expect(eventLabel("PROCESSING_REJECTED")).toBe("Traitement rejeté");
    expect(eventTone("PROCESSING_REJECTED")).toBe("danger");
    expect(eventTone("RAG_INDEXED")).toBe("good");
    expect(eventTone("SYNTHETIC_SEEDED")).toBe("neutral");
    expect(runLabel("SUCCEEDED")).toBe("Réussi");
    expect(issueLabel("TOTAL_MISMATCH")).toBe("Incohérence du montant TTC");
    expect(eventDate("2026-11-09T12:30:00Z")).toContain("13:30");
  });
  it("computes mismatch explanation solely from real extracted fields", () => {
    const explanation = mismatchEvidence(rejectedRecord);
    expect(explanation).toContain("24,00");
    expect(explanation).toContain("30,00");
    expect(explanation).toContain("6,00");
    expect(mismatchEvidence(undefined)).toBeNull();
    expect(mismatchEvidence({
      ...rejectedRecord, normalized_fields: { subtotal: "20.00", total: "30.00" },
    })).toBeNull();
  });
  it("answers general DocuMind usage locally without inventing a source", () => {
    expect(applicationHelp("Que peux-tu faire ?")).toContain("citations");
    expect(applicationHelp("que peut tu faire ?")).toContain("Documents");
    expect(applicationHelp("Quels types de documents sont accepter ?")).toContain("XLSX");
    expect(applicationHelp("Quels fichiers puis-je importer ?")).toContain("CSV");
    expect(applicationHelp("en quoi consiste cette app ?")).toContain("analyse documentaire");
    expect(applicationHelp("on quoi consiste cette app ?")).toContain("analyse documentaire");
    expect(applicationHelp("À quoi sert cette application ?")).toContain("factures");
    expect(applicationHelp("C'est quoi DocuMind ?")).toContain("journal");
    expect(applicationHelp("Explique-moi DocuMind")).toContain("SQL");
    expect(applicationHelp("En quoi consiste ce document accepté ?")).toBeNull();
    expect(applicationHelp("Quel est le montant TTC de la facture DM-2026-001 ?")).toBeNull();
    expect(applicationHelp("Quel est le montant TTC de la facture ZXZ-9999 ?")).toBeNull();
  });
  it("only formats an independently cited EUR TTC numeric answer", () => {
    const question = "Quel est le montant TTC de la facture DM-2026-001 ?";
    expect(displayedAnswer(question, "120.00", [citation])).toContain("120,00");
    expect(displayedAnswer(question, "120.00", [citation])).toContain("TTC");
    expect(displayedAnswer(question, "120.00", [])).toBe("120.00");
    expect(displayedAnswer("Combien de lignes ?", "120.00", [citation])).toBe("120.00");
    expect(displayedAnswer(question, "Je ne sais pas.", [citation])).toBe("Je ne sais pas.");
  });
});
