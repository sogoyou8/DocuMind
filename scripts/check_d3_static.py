"""Dependency-free D3 source/safety preflight; does not replace PostgreSQL tests."""
import ast
from pathlib import Path
import re

script_dir = Path(__file__).resolve().parent
project = script_dir.parent
backend = project / "backend"
if not backend.is_dir():
    # In local Compose, scripts are mounted at /workspace/scripts, backend at /app.
    backend = Path("/app")
if not backend.is_dir():
    raise SystemExit("Unable to find DocuMind Django backend.")

source_files = [
    backend / "documents/bi/fixtures.py",
    backend / "documents/migrations/0003_bi_views.py",
    backend / "documents/management/commands/seed_d3.py",
    backend / "documents/management/commands/verify_d3.py",
    backend / "documents/management/commands/configure_bi_reader.py",
    backend / "documents/management/commands/verify_bi_reader.py",
    backend / "documents/test_d3.py",
    script_dir / "provision_metabase.py",
]
for source in source_files:
    ast.parse(source.read_text(encoding="utf-8"), filename=str(source))

sql = (backend / "documents/bi/views_v1.sql").read_text(encoding="utf-8")
expected_views = {
    "validated_invoices", "document_quality", "quality_issues",
    "spending_monthly", "spending_suppliers", "spending_formats",
    "currency_totals", "document_status_counts", "issue_code_counts",
}
actual_views = set(
    re.findall(r"CREATE OR REPLACE VIEW bi\.([a-z_]+)", sql, flags=re.I)
)
if actual_views != expected_views:
    raise SystemExit(f"Unexpected BI SQL views: {actual_views ^ expected_views}")

if "WHERE d.source = 'UPLOAD'" not in sql:
    raise SystemExit("BI views lost local source restriction.")
if "r.status = 'SUCCEEDED'" not in sql:
    raise SystemExit("Invoice BI view lost successful-run restriction.")
if "d.state IN ('ACCEPTED', 'INDEXED')" not in sql:
    raise SystemExit("Invoice BI view lost document acceptance restriction.")

migration = (backend / "documents/migrations/0003_bi_views.py").read_text()
if 'vendor != "postgresql"' not in migration:
    raise SystemExit("D3 migration must be a no-op on Render's SQLite.")
role = (
    backend / "documents/management/commands/configure_bi_reader.py"
).read_text()
if "GRANT SELECT ON ALL TABLES IN SCHEMA bi" not in role:
    raise SystemExit("The Metabase SQL reader lost its governed view grants.")

ps = (script_dir / "verify-d3.ps1").read_text(encoding="utf-8")
if not ps.isascii():
    raise SystemExit("PowerShell D3 recipe must remain ASCII for Windows PS 5.1.")

print("D3 STATIC OK: Python syntax, nine governed views, Render guard and reader grants")
