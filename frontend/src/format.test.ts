import { describe, expect, it } from "vitest";
import { bytes, money, monthlyEUR, percent, shortDate } from "./format";

describe("D5 formatting without invented metrics", () => {
  it("shows unavailable values as an em dash, never zero euros", () => {
    expect(money(null)).toBe("—");
    expect(money(undefined)).toBe("—");
    expect(money("not a number")).toBe("—");
    expect(percent(0, 0)).toBe("—");
  });
  it("formats real decimal EUR strings from Django", () => {
    const result = money("1344.00", "EUR");
    expect(result).toContain("344");
    expect(result).toContain("€");
    expect(money("12.30", "USD")).toContain("12");
  });
  it("never adds unrelated currencies to the EUR trend", () => {
    const entries = [
      { month: "2026-09-01", currency: "USD", invoice_count: 1, total: "999.00" },
      { month: "2026-10-01", currency: "EUR", invoice_count: 2, total: "42.00" },
      { month: "2026-09-01", currency: "EUR", invoice_count: 1, total: "11.00" },
    ];
    expect(monthlyEUR(entries).map(v => v.total)).toEqual(["11.00", "42.00"]);
  });
  it("keeps human-readable dates and sizes", () => {
    expect(shortDate("2026-11-09T12:00:00Z")).toContain("2026");
    expect(bytes(1024)).toBe("1.0 Ko");
    expect(bytes(0)).toBe("0 octet");
  });
});
