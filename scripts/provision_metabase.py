"""Idempotent Metabase v0.64.1 local setup using its free REST API.

Runs inside the Django API container over the private Compose network.
Only queries the governed bi schema. Never writes a secret to Git or logs.
"""
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.environ.get("DOCUMIND_METABASE_URL", "http://metabase:3000").rstrip("/")
ADMIN_EMAIL = "admin@documind.local"
ADMIN_PASSWORD = os.environ.get("DOCUMIND_METABASE_ADMIN_PASSWORD", "")
BI_PASSWORD = os.environ.get("DOCUMIND_BI_PASSWORD", "")
COLLECTION_NAME = "DocuMind - D3 analytique"
DATABASE_NAME = "DocuMind BI (lecture seule)"
DASHBOARD_NAME = "DocuMind | Pilotage documentaire"

if not ADMIN_PASSWORD or not BI_PASSWORD:
    raise SystemExit("Missing local Metabase admin or BI reader credentials.")


def api(method, path, body=None, session=None, timeout=50):
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if session:
        headers["X-Metabase-Session"] = session
    request = Request(BASE + path, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(4_000_000)
            return json.loads(raw) if raw else None
    except HTTPError as exc:
        # Do not echo request bodies or server response bodies: may leak secrets.
        raise RuntimeError(
            f"Metabase API {method} {path.split('?')[0]} returned HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Metabase API unreachable on {BASE}.") from exc


def rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise RuntimeError("Unexpected Metabase collection/list response shape.")


def login():
    last = None
    for _ in range(80):
        try:
            health = api("GET", "/api/health", timeout=5)
            if health.get("status") == "ok":
                break
        except (RuntimeError, AttributeError) as err:
            last = err
        time.sleep(5)
    else:
        raise RuntimeError(f"Metabase health never became ready: {last}")
    settings = api("GET", "/api/session/properties")
    if settings.get("has-user-setup"):
        data = api("POST", "/api/session", {
            "username": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
        })
    else:
        token = settings.get("setup-token")
        if not token:
            raise RuntimeError("Metabase has no setup token and no initialized admin.")
        data = api("POST", "/api/setup", {
            "token": token,
            "user": {
                "first_name": "DocuMind", "last_name": "Local",
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
            },
            "prefs": {"site_name": "DocuMind D3 - donnees fictives", "site_locale": "fr"},
        })
    session = data.get("id") if isinstance(data, dict) else None
    if not session:
        raise RuntimeError("Metabase session not returned; setup is incomplete.")
    print("Metabase API authenticated (local admin).")
    return session


def database(session):
    existing = rows(api("GET", "/api/database", session=session))
    matches = [d for d in existing if d.get("name") == DATABASE_NAME]
    if matches:
        result = matches[0]
    else:
        result = api("POST", "/api/database", {
            "name": DATABASE_NAME,
            "engine": "postgres",
            "details": {
                "host": "postgres", "port": 5432, "dbname": "documind",
                "user": "documind_bi", "password": BI_PASSWORD, "ssl": False,
            },
            "is_full_sync": True, "is_on_demand": False,
        }, session=session)
    value = result.get("id")
    if not isinstance(value, int):
        raise RuntimeError("Metabase BI database ID absent.")
    print(f"Read-only BI database connected: id={value}")
    return value


def collection(session):
    found = rows(api("GET", "/api/collection", session=session))
    chosen = next((v for v in found if v.get("name") == COLLECTION_NAME), None)
    if not chosen:
        chosen = api("POST", "/api/collection", {
            "name": COLLECTION_NAME,
            "description": "Demo fictive. Questions fondees sur les vues SQL bi uniquement.",
        }, session=session)
    if not isinstance(chosen.get("id"), int):
        raise RuntimeError("Could not provision D3 collection.")
    return chosen["id"]


# SQL uses only governed BI views. All monetary KPIs are scoped to one currency.
CARDS = [
    {
        "name": "Factures acceptees",
        "display": "scalar", "tab": "Synthese",
        "sql": "SELECT COUNT(*) AS invoice_count FROM bi.validated_invoices",
        "layout": (0, 0, 6, 3),
    },
    {
        "name": "TTC valide - EUR",
        "display": "scalar", "tab": "Synthese",
        "sql": "SELECT COALESCE(SUM(total),0) AS total_eur FROM bi.validated_invoices WHERE currency = 'EUR'",
        "layout": (0, 6, 6, 3),
    },
    {
        "name": "Documents rejetes",
        "display": "scalar", "tab": "Synthese",
        "sql": "SELECT COUNT(*) AS rejected_documents FROM bi.document_quality WHERE document_state = 'REJECTED'",
        "layout": (0, 12, 6, 3),
    },
    {
        "name": "Taux de rejet (%)",
        "display": "scalar", "tab": "Synthese",
        "sql": (
            "SELECT COALESCE(ROUND(100.0 * COUNT(*) FILTER "
            "(WHERE document_state = 'REJECTED') / NULLIF(COUNT(*), 0), 1), 0) "
            "AS rejection_pct FROM bi.document_quality"
        ),
        "layout": (0, 18, 6, 3),
    },
    {
        "name": "Depenses TTC mensuelles - EUR",
        "display": "line", "tab": "Synthese",
        "sql": "SELECT month, total FROM bi.spending_monthly WHERE currency = 'EUR' ORDER BY month",
        "layout": (3, 0, 12, 7),
    },
    {
        "name": "TTC par fournisseur - EUR",
        "display": "bar", "tab": "Synthese",
        "sql": "SELECT supplier_name, total FROM bi.spending_suppliers WHERE currency = 'EUR' ORDER BY total DESC",
        "layout": (3, 12, 12, 7),
    },
    {
        "name": "Documents par etat",
        "display": "bar", "tab": "Synthese",
        "sql": (
            "SELECT document_state, SUM(document_count)::integer AS document_count "
            "FROM bi.document_status_counts GROUP BY document_state "
            "ORDER BY document_count DESC"
        ),
        "layout": (10, 0, 12, 5),
    },
    {
        "name": "Anomalies par regle",
        "display": "bar", "tab": "Synthese",
        "sql": (
            "SELECT issue_code, SUM(issue_count)::integer AS issue_count "
            "FROM bi.issue_code_counts GROUP BY issue_code ORDER BY issue_count DESC"
        ),
        "layout": (10, 12, 12, 5),
    },
    {
        "name": "Factures et sources",
        "display": "table", "tab": "Tracabilite",
        "sql": (
            "SELECT issued_on, supplier_name, invoice_number, currency, "
            "subtotal, tax, total, document_name, source_locator "
            "FROM bi.validated_invoices ORDER BY issued_on DESC, invoice_number"
        ),
        "layout": (0, 0, 24, 9),
    },
    {
        "name": "Documents et traitements",
        "display": "table", "tab": "Tracabilite",
        "sql": (
            "SELECT document_name, file_type, document_state, "
            "pipeline_version, run_status, issue_count "
            "FROM bi.document_quality ORDER BY document_name"
        ),
        "layout": (9, 0, 24, 7),
    },
    {
        "name": "Anomalies localisees",
        "display": "table", "tab": "Tracabilite",
        "sql": (
            "SELECT document_name, source_locator, issue_code, field_name, "
            "message FROM bi.quality_issues ORDER BY document_name, issue_code"
        ),
        "layout": (16, 0, 24, 7),
    },
    {
        "name": "Totaux par devise",
        "display": "table", "tab": "Tracabilite",
        "sql": (
            "SELECT currency, invoice_count, supplier_count, subtotal, tax, total "
            "FROM bi.currency_totals ORDER BY currency"
        ),
        "layout": (23, 0, 24, 5),
    },
]


def cards(session, database_id, collection_id):
    existing = rows(api("GET", "/api/card?f=all", session=session))
    result = {}
    for spec in CARDS:
        text = spec["sql"]
        if not text.strip().upper().startswith("SELECT ") or "bi." not in text:
            raise RuntimeError("Unsafe or unscoped SQL attempted in Metabase provisioning.")
        payload = {
            "name": spec["name"],
            "type": "question",
            "description": (
                "DocuMind D3 - simulation fictive, PostgreSQL schema bi. "
                "Rapprochement SQL / factures sources obligatoire."
            ),
            "collection_id": collection_id,
            "display": spec["display"],
            "visualization_settings": {},
            "dataset_query": {
                "database": database_id,
                "type": "native",
                "native": {"query": text, "template-tags": {}},
            },
        }
        previous = next(
            (c for c in existing
             if c.get("name") == spec["name"] and
                c.get("collection_id") == collection_id), None
        )
        if previous:
            card_id = previous["id"]
            api("PUT", f"/api/card/{card_id}", payload, session=session)
        else:
            created = api("POST", "/api/card", payload, session=session)
            card_id = created["id"]
        result[spec["name"]] = card_id
    print(f"Provisioned {len(result)} real SQL questions; no static cards.")
    return result


def dashboard(session, collection_id, card_ids):
    existing = rows(api("GET", "/api/dashboard", session=session))
    found = next(
        (d for d in existing
         if d.get("name") == DASHBOARD_NAME and
            d.get("collection_id") == collection_id), None
    )
    if not found:
        found = api("POST", "/api/dashboard", {
            "name": DASHBOARD_NAME,
            "description": "Donnees fictives | KPIs reconciles en SQL | aucune depense multidevise additionnee.",
            "collection_id": collection_id,
        }, session=session)
    dash_id = found["id"]
    current = api("GET", f"/api/dashboard/{dash_id}", session=session)
    existing_tabs = {t["name"]: t["id"] for t in current.get("tabs", [])}
    tabs = [
        {"id": existing_tabs.get("Synthese", -1), "name": "Synthese"},
        {"id": existing_tabs.get("Tracabilite", -2), "name": "Tracabilite"},
    ]
    existing_cards = {
        item["card_id"]: item
        for item in current.get("dashcards", [])
        if isinstance(item.get("card_id"), int)
    }
    managed_ids = set(card_ids.values())
    dashcards = []
    for index, spec in enumerate(CARDS, 1):
        card_id = card_ids[spec["name"]]
        prior = existing_cards.get(card_id)
        row, col, size_x, size_y = spec["layout"]
        dashcards.append({
            "id": prior["id"] if prior else -index,
            "card_id": card_id, "row": row, "col": col,
            "size_x": size_x, "size_y": size_y,
            "dashboard_tab_id": next(t["id"] for t in tabs if t["name"] == spec["tab"]),
            "parameter_mappings": [], "visualization_settings": {},
        })
    # Do not delete cards added manually by the user.
    for item in current.get("dashcards", []):
        if item.get("card_id") not in managed_ids:
            dashcards.append({
                k: item[k] for k in (
                    "id", "card_id", "row", "col", "size_x", "size_y",
                    "dashboard_tab_id", "parameter_mappings",
                    "visualization_settings",
                ) if k in item
            })
    api("PUT", f"/api/dashboard/{dash_id}", {
        "name": DASHBOARD_NAME,
        "tabs": tabs,
        "dashcards": dashcards,
    }, session=session)
    final = api("GET", f"/api/dashboard/{dash_id}", session=session)
    final_ids = {entry.get("card_id") for entry in final.get("dashcards", [])}
    missing = managed_ids - final_ids
    if missing:
        raise RuntimeError(f"{len(missing)} BI questions missing on dashboard.")
    print(f"Saved dashboard: http://127.0.0.1:3033/dashboard/{dash_id}")
    return dash_id


def verify(session, card_ids):
    for spec in CARDS:
        card_id = card_ids[spec["name"]]
        result = api("POST", f"/api/card/{card_id}/query", {}, session=session, timeout=90)
        if result.get("status") == "failed" or result.get("error"):
            raise RuntimeError(f"Metabase SQL query failed for {spec['name']}")
        data = result.get("data", {})
        if not isinstance(data.get("rows"), list):
            raise RuntimeError(f"No query rows available for {spec['name']}")
    # Explicitly check important fixture KPI queries are numeric and consistent.
    values = {}
    for name in ("Factures acceptees", "TTC valide - EUR", "Documents rejetes"):
        payload = api("POST", f"/api/card/{card_ids[name]}/query", {}, session=session)
        found_rows = payload["data"]["rows"]
        if len(found_rows) != 1 or len(found_rows[0]) != 1:
            raise RuntimeError(f"Invalid scalar shape for {name}")
        values[name] = found_rows[0][0]
    # These are minimums because the local database may also contain extra,
    # user-authorized uploads beyond the reproducible demo corpus.
    if values["Factures acceptees"] < 15 or float(values["TTC valide - EUR"]) < 1344:
        raise RuntimeError("Metabase aggregate misses the verified fictional corpus.")
    if values["Documents rejetes"] < 2:
        raise RuntimeError("Metabase rejected-document indicator missed the anomalies.")
    print(
        "D3 METABASE OK: dashboard + 12 live SQL questions; "
        f"accepted_invoices={values['Factures acceptees']}, "
        f"EUR_TTC={values['TTC valide - EUR']}, "
        f"rejected_documents={values['Documents rejetes']}"
    )


def main():
    session = login()
    db_id = database(session)
    collection_id = collection(session)
    card_ids = cards(session, db_id, collection_id)
    dashboard(session, collection_id, card_ids)
    verify(session, card_ids)


if __name__ == "__main__":
    main()
