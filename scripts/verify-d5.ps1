param([switch]$SkipBrowser)

# DocuMind D5 V1: full local acceptance; Windows PowerShell 5.1 ASCII only.
# Uses Docker Desktop. Never destroys volumes, resets other user accounts,
# or exposes the local SQL/AI services to the Internet.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-Location (Join-Path $PSScriptRoot "..")

function Assert-Code([string]$step) {
    if ($LASTEXITCODE -ne 0) { throw "$step failed (exit=$LASTEXITCODE)" }
}

Write-Host "DOCUMIND D5 - React/Vite V1 cockpit + Django + SQL + local RAG" -ForegroundColor Cyan

docker compose --profile ai --profile ui --profile qa config --quiet
Assert-Code "Docker Compose D5 config"

# Reuse the free Ollama models/Chroma/PostgreSQL volumes from D4.
# Metabase and Airflow are paused for RAM only (never removed).
docker compose --profile analytics stop metabase
Assert-Code "Pause Metabase"
docker compose --profile pipeline stop airflow
Assert-Code "Pause Airflow"

docker compose --profile ai --profile ui up -d --build postgres api ollama rag web
Assert-Code "Start D5 backend and local React"

# D5.1: Docker 'up -d' keeps a previously running Vite process alive.
# After switching Git branches this may serve the old frontend modules even
# though TypeScript and Vite build the new sources successfully.
# Only the Vite dependency cache is reset; never delete database/vector volumes.
docker compose --profile ui exec -T web sh -c "rm -rf /app/node_modules/.vite"
Assert-Code "Clear disposable Vite optimized-module cache"
docker compose --profile ui restart web
Assert-Code "Restart Vite so Chromium sees the checked-out branch"

docker compose exec -T api python /workspace/scripts/check_d5_static.py
Assert-Code "Static D5 and security preflight"

docker compose --profile ai exec -T rag python manage.py check
Assert-Code "Django system checks"
docker compose --profile ai exec -T rag python manage.py makemigrations --check --dry-run
Assert-Code "Django migration drift"
docker compose --profile ai exec -T rag python manage.py spectacular --file /tmp/documind-v1-openapi.yaml --validate --fail-on-warn
Assert-Code "D5 OpenAPI schema"

docker compose --profile ai exec -T rag python manage.py test documents -v 2
Assert-Code "All Django D1-D5 unit and integration tests"

docker compose --profile ai exec -T rag python manage.py seed_d3 --process
Assert-Code "Seed real synthetic local D3 files"
docker compose --profile ai exec -T rag python manage.py verify_d3
Assert-Code "Reconcile D3 SQL and real source fixture"
docker compose --profile ai exec -T rag python manage.py index_pending --limit 20
Assert-Code "D4 Chroma embedding process"
docker compose --profile ai exec -T rag python manage.py verify_d4
Assert-Code "D4 real Ollama/Chroma/LangGraph grounding"

$privateDir = Join-Path (Get-Location) "data/local"
New-Item -ItemType Directory -Force -Path $privateDir | Out-Null
$credentialFile = Join-Path $privateDir "d5-operator.json"

function New-PrivatePassword {
    $bytes = New-Object byte[] 40
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ("D5x9_" + ([Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+', '-' -replace '/', '_'))
}

if (-not (Test-Path -LiteralPath $credentialFile)) {
    $localAccount = [ordered]@{
        username = "documind-local"
        password = New-PrivatePassword
    }
    $localAccount | ConvertTo-Json | Set-Content -LiteralPath $credentialFile -Encoding Ascii
    Write-Host "Created private local UI account credentials under data/local (Git ignored)." -ForegroundColor Cyan
}
$localAccount = Get-Content -LiteralPath $credentialFile -Raw | ConvertFrom-Json
if ($localAccount.username -ne "documind-local" -or
    [string]::IsNullOrWhiteSpace($localAccount.password) -or
    $localAccount.password.Length -lt 24) {
    throw "Invalid private D5 credentials. Check data/local/d5-operator.json"
}

# Only the dedicated local demo operator account is provisioned/reset.
$env:DOCUMIND_E2E_PASSWORD = [string]$localAccount.password
try {
    docker compose --profile ai exec -T -e "DOCUMIND_LOCAL_PASSWORD=$env:DOCUMIND_E2E_PASSWORD" rag python manage.py bootstrap_local_user --reset-password
    Assert-Code "D5 local operator account"

    $apiReady = $false
    for ($i = 0; $i -lt 35; $i++) {
        try {
            $state = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/health/" -TimeoutSec 6
            if ($state.status -eq "ok") { $apiReady = $true; break }
        } catch {
            # A cold Docker start may still be migrating and warming up.
        }
        Start-Sleep -Seconds 4
    }
    if (-not $apiReady) { throw "D5 Django RAG HTTP healthcheck unavailable" }
    Write-Host "Local PostgreSQL-backed Django API: HTTP health OK" -ForegroundColor Green

    $uiReady = $false
    for ($i = 0; $i -lt 90; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 6
            if ($response.StatusCode -eq 200 -and $response.Content -like "*DocuMind*") {
                $uiReady = $true
                break
            }
        } catch {
            # npm install on the first run may take longer.
        }
        Start-Sleep -Seconds 4
    }
    if (-not $uiReady) {
        throw "Vite UI not ready. Inspect docker compose --profile ui logs --tail=120 web"
    }
    Write-Host "DocuMind React UI: HTTP 200" -ForegroundColor Green

    docker compose --profile ui exec -T web npm run typecheck
    Assert-Code "React TypeScript strict typecheck"
    docker compose --profile ui exec -T web npm run build
    Assert-Code "React Vite production build"
    docker compose --profile ui exec -T web npm test
    Assert-Code "Frontend Vitest contracts"

    if (-not $SkipBrowser) {
        # Browser image includes real Chromium. The password is passed
        # transiently by environment, not printed or committed.
        docker compose --profile ai --profile ui --profile qa run --rm ui-e2e
        Assert-Code "Playwright public/mobile and real local SQL/RAG journeys"
    }

    docker compose --profile ai exec -T rag python manage.py verify_d3
    Assert-Code "Final D3 SQL reconciliation after D5 browser tests"

    Write-Host "D5 LOCAL OK: Django, SQL, local login, React build, Vitest, Ollama, Chroma and E2E" -ForegroundColor Green
    Write-Host "Open local workspace: http://127.0.0.1:5173" -ForegroundColor Cyan
    Write-Host "Login: documind-local" -ForegroundColor Cyan
    Write-Host "Private password: data/local/d5-operator.json (never share or commit)" -ForegroundColor Yellow
    Write-Host "Browser screenshots: frontend/test-results/ and frontend/playwright-report/" -ForegroundColor Cyan
    Write-Host "Do not run docker compose down -v. Docker volumes contain local data." -ForegroundColor Yellow
} finally {
    Remove-Item Env:DOCUMIND_E2E_PASSWORD -ErrorAction SilentlyContinue
}
