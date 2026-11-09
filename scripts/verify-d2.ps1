param(
    [switch]$SkipAirflow
)

# ASCII-only file: Windows PowerShell 5.1 may read UTF-8 without BOM as ANSI.
# UTF-8 em dash bytes can decode into a smart quote and break script parsing.
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
    Write-Host "D2 Airflow 3.4.0 - image locale et DAG" -ForegroundColor Cyan
    docker compose --profile pipeline build airflow
    if ($LASTEXITCODE -ne 0) { throw "Airflow image build failed" }

    # An earlier validation may have started Airflow before its metadata DB
    # was initialized. Stop it before migrating to avoid concurrent access.
    docker compose --profile pipeline stop airflow
    if ($LASTEXITCODE -ne 0) { throw "Airflow stop failed" }

    # Airflow 3 requires its own metadata schema; this is separate from the
    # DocuMind PostgreSQL migrations and uses its persistent local volume.
    # 'run' creates a temporary container but preserves the named state volume.
    docker compose --profile pipeline run --rm --no-deps airflow airflow db migrate
    if ($LASTEXITCODE -ne 0) { throw "Airflow metadata migration failed" }

    docker compose --profile pipeline run --rm --no-deps airflow airflow db check-migrations -t 60
    if ($LASTEXITCODE -ne 0) { throw "Airflow metadata migrations were not confirmed" }

    docker compose --profile pipeline up -d airflow
    if ($LASTEXITCODE -ne 0) { throw "Airflow local startup failed" }

    # The standalone server and DAG processor take time to start. In Windows
    # PowerShell 5.1, native stderr with ErrorActionPreference=Stop can be a
    # terminating NativeCommandError, so allow/capture stderr only in the poll.
    $ready = $false
    $lastDagOutput = ""
    for ($i = 0; $i -lt 40; $i++) {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $dagOutput = @(docker compose --profile pipeline exec -T airflow airflow dags list 2>&1)
            $dagExit = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previousPreference
        }
        $lastDagOutput = $dagOutput -join "`n"
        if ($dagExit -eq 0 -and $lastDagOutput.Contains("documind_d2_ingestion")) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 5
    }
    if (-not $ready) {
        throw "DAG not visible. Last CLI result: $lastDagOutput ; inspect docker compose --profile pipeline logs --tail=100 airflow"
    }

    # Execute the actual DAG task, not merely its parser.
    docker compose --profile pipeline exec -T airflow airflow dags test documind_d2_ingestion
    if ($LASTEXITCODE -ne 0) {
        throw "Airflow DAG execution failed"
    }
    Write-Host "Airflow UI (local): http://127.0.0.1:8088" -ForegroundColor Cyan
}

if ($SkipAirflow) {
    Write-Host "D2 CORE OK : Pandas/PDF/XLSX, PostgreSQL, quarantine et replays ; Airflow NON TESTE" -ForegroundColor Yellow
    Write-Host "Pour la recette complete, relancez sans -SkipAirflow." -ForegroundColor Yellow
} else {
    Write-Host "D2 LOCAL OK : extraction, normalisation, quarantine, replays et DAG Airflow" -ForegroundColor Green
}
