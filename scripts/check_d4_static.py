"""D4 syntax and safety-contract preflight; no AI dependencies required."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend = root / "backend"
if not backend.exists():
    backend = Path("/app")
if not backend.exists():
    raise SystemExit("DocuMind D4 backend path unavailable.")

sources = [
    "documents/rag/__init__.py",
    "documents/rag/security.py",
    "documents/rag/sources.py",
    "documents/rag/ollama.py",
    "documents/rag/store.py",
    "documents/rag/indexer.py",
    "documents/rag/search.py",
    "documents/rag/graph.py",
    "documents/assistant_api.py",
    "documents/test_d4.py",
    "documents/management/commands/index_pending.py",
    "documents/management/commands/verify_d4.py",
    "documents/migrations/0004_chunk_references.py",
]
for rel in sources:
    file = backend / rel
    ast.parse(file.read_text(encoding="utf-8"), filename=str(file))

settings = (backend / "documind_api/settings.py").read_text(encoding="utf-8")
if 'and not DEMO_READONLY)' not in settings:
    raise SystemExit("AI switch lost forced read-only demo guard.")
if 'DOCUMIND_AI_ENABLED' not in settings:
    raise SystemExit("AI feature flag missing.")
source = (backend / "documents/rag/search.py").read_text(encoding="utf-8")
if "digest(passage) == ref.content_sha256" not in source:
    raise SystemExit("D4 search text integrity gate missing.")
if "doc.state == Document.State.INDEXED" not in source:
    raise SystemExit("D4 search accepted source gate missing.")
if "if hostile_instruction(passage)" not in source:
    raise SystemExit("Untrusted source instruction filter missing.")
compose = (root / "compose.yaml").read_text(encoding="utf-8")
if not all(v in compose for v in (
    'profiles: ["ai"]', '127.0.0.1:8001:8001',
    '127.0.0.1:11435:11434', "documind_chroma_state:",
)):
    raise SystemExit("D4 Compose must stay on private opt-in localhost ports.")
render = (root / "render.yaml").read_text(encoding="utf-8")
if "DOCUMIND_AI_ENABLED" in render or "ollama" in render.lower():
    raise SystemExit("Render must not load or deploy local AI.")
powershell = (root / "scripts/verify-d4.ps1").read_text(encoding="utf-8")
if not powershell.isascii():
    raise SystemExit("D4 PowerShell recipe must remain ASCII (Windows PS 5.1).")
print("D4 STATIC OK: Python syntax, local-only AI isolation, SQL provenance and source protection.")
