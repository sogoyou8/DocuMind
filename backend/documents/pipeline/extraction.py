"""Bounded PDF/CSV/XLSX extraction with source locators.

This module has no Django dependencies and never sends data to a third party.
A RawRecord represents one CSV logical record, one XLSX row, or one PDF page.
"""
from dataclasses import dataclass
from io import BytesIO
from typing import Any

MAX_SOURCE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000
MAX_COLUMNS = 40
MAX_SHEETS = 10
MAX_PAGES = 20
MAX_PDF_TEXT_CHARS = 200_000


class ExtractionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class RawRecord:
    source_locator: str
    fields: dict[str, Any]


def extract_records(data: bytes, file_type: str) -> list[RawRecord]:
    if not data or len(data) > MAX_SOURCE_BYTES:
        raise ExtractionError("SIZE_INVALID", "Source absente ou supérieure à 5 Mio.")
    match file_type.upper():
        case "CSV":
            return _csv_records(data)
        case "XLSX":
            return _xlsx_records(data)
        case "PDF":
            return _pdf_records(data)
        case _:
            raise ExtractionError("FORMAT_UNSUPPORTED", "Seuls PDF, CSV et XLSX sont traités.")


def _csv_records(data: bytes) -> list[RawRecord]:
    import pandas as pd

    try:
        # UTF-8 and Python CSV dialect sniffing: semicolon and comma are supported.
        table = pd.read_csv(
            BytesIO(data), encoding="utf-8-sig", sep=None, engine="python",
            dtype=str, keep_default_na=False, nrows=MAX_ROWS + 1,
            on_bad_lines="error",
        )
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError, OSError) as exc:
        raise ExtractionError("CSV_PARSE_ERROR", "Impossible de lire le CSV UTF-8.") from exc
    if len(table) > MAX_ROWS:
        raise ExtractionError("ROW_LIMIT", "Maximum 5 000 lignes de données.")
    if table.empty or len(table.columns) == 0:
        raise ExtractionError("EMPTY_DOCUMENT", "CSV sans ligne de données.")
    if len(table.columns) > MAX_COLUMNS:
        raise ExtractionError("COLUMN_LIMIT", "Maximum 40 colonnes.")
    names = [str(column).strip() for column in table.columns]
    if len(set(names)) != len(names) or any(not name or name.startswith("Unnamed:") for name in names):
        raise ExtractionError("INVALID_HEADER", "En-têtes CSV absents ou dupliqués.")
    table.columns = names
    records = table.to_dict(orient="records")
    return [
        RawRecord(f"csv:record:{index}", {key: str(value) for key, value in row.items()})
        for index, row in enumerate(records, 1)
    ]


def _xlsx_records(data: bytes) -> list[RawRecord]:
    import pandas as pd
    from openpyxl import load_workbook
    from zipfile import BadZipFile

    try:
        book = load_workbook(BytesIO(data), read_only=True, data_only=True, keep_links=False)
    except (ValueError, BadZipFile, OSError, KeyError) as exc:
        raise ExtractionError("XLSX_PARSE_ERROR", "Classeur XLSX illisible.") from exc
    try:
        if len(book.worksheets) > MAX_SHEETS:
            raise ExtractionError("SHEET_LIMIT", "Maximum 10 feuilles Excel.")
        result: list[RawRecord] = []
        for sheet in book.worksheets:
            iterator = sheet.iter_rows(max_row=MAX_ROWS + 2, max_col=MAX_COLUMNS + 1, values_only=True)
            header_row = next(iterator, None)
            if header_row is None or all(value is None for value in header_row):
                continue
            if len(header_row) > MAX_COLUMNS and any(value is not None for value in header_row[MAX_COLUMNS:]):
                raise ExtractionError("COLUMN_LIMIT", "Maximum 40 colonnes Excel.")
            names = [str(value).strip() if value is not None else "" for value in header_row[:MAX_COLUMNS]]
            while names and not names[-1]:
                names.pop()
            if not names or len(set(names)) != len(names) or any(not name for name in names):
                raise ExtractionError("INVALID_HEADER", f"En-tête invalide dans {sheet.title}.")
            rows: list[dict[str, str]] = []
            for values in iterator:
                if all(v is None or str(v).strip() == "" for v in values):
                    continue
                if len(values) > len(names) and any(v is not None for v in values[len(names):]):
                    raise ExtractionError("COLUMN_LIMIT", "Cellules hors en-têtes Excel.")
                rows.append({
                    key: "" if value is None else str(value)
                    for key, value in zip(names, values)
                })
                if len(rows) + len(result) > MAX_ROWS:
                    raise ExtractionError("ROW_LIMIT", "Maximum 5 000 lignes de données.")
            if not rows:
                continue
            frame = pd.DataFrame.from_records(rows, columns=names).fillna("")
            for number, record in enumerate(frame.to_dict(orient="records"), 2):
                result.append(RawRecord(
                    f"xlsx:{sheet.title}:row:{number}",
                    {key: str(value) for key, value in record.items()},
                ))
        if not result:
            raise ExtractionError("EMPTY_DOCUMENT", "Classeur sans ligne de données.")
        return result
    except ExtractionError:
        raise
    except (TypeError, ValueError, OSError) as exc:
        raise ExtractionError("XLSX_PARSE_ERROR", "Lecture des lignes Excel impossible.") from exc
    finally:
        book.close()


def _pdf_records(data: bytes) -> list[RawRecord]:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ExtractionError("PDF_ENCRYPTED", "PDF chiffré non autorisé.")
        if len(reader.pages) > MAX_PAGES:
            raise ExtractionError("PAGE_LIMIT", "Maximum 20 pages PDF.")
        if not reader.pages:
            raise ExtractionError("EMPTY_DOCUMENT", "PDF sans page.")
        total_chars = 0
        records: list[RawRecord] = []
        for index, page in enumerate(reader.pages, 1):
            # Only genuine extractable text; never OCR scanned/handwritten documents.
            text = page.extract_text() or ""
            total_chars += len(text)
            if total_chars > MAX_PDF_TEXT_CHARS:
                raise ExtractionError("PDF_TEXT_LIMIT", "Texte PDF trop volumineux.")
            if not text.strip():
                raise ExtractionError("PDF_NO_TEXT", f"Page {index} sans texte extractible (OCR exclu).")
            fields: dict[str, str] = {"_page_text": text[:8000]}
            for line in text.splitlines():
                separator = ":" if ":" in line else ("=" if "=" in line else None)
                if not separator:
                    continue
                key, value = line.split(separator, 1)
                if 0 < len(key.strip()) <= 80 and value.strip():
                    fields[key.strip()] = value.strip()
            records.append(RawRecord(f"pdf:page:{index}", fields))
        return records
    except ExtractionError:
        raise
    except (PdfReadError, ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        raise ExtractionError("PDF_PARSE_ERROR", "PDF textuel endommagé ou non pris en charge.") from exc
