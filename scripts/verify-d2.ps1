param(
    [switch]$SkipAirflow
)

$ErrorActionPreference = "Stop"
$projectRoot = Join-Path $PSScriptRoot ".."
Set-Location $projectRoot
Write-Host "DOCUMIND D2 : validation du pipeline local Django + Pandas + Airflow" -ForegroundColor Cyan

# D1 script now also executes D2 tests with the real local PostgreSQL database.
& (Join-Path $PSScriptRoot "verify-d1.ps1")
if (-not $?) { throw "D1/D2 Django validation failed" }

# This command creates only fictional local documents and no hosted service.
docker compose exec -T api python manage.py seed_d2 --process
if ($LASTEXITCODE -ne 0) { throw "D2 synthetic corpus or processing failed" }

# A replay of the same corpus must NOT duplicate invoice, run or amount.
docker compose exec -T api python manage.py seed_d2 --process
if ($LASTEXITCODE -ne 0) { throw "D2 idempotent replay failed" }

docker compose exec -T api python manage.py verify_d2
if ($LASTEXITCODE -ne 0) { throw "D2 SQL integrity and amount verification failed" }

docker compose exec -T api python manage.py process_pending --limit 20
if ($LASTEXITCODE -ne 0) { throw "D2 batch worker failed" }

if (-not $SkipAirflow) {
    Write-Host "D2 Airflow 3.4.0 — image locale et DAG" -ForegroundColor Cyan
    docker compose --profile pipeline build airflow
    if ($LASTEXITCODE -ne 0) { throw "Airflow image build failed" }

    docker compose --profile pipeline up -d airflow
    if ($LASTEXITCODE -ne 0) { throw "Airflow local startup failed" }

    # Airflow standalone initializes its own metadata DB on first launch.
    $ready = $false
    for ($i = 0; $i -lt 25; $i++) {
        $output = docker compose --profile pipeline exec -T airflow airflow dags list 2>&1
        if ($LASTEXITCODE -eq 0 -and ($output -join "`n").Contains("documind_d2_ingestion")) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 5
    }
    if (-not $ready) {
        throw "DAG not visible. Inspect: docker compose --profile pipeline logs --tail=100 airflow"
    }

    # Execute the actual DAG task, not merely its parser.
    docker compose --profile pipeline exec -T airflow airflow dags test documind_d2_ingestion
    if ($LASTEXITCODE -ne 0) {
        throw "Airflow DAG execution failed"
    }
    Write-Host "Airflow UI (local): http://127.0.0.1:8088" -ForegroundColor Cyan
}

Write-Host "D2 LOCAL OK : extraction, normalisation, quarantine, replays et Airflow" -ForegroundColor Green
if ($SkipAirflow) {
    Write-Host "Airflow was skipped: rerun without -SkipAirflow before claiming complete D2." -ForegroundColor Yellow
}
