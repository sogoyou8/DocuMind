"""Deterministic invoice field mapping and validation — never infer missing amounts."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata


ALIAS_GROUPS = {
    "supplier": {"supplier", "supplier_name", "vendor", "fournisseur", "nom_fournisseur"},
    "number": {"invoice", "invoice_number", "invoice_id", "facture", "numero_facture", "num_facture", "n_facture"},
    "issued_on": {"date", "invoice_date", "date_facture", "date_emission", "issued_on"},
    "currency": {"currency", "devise", "monnaie"},
    "subtotal": {"subtotal", "ht", "montant_ht", "total_ht", "hors_taxe"},
    "tax": {"tax", "vat", "tva", "montant_tva", "taxe"},
    "total": {"total", "ttc", "total_ttc", "montant_ttc"},
}


def canonical_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


FIELD_BY_ALIAS = {
    alias: key for key, aliases in ALIAS_GROUPS.items() for alias in aliases
}


@dataclass(frozen=True)
class NormalizedRow:
    fields: dict[str, str]
    issues: tuple[dict[str, str], ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _issue(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "severity": "ERROR", "message": message}


def _amount(text: str) -> Decimal:
    source = str(text).strip().replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if not source or not re.fullmatch(r"[0-9][0-9.,]*", source):
        raise ValueError("Montant non numérique ou négatif.")
    if "," in source and "." in source:
        decimal_sep = "," if source.rfind(",") > source.rfind(".") else "."
        grouping_sep = "." if decimal_sep == "," else ","
        source = source.replace(grouping_sep, "").replace(decimal_sep, ".")
    elif "," in source:
        source = source.replace(",", ".")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", source):
        raise ValueError("Montant ambigu ou précision supérieure à 2 décimales.")
    try:
        amount = Decimal(source)
    except InvalidOperation as exc:
        raise ValueError("Montant invalide.") from exc
    if amount < 0 or amount > Decimal("9999999999.99"):
        raise ValueError("Montant hors bornes.")
    return amount.quantize(Decimal("0.01"))


def _date(text: str) -> date:
    value = str(text).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("Date attendue en AAAA-MM-JJ ou JJ/MM/AAAA.")


def normalize_invoice(source: dict[str, object]) -> NormalizedRow:
    mapped: dict[str, str] = {}
    problems: list[dict[str, str]] = []
    for raw_key, raw_value in source.items():
        key = FIELD_BY_ALIAS.get(canonical_key(raw_key))
        if key is None:
            continue
        value = str(raw_value).strip() if raw_value is not None else ""
        if key in mapped and mapped[key] != value:
            problems.append(_issue("AMBIGUOUS_FIELD", key, f"Valeurs contradictoires pour {key}."))
        else:
            mapped[key] = value

    for key in ALIAS_GROUPS:
        if not mapped.get(key):
            problems.append(_issue("MISSING_FIELD", key, f"Champ obligatoire absent : {key}."))
    if problems:
        return NormalizedRow({}, tuple(problems))

    values: dict[str, str] = {}
    values["supplier"] = mapped["supplier"][:150]
    values["supplier_key"] = canonical_key(mapped["supplier"])
    values["number"] = mapped["number"][:100]
    if not values["supplier_key"] or len(mapped["supplier"]) > 150 or len(mapped["number"]) > 100:
        problems.append(_issue("INVALID_TEXT", "supplier", "Nom ou numéro trop long/invalide."))

    try:
        values["issued_on"] = _date(mapped["issued_on"]).isoformat()
    except ValueError as exc:
        problems.append(_issue("INVALID_DATE", "issued_on", str(exc)))

    currency = mapped["currency"].upper()
    if currency not in {"EUR", "USD", "GBP"}:
        problems.append(_issue("INVALID_CURRENCY", "currency", "Devise explicite EUR, USD ou GBP requise."))
    else:
        values["currency"] = currency

    amounts: dict[str, Decimal] = {}
    for key in ("subtotal", "tax", "total"):
        try:
            amounts[key] = _amount(mapped[key])
            values[key] = str(amounts[key])
        except ValueError as exc:
            problems.append(_issue("INVALID_AMOUNT", key, str(exc)))
    if len(amounts) == 3:
        if amounts["total"] == 0:
            problems.append(_issue("INVALID_TOTAL", "total", "TTC doit être positif."))
        if abs(amounts["subtotal"] + amounts["tax"] - amounts["total"]) > Decimal("0.01"):
            problems.append(_issue("TOTAL_MISMATCH", "total", "HT + TVA doit être égal au TTC (tolérance 0,01)."))

    return NormalizedRow(values, tuple(problems))
