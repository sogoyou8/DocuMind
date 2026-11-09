"""D3 artificial business history. Never present these as real business observations.

The existing D2 November corpus contributes 3 valid invoices (240 EUR TTC).
These four added monthly CSVs contribute 12 invoices (1104 EUR TTC).
"""
from decimal import Decimal


HEADERS = "fournisseur,numero_facture,date_facture,devise,ht,tva,ttc\n"
ROWS = {
    "2026-07": [
        ("Atelier Fictif", "D3-2026-07-A", "65", "13", "78"),
        ("Librairie Fictive", "D3-2026-07-L", "90", "18", "108"),
        ("Imprimerie Fictive", "D3-2026-07-I", "45", "9", "54"),
    ],
    "2026-08": [
        ("Atelier Fictif", "D3-2026-08-A", "110", "22", "132"),
        ("Librairie Fictive", "D3-2026-08-L", "80", "16", "96"),
        ("Imprimerie Fictive", "D3-2026-08-I", "35", "7", "42"),
    ],
    "2026-09": [
        ("Atelier Fictif", "D3-2026-09-A", "130", "26", "156"),
        ("Librairie Fictive", "D3-2026-09-L", "70", "14", "84"),
        ("Imprimerie Fictive", "D3-2026-09-I", "55", "11", "66"),
    ],
    "2026-10": [
        ("Atelier Fictif", "D3-2026-10-A", "85", "17", "102"),
        ("Librairie Fictive", "D3-2026-10-L", "95", "19", "114"),
        ("Imprimerie Fictive", "D3-2026-10-I", "60", "12", "72"),
    ],
}


def d3_example_files():
    """Bytes are deliberately fixed, including line ordering and LF endings."""
    files = []
    for month, rows in ROWS.items():
        values = [HEADERS]
        for supplier, number, subtotal, tax, total in rows:
            values.append(
                f"{supplier},{number},{month}-15,EUR,{subtotal},{tax},{total}\n"
            )
        files.append((f"documind-d3-{month}.csv", "".join(values).encode("utf-8")))

    anomaly = (
        HEADERS + "Atelier Fictif,D3-2026-08-ERROR,2026-08-17,EUR,20,4,30\n"
    ).encode("utf-8")
    files.append(("documind-d3-anomalie.csv", anomaly))
    return files


def synthetic_expected_monthly():
    totals = {
        month: sum((Decimal(row[4]) for row in rows), Decimal("0"))
        for month, rows in ROWS.items()
    }
    # D2 three genuine extracted synthetic files all dated 2026-11-09.
    totals["2026-11"] = Decimal("240.00")
    return dict(sorted(totals.items()))
