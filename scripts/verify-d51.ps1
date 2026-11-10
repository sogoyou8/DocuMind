# DocuMind D5.1 - Full post-review regression, Windows PowerShell 5.1 ASCII only.
# Runs D5 acceptance including the new D5.1 unit tests and visual E2E.
# Does not delete Docker volumes, deploy public services or merge branches.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "DOCUMIND D5.1 - FINAL UX/UI REGRESSION" -ForegroundColor Cyan
Write-Host "Targets: 1920x993, 1649x928, 1440x900, 390x844" -ForegroundColor Cyan
Write-Host "The complete D5 backend, D3 SQL and D4 local RAG regression will also run." -ForegroundColor Cyan

& (Join-Path $PSScriptRoot "verify-d5.ps1")
if ($LASTEXITCODE -ne 0) { throw "D5.1 acceptance failed. See output above." }

Write-Host "D5.1 LOCAL OK: full Django/SQL/RAG + TS/Vite/Vitest + responsive Playwright" -ForegroundColor Green
Write-Host "Review screenshots in frontend/test-results/ before PR merge." -ForegroundColor Yellow
Write-Host "Never run docker compose down -v (data volumes must be preserved)." -ForegroundColor Yellow
