"""Dependency-free syntax and repository structure check for D1."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = sorted((ROOT / "backend").rglob("*.py"))
REQUIRED = [
    "render.yaml", "compose.yaml", "backend/Dockerfile", "backend/requirements.txt",
    "backend/manage.py", "backend/documind_api/settings.py", "backend/documents/api.py",
    "backend/documents/models.py", "backend/documents/serializers.py",
    "backend/documents/migrations/0001_initial.py", "backend/documents/tests.py",
    "docs/DEPLOIEMENT-D0.1.md", "docs/ETAT-D1.md",
]

for rel in REQUIRED:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"Missing D1 file: {rel}")

if len(PYTHON_FILES) < 8:
    raise SystemExit("D1 Python module tree is incomplete")
for path in PYTHON_FILES:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
if "plan: free" not in blueprint:
    raise SystemExit("Render must use free plan")
if "\ndatabases:" in blueprint:
    raise SystemExit("Do not create expiring Render Postgres databases")
if 'DOCUMIND_DEMO_READONLY' not in blueprint:
    raise SystemExit("Public demo must be read-only")

print(f"D1 static syntax + structure OK: {len(PYTHON_FILES)} Python files")
