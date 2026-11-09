"""Reproducible, explicitly fictional D2 source corpus (no real invoices)."""
from io import BytesIO
from openpyxl import Workbook


def make_text_pdf(lines: list[str]) -> bytes:
    """Produce a tiny, genuine text-layer PDF with only standard ASCII glyphs.

    Intended for deterministic test fixtures, not a user-facing PDF generator.
    """
    safe_lines = []
    for line in lines:
        line = line.encode("ascii", "strict").decode("ascii")
        safe_lines.append(line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)"))
    stream = "BT /F1 12 Tf 50 760 Td 18 TL\n"
    stream += "".join(f"({line}) Tj T*\n" for line in safe_lines)
    stream += "ET\n"
    content = stream.encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"endstream",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        result += f"{offset:010d} 00000 n \n".encode()
    result += f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(result)


def example_files() -> list[tuple[str, bytes]]:
    """Three valid examples and one intentional accounting anomaly."""
    csv_ok = (
        "fournisseur,numero_facture,date_facture,devise,ht,tva,ttc\n"
        "Atelier Fictif,DM-2026-001,2026-11-09,EUR,100.00,20.00,120.00\n"
    ).encode("utf-8")
    csv_bad = (
        "fournisseur,numero_facture,date_facture,devise,ht,tva,ttc\n"
        "Studio Fictif,DM-2026-ERR,09/11/2026,EUR,50.00,10.00,100.00\n"
    ).encode("utf-8")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Factures"
    sheet.append(["Supplier", "Invoice Number", "Date", "Currency", "Subtotal", "Tax", "Total"])
    sheet.append(["Librairie Fictive", "DM-2026-002", "2026-11-09", "EUR", 70, 14, 84])
    out = BytesIO()
    workbook.save(out)

    pdf = make_text_pdf([
        "Fournisseur: Imprimerie Fictive",
        "Numero facture: DM-2026-003",
        "Date: 2026-11-09",
        "Devise: EUR",
        "HT: 30.00",
        "TVA: 6.00",
        "TTC: 36.00",
    ])
    return [
        ("demo-d2-facture-valide.csv", csv_ok),
        ("demo-d2-factures.xlsx", out.getvalue()),
        ("demo-d2-facture-texte.pdf", pdf),
        ("demo-d2-facture-anomalie.csv", csv_bad),
    ]
