import type { DocState, Monthly } from "./types";

export function money(amount: string | number | null | undefined, currency = "EUR"): string {
  if (amount == null || amount === "") return "—";
  const numeric = Number(amount);
  if (!Number.isFinite(numeric)) return "—";
  try {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency", currency, maximumFractionDigits: 2,
    }).format(numeric);
  } catch {
    return `${numeric.toLocaleString("fr-FR")} ${currency}`;
  }
}

export function shortDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit", month: "short", year: "numeric",
    timeZone: "Europe/Paris",
  }).format(date);
}

export function monthName(month: string): string {
  const date = new Date(`${month.slice(0, 7)}-01T12:00:00Z`);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fr-FR", {
    month: "short", year: "2-digit", timeZone: "UTC",
  }).format(date);
}

export function bytes(value: number): string {
  if (!Number.isFinite(value) || value < 0) return "—";
  if (value === 0) return "0 octet";
  if (value < 1024) return `${value} octets`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} Ko`;
  return `${(value / 1024 / 1024).toFixed(2)} Mo`;
}

export const stateLabels: Record<DocState, string> = {
  RECEIVED: "Reçu",
  VALIDATING: "En traitement",
  ACCEPTED: "Accepté",
  INDEXED: "Indexé",
  REJECTED: "Rejeté",
};

export function monthlyEUR(rows: Monthly[]): Monthly[] {
  return rows.filter(row => row.currency === "EUR").sort(
    (a, b) => a.month.localeCompare(b.month),
  );
}

export function percent(numerator: number, denominator: number): string {
  if (!denominator) return "—";
  return `${new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 1,
  }).format(100 * numerator / denominator)} %`;
}
