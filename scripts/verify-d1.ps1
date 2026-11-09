$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "DocuMind D1 : build + PostgreSQL + tests" -ForegroundColor Cyan
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Docker Compose build/start failed" }

docker compose exec -T api python manage.py check
if ($LASTEXITCODE -ne 0) { throw "Django system check failed" }

docker compose exec -T api python manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) { throw "Migration drift detected" }

docker compose exec -T api python manage.py test documents -v 2
if ($LASTEXITCODE -ne 0) { throw "Django tests failed" }

# Fail on generator diagnostics too: --validate alone can exit 0 even when schema errors are reported.
docker compose exec -T api python manage.py spectacular --file /tmp/documind-openapi.yaml --validate --fail-on-warn
if ($LASTEXITCODE -ne 0) { throw "OpenAPI schema warnings/errors detected (D1 NOT validated)" }

$health = Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health/" -TimeoutSec 15
if ($health.status -ne "ok") { throw "Healthcheck failed" }

Write-Host "D1 LOCAL OK : health + tests + schema + PostgreSQL" -ForegroundColor Green
Write-Host "API : http://127.0.0.1:8000 ; do not run docker compose down -v" -ForegroundColor Yellow
