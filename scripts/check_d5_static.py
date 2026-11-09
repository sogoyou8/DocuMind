"""D5 source and security preflight. Python stdlib only, no browser required."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend = root / "backend"
frontend = root / "frontend"
if not backend.exists():
    backend = Path("/app")
if not frontend.exists():
    frontend = Path("/workspace/frontend")
if not (backend.exists() and frontend.exists()):
    raise SystemExit("DocuMind D5 source mounts unavailable.")

sources = [
    "documents/frontend_api.py",
    "documents/session_views.py",
    "documents/test_d5.py",
    "documents/management/commands/bootstrap_local_user.py",
    "documents/urls.py",
    "documents/api.py",
    "documind_api/settings.py",
]
for rel in sources:
    file = backend / rel
    ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

urls = (backend / "documents/urls.py").read_text(encoding="utf-8")
for route in ("session/", "session/login/", "session/logout/", "analytics/", "audit/"):
    if f'path("{route}"' not in urls:
        raise SystemExit(f"Missing first-party D5 endpoint: {route}")

session = (backend / "documents/session_views.py").read_text(encoding="utf-8")
for token in ("@csrf_protect", "if settings.DEMO_READONLY:", "authenticate("):
    if token not in session:
        raise SystemExit(f"D5 session guard missing: {token}")

analytics = (backend / "documents/frontend_api.py").read_text(encoding="utf-8")
for token in ("if settings.DEMO_READONLY:", "bi.currency_totals", "bi.spending_monthly",
              "bi.spending_suppliers", "bi.issue_code_counts", "bi.document_status_counts"):
    if token not in analytics:
        raise SystemExit(f"D5 real BI / demo guard missing: {token}")

types = (frontend / "src/types.ts").read_text(encoding="utf-8")
api = (frontend / "src/api.ts").read_text(encoding="utf-8")
for token in ("type DocumentDetail", "type AssistantAnswer", "type Analytics"):
    if token not in types:
        raise SystemExit(f"D5 frontend type contract missing: {token}")
for token in ("credentials: \"same-origin\"", "X-CSRFToken", "/api/v1/assistant/ask/",
              "/api/v1/analytics/", "/api/v1/session/"):
    if token not in api:
        raise SystemExit(f"D5 API client guard missing: {token}")

vite = (frontend / "vite.config.ts").read_text(encoding="utf-8")
if "changeOrigin: false" not in vite or 'allowedHosts: ["web"]' not in vite:
    raise SystemExit("D5 Vite proxy origin/host isolation missing.")

compose = (root / "compose.yaml").read_text(encoding="utf-8")
if not compose.exists():
    compose = (Path("/workspace/compose.yaml")).read_text(encoding="utf-8")
else:
    compose = compose.read_text(encoding="utf-8")
for token in ('profiles: ["ui"]', 'profiles: ["qa"]', 'profiles: ["ai"]',
              "127.0.0.1:5173:5173", "127.0.0.1:8001:8001"):
    if token not in compose:
        raise SystemExit(f"D5 Docker isolation missing: {token}")

render_path = root / "render.yaml"
if not render_path.exists():
    render_path = Path("/workspace/render.yaml")
render = render_path.read_text(encoding="utf-8")
if any(text in render.lower() for text in ("ollama", "chromadb", "metabase", "documind_ai_enabled")):
    raise SystemExit("Render must not host optional local AI and analytics.")

powershell = (root / "scripts/verify-d5.ps1")
if not powershell.exists():
    powershell = Path("/workspace/scripts/verify-d5.ps1")
if not powershell.read_text(encoding="utf-8").isascii():
    raise SystemExit("D5 PowerShell must be ASCII-only for Windows 5.1.")

print("D5 STATIC OK: Python AST, routes, CSRF, demo isolation, real SQL, typed frontend and Docker boundaries")
