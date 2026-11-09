param([switch]$SkipCoreTests)

# ASCII only for Windows PowerShell 5.1. Do not print passwords or source files.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "DOCUMIND D4 - Local RAG with Ollama, Chroma and LangGraph" -ForegroundColor Cyan

if (-not $SkipCoreTests) {
    # Runs Django, SQL/fixture and OpenAPI regressions on local PostgreSQL.
    & (Join-Path $PSScriptRoot "verify-d2.ps1") -SkipAirflow
    if (-not $?) { throw "Regression D1/D2/D3 failed" }
}

docker compose up -d postgres api
if ($LASTEXITCODE -ne 0) { throw "Core local services unavailable" }
docker compose exec -T api python /workspace/scripts/check_d4_static.py
if ($LASTEXITCODE -ne 0) { throw "D4 source/architecture preflight failed" }

docker compose exec -T api python manage.py seed_d3 --process
if ($LASTEXITCODE -ne 0) { throw "D3 synthetic source corpus unavailable" }
docker compose exec -T api python manage.py verify_d3
if ($LASTEXITCODE -ne 0) { throw "D3 analytical contract regression" }

# Optional heavy services are paused, not removed: keep their volumes.
docker compose --profile analytics stop metabase
if ($LASTEXITCODE -ne 0) { throw "Cannot pause local Metabase" }
docker compose --profile pipeline stop airflow
if ($LASTEXITCODE -ne 0) { throw "Cannot pause local Airflow" }

# No model cloud APIs: Ollama downloads models once into a persistent volume.
docker compose --profile ai up -d ollama
if ($LASTEXITCODE -ne 0) { throw "Ollama local startup failed" }

$ollamaReady = $false
for ($i = 0; $i -lt 35; $i++) {
    try {
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11435/api/tags" -TimeoutSec 5
        if ($null -ne $tags.models) {
            $ollamaReady = $true
            break
        }
    } catch {
        # Docker started but the local Ollama HTTP listener is still booting.
    }
    Start-Sleep -Seconds 3
}
if (-not $ollamaReady) {
    throw "Ollama local HTTP endpoint unavailable. Inspect docker compose --profile ai logs --tail=80 ollama"
}

Write-Host "Installing local embedding model (one-time download)..." -ForegroundColor Cyan
docker compose --profile ai exec -T ollama ollama pull nomic-embed-text
if ($LASTEXITCODE -ne 0) { throw "Embedding model nomic-embed-text unavailable" }

Write-Host "Installing compact local text model (one-time download)..." -ForegroundColor Cyan
docker compose --profile ai exec -T ollama ollama pull qwen2.5:1.5b
if ($LASTEXITCODE -ne 0) { throw "Chat model qwen2.5:1.5b unavailable" }

docker compose --profile ai build rag
if ($LASTEXITCODE -ne 0) { throw "RAG dependency image build failed" }
docker compose --profile ai up -d rag
if ($LASTEXITCODE -ne 0) { throw "Django local RAG instance unavailable" }

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/health/" -TimeoutSec 6
        if ($health.status -eq "ok") { $ready = $true; break }
    } catch {
        # First launch waits for migrations / server startup.
    }
    Start-Sleep -Seconds 4
}
if (-not $ready) {
    throw "D4 healthcheck failed. Use docker compose --profile ai logs --tail=100 rag"
}

# This suite runs D4 offline fakes plus D1/D2/D3 regressions, in the full
# image containing ChromaDB and LangGraph. No live LLM calls in unit tests.
docker compose --profile ai exec -T rag python manage.py test documents -v 2
if ($LASTEXITCODE -ne 0) { throw "D4 Django security and provenance tests failed" }
docker compose --profile ai exec -T rag python manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) { throw "D4 Django migration drift detected" }
docker compose --profile ai exec -T rag python manage.py spectacular --file /tmp/documind-d4-openapi.yaml --validate --fail-on-warn
if ($LASTEXITCODE -ne 0) { throw "D4 OpenAPI invalid" }

# Real model and Chroma tests, intentionally separate from mocked unit tests.
docker compose --profile ai exec -T rag python manage.py index_pending --limit 20
if ($LASTEXITCODE -ne 0) { throw "D4 vector indexing failed" }
docker compose --profile ai exec -T rag python manage.py verify_d4
if ($LASTEXITCODE -ne 0) { throw "D4 cited RAG answer or abstention failed" }

docker compose exec -T api python manage.py verify_d3
if ($LASTEXITCODE -ne 0) { throw "D4 changed D3 financial indicators" }

Write-Host "D4 LOCAL OK: real local Ollama, Chroma citations, LangGraph, injection, abstention, SQL and API tests" -ForegroundColor Green
Write-Host "Local RAG API: http://127.0.0.1:8001/api/v1/assistant/status/" -ForegroundColor Cyan
Write-Host "Ollama and Chroma data are private to Docker volumes. Never run docker compose down -v." -ForegroundColor Yellow
