# Public smoke check of the FREE Render demo. No account, secrets or private documents.
param(
    [string]$BaseUrl = "https://documind-d1-api-htpg.onrender.com"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$BaseUrl = $BaseUrl.TrimEnd('/')

Write-Host "DocuMind D1 Render smoke test (lecture seule)" -ForegroundColor Cyan
Write-Host "Cible : $BaseUrl" -ForegroundColor Cyan

$paths = @(
    "/",
    "/api/v1/health/",
    "/api/v1/documents/",
    "/api/v1/overview/",
    "/api/v1/schema/",
    "/api/v1/docs/"
)
foreach ($path in $paths) {
    $response = Invoke-WebRequest -Uri ($BaseUrl + $path) -Method Get -UseBasicParsing -TimeoutSec 120
    if ([int]$response.StatusCode -ne 200) {
        throw "GET $path : attendu HTTP 200, obtenu $($response.StatusCode)"
    }
    Write-Host "GET $path : HTTP 200" -ForegroundColor Green
}

$health = Invoke-RestMethod -Uri ($BaseUrl + "/api/v1/health/") -TimeoutSec 120
if ($health.status -ne "ok") { throw "Healthcheck: status != ok" }

$documents = Invoke-RestMethod -Uri ($BaseUrl + "/api/v1/documents/") -TimeoutSec 120
if (@($documents.results).Count -ne 3) {
    throw "La démo doit exposer exactement 3 fiches synthétiques au premier démarrage."
}
if (@($documents.results | Where-Object { $_.source -ne "DEMO" }).Count -ne 0) {
    throw "Une fiche non synthétique a été exposée dans la démo publique."
}

$overview = Invoke-RestMethod -Uri ($BaseUrl + "/api/v1/overview/") -TimeoutSec 120
if ($overview.mode -ne "synthetic-demo" -or $overview.total -ne 3 -or
    $overview.ai_enabled -ne $false -or $overview.airflow_enabled -ne $false) {
    throw "Indicateurs D1 incohérents avec le mode synthétique."
}
Write-Host "Fiches fictives + indicateurs D1 : OK" -ForegroundColor Green

# A POST without authentication must be refused without storing any file.
$postStatus = $null
try {
    $result = Invoke-WebRequest -Uri ($BaseUrl + "/api/v1/documents/") -Method Post -UseBasicParsing -ContentType "application/json" -Body '{"probe":"readonly-only"}' -TimeoutSec 120
    $postStatus = [int]$result.StatusCode
}
catch {
    if ($null -eq $_.Exception.Response) {
        throw "POST public: erreur réseau sans réponse HTTP : $_"
    }
    $postStatus = [int]$_.Exception.Response.StatusCode
}
if ($postStatus -ne 403) {
    throw "POST public : attendu HTTP 403, obtenu $postStatus"
}
Write-Host "POST /api/v1/documents/ : HTTP 403 (écriture interdite)" -ForegroundColor Green

Write-Host "D1 RENDER OK : routes, santé, démo 100% synthétique et sécurité en lecture seule" -ForegroundColor Green
