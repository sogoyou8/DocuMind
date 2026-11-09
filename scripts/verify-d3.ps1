param(
    [switch]$SkipCoreTests
)

# ASCII-only for Windows PowerShell 5.1 compatibility.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "DOCUMIND D3 - SQL/Metabase local integration" -ForegroundColor Cyan
if (-not $SkipCoreTests) {
    & (Join-Path $PSScriptRoot "verify-d2.ps1") -SkipAirflow
    if (-not $?) { throw "Regression tests D1/D2/D3 failed" }
}

# Never use down -v: preserve the existing PostgreSQL and Airflow volumes.
docker compose up -d postgres api
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL or Django API unavailable" }

docker compose exec -T api python manage.py seed_d3 --process
if ($LASTEXITCODE -ne 0) { throw "D3 multi-period synthetic seed failed" }

# Re-run the seed: there must be zero duplicated financial rows.
docker compose exec -T api python manage.py seed_d3 --process
if ($LASTEXITCODE -ne 0) { throw "D3 idempotence replay failed" }

docker compose exec -T api python manage.py verify_d3
if ($LASTEXITCODE -ne 0) { throw "D3 independent SQL/ORM reconciliation failed" }

# Generate two strong local secrets once. They live only in a gitignored path.
$localFolder = Join-Path (Get-Location) "data/local"
New-Item -ItemType Directory -Force -Path $localFolder | Out-Null
$secretsFile = Join-Path $localFolder "d3-metabase-secrets.json"

function New-LocalSecret {
    $bytes = New-Object byte[] 40
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([Convert]::ToBase64String($bytes).TrimEnd('=') -replace '\+', '-' -replace '/', '_')
}

if (-not (Test-Path -LiteralPath $secretsFile)) {
    $newSecrets = [ordered]@{
        admin_email = "admin@documind.local"
        admin_password = New-LocalSecret
        bi_password = New-LocalSecret
    }
    $newSecrets | ConvertTo-Json | Set-Content -LiteralPath $secretsFile -Encoding Ascii
    Write-Host "Created private local BI credentials (excluded from Git)." -ForegroundColor Cyan
}

$localSecrets = Get-Content -LiteralPath $secretsFile -Raw | ConvertFrom-Json
if (-not $localSecrets.admin_password -or -not $localSecrets.bi_password) {
    throw "Incomplete local BI credentials. Check data/local/d3-metabase-secrets.json"
}

$biPassword = [string]$localSecrets.bi_password
$adminPassword = [string]$localSecrets.admin_password

docker compose exec -T -e "DOCUMIND_BI_PASSWORD=$biPassword" api python manage.py configure_bi_reader
if ($LASTEXITCODE -ne 0) { throw "BI read-only SQL role configuration failed" }

docker compose exec -T -e "DOCUMIND_BI_PASSWORD=$biPassword" api python manage.py verify_bi_reader
if ($LASTEXITCODE -ne 0) { throw "BI SQL permissions verification failed" }

# Metabase is isolated in the optional local analytics profile. Not Render.
docker compose --profile analytics up -d metabase
if ($LASTEXITCODE -ne 0) { throw "Local Metabase container startup failed" }

$healthy = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:3033/api/health" -TimeoutSec 7
        if ($res.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        # Metabase can be unavailable during JVM + application DB startup.
    }
    Start-Sleep -Seconds 5
}
if (-not $healthy) {
    throw "Metabase healthcheck unavailable. Inspect docker compose --profile analytics logs --tail=100 metabase"
}
Write-Host "Metabase API health OK." -ForegroundColor Green

# HTTP API provisioning and verification are done inside the private Compose
# network. Passwords are only in environment variables for these invocations.
docker compose exec -T -e "DOCUMIND_BI_PASSWORD=$biPassword" -e "DOCUMIND_METABASE_ADMIN_PASSWORD=$adminPassword" api python /workspace/scripts/provision_metabase.py
if ($LASTEXITCODE -ne 0) { throw "Metabase BI dashboard provisioning or query verification failed" }

Write-Host "D3 LOCAL OK: SQL views, fiscal metrics, read-only account and Metabase dashboard" -ForegroundColor Green
Write-Host "Metabase: http://127.0.0.1:3033" -ForegroundColor Cyan
Write-Host "Account email: admin@documind.local" -ForegroundColor Cyan
Write-Host "Private password file: data/local/d3-metabase-secrets.json (never commit/share it)" -ForegroundColor Yellow
