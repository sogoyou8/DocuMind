import type { Citation, RecordRow } from "./types";
import { money } from "./format";

/** UI-only vocabulary. The original backend codes and source identifiers stay intact. */
const fields: Record<string, string> = {
  tax: "TVA", total: "Montant TTC", subtotal: "Montant HT",
  number: "N° de facture", invoice_number: "N° de facture",
  currency: "Devise", supplier: "Fournisseur",
  supplier_name: "Fournisseur", supplier_key: "Identifiant fournisseur",
  issued_on: "Date de facture",
};
export function fieldLabel(code: string): string {
  return fields[code] ?? code.replace(/_/g, " ");
}

const actions: Record<string, string> = {
  RAG_INDEXED: "Document indexé pour l'IA",
  PROCESSING_ACCEPTED: "Traitement validé",
  PROCESSING_REJECTED: "Traitement rejeté",
  PROCESSING_FAILED: "Échec du traitement",
  SYNTHETIC_SEEDED: "Exemple fictif initialisé",
  DOCUMENT_RECEIVED: "Document reçu",
  DOCUMENT_UPLOADED: "Document importé",
  DOCUMENT_INDEXED: "Document indexé",
};
export function eventLabel(code: string): string {
  return actions[code] ?? code.replace(/_/g, " ");
}
export function eventTone(code: string): "good" | "danger" | "neutral" {
  if (/REJECTED|FAILED|ERROR/.test(code)) return "danger";
  if (code === "SYNTHETIC_SEEDED" || /RECEIVED|UPLOADED/.test(code)) return "neutral";
  if (/ACCEPTED|INDEXED|SUCCEEDED/.test(code)) return "good";
  return "neutral";
}
export function runLabel(status: string): string {
  return ({
    RUNNING: "En cours", SUCCEEDED: "Réussi",
    REJECTED: "Rejeté", FAILED: "Échec",
  } as Record<string, string>)[status] ?? status;
}
export function issueLabel(code: string): string {
  return code === "TOTAL_MISMATCH" ? "Incohérence du montant TTC" : code.replace(/_/g, " ");
}
export function sourceLabel(locator: string): string {
  const csv = /^csv:record:(\d+)$/i.exec(locator);
  if (csv) return `CSV · Enregistrement ${csv[1]}`;
  const pdf = /^pdf:page:(\d+)$/i.exec(locator);
  if (pdf) return `PDF · Page ${pdf[1]}`;
  const row = /(?:^|:)row:(\d+)$/i.exec(locator);
  if (row) return `Tableur · Ligne ${row[1]}`;
  return locator || "Source non précisée";
}
export function eventDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    timeZone: "Europe/Paris",
  }).format(date);
}
export function displayFieldValue(key: string, value: unknown, row: RecordRow): string {
  if (value === null || value === undefined) return "—";
  if (key === "issued_on" && typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-");
    return `${d}/${m}/${y}`;
  }
  if (["tax", "total", "subtotal"].includes(key) && typeof value !== "object") {
    return money(String(value), String(row.normalized_fields.currency || "EUR"));
  }
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

/** Issue explanation is computed only from the actual extracted source row. */
export function mismatchEvidence(record: RecordRow | undefined): string | null {
  if (!record) return null;
  const values = record.normalized_fields;
  const subtotal = Number(values.subtotal), tax = Number(values.tax), total = Number(values.total);
  if ([subtotal, tax, total].some(n => !Number.isFinite(n)) ||
      [values.subtotal, values.tax, values.total].some(v => v === null || v === undefined || v === "")) {
    return null;
  }
  const currency = typeof values.currency === "string" ? values.currency : "EUR";
  const expected = Math.round((subtotal + tax) * 100) / 100;
  const gap = Math.round(Math.abs(total - expected) * 100) / 100;
  return `TTC attendu : ${money(expected, currency)} · TTC déclaré : ${money(total, currency)} · Écart : ${money(gap, currency)}`;
}

/** Deterministic application guide; it never queries or impersonates the document RAG. */
export function applicationHelp(question: string): string | null {
  const q = question.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("fr").replace(/[!?.,\x27’\-]/g, " ").replace(/\s+/g, " ").trim();
  const aboutFormats = /(type(s)?|format(s)?|quel(s)?).*(document(s)?|fichier(s)?).*(accept|import|support|permi)/
    .test(q) || /(document(s)?|fichier(s)?).*(accept|import|support|permi)/.test(q);
  if (aboutFormats && !/factur(e|es)\s+(dm|d3|zxz)/.test(q)) {
    return "DocuMind accepte les PDF textuels (sans OCR), les CSV et les classeurs XLSX jusqu'à 5 Mio par fichier. Dans l'instance locale, le rôle opérateur permet l'import et le traitement ; seuls les documents acceptés peuvent ensuite être indexés pour l'IA. La démonstration publique reste en lecture seule.";
  }
  // A general question about DocuMind itself must not be confused with
  // a question about an indexed invoice or document. No LLM or citation here.
  const aboutApplication = /^(?:(?:en|on) quoi consiste|c est quoi|qu est ce que|a quoi sert|comment fonctionne)\s+(?:(?:cette|une|l|la|ton|votre|le)\s+)?(?:app|application|logiciel|outil|documind)(?:\s|$)/
    .test(q) || /^(?:presente|explique|decris)\s+(?:moi\s+)?(?:documind|cette app|cette application)(?:\s|$)/.test(q);
  if (aboutApplication) {
    return "DocuMind est une application locale d'analyse documentaire. Elle importe des PDF textuels, CSV et XLSX, conserve leur empreinte et leur provenance, extrait les factures, vérifie les montants et signale les anomalies. Les données acceptées alimentent des indicateurs SQL. L'assistant IA local répond aux questions sur les documents indexés avec une citation précise, ou s'abstient sans preuve. Le journal conserve les opérations réalisées.";
  }
  if (/(que (peux|peut|pouvez|sais)( tu| vous)? faire|quelles? (sont )?(tes|vos) fonctionnalites|a quoi sert documind|comment utiliser documind)/.test(q)) {
    return "Je peux rechercher des informations dans les documents locaux acceptés, répondre avec des citations vers leurs emplacements sources ou m'abstenir sans preuve. Pour importer, contrôler et indexer un fichier, utilise « Documents ». Pour les montants validés et les anomalies, ouvre « Analyse & KPI » ; pour les opérations horodatées, ouvre « Historique ». Je n'exécute aucune commande arbitraire et je n'invente pas de source.";
  }
  return null;
}

/** Improve display of an answer supported by an EUR TTC citation, never rewrite its evidence. */
export function displayedAnswer(question: string, answer: string, citations: Citation[]): string {
  const trimmed = answer.trim();
  if (!/\b(ttc|montant total)\b/i.test(question) || !/^\d+(?:[.,]\d{1,2})?$/.test(trimmed)) {
    return answer;
  }
  const evidence = citations.some(c => /\bEUR\b/i.test(c.excerpt) && /\b(?:ttc|montant ttc)\b/i.test(c.excerpt));
  return evidence ? `${money(trimmed.replace(",", "."), "EUR")} TTC` : answer;
}
