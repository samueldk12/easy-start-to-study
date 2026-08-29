$ConnectUrl = "http://localhost:8083"
$ConfigFile = Join-Path $PSScriptRoot "..\debezium\register-postgres.json"

Write-Host "Checking Kafka Connect status at $ConnectUrl..." -ForegroundColor Cyan
while ($true) {
    try {
        $response = Invoke-RestMethod -Uri "$ConnectUrl/connectors" -Method Get -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Kafka Connect is ready!" -ForegroundColor Green
        break
    }
    catch {
        Write-Host "Waiting for Kafka Connect to become available (5s)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

Write-Host "Registering Debezium PostgreSQL CDC Connector..." -ForegroundColor Cyan
$jsonBody = Get-Content -Raw -Path $ConfigFile

try {
    $result = Invoke-RestMethod -Uri "$ConnectUrl/connectors" -Method Post -Body $jsonBody -ContentType "application/json"
    Write-Host "Connector registered successfully!" -ForegroundColor Green
    $result | ConvertTo-Json -Depth 5
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 409) {
        Write-Host "Connector already registered. Updating config..." -ForegroundColor Yellow
        $parsed = $jsonBody | ConvertFrom-Json
        $updateResult = Invoke-RestMethod -Uri "$ConnectUrl/connectors/postgres-cdc-connector/config" -Method Put -Body ($parsed.config | ConvertTo-Json) -ContentType "application/json"
        Write-Host "Connector config updated successfully." -ForegroundColor Green
    }
    else {
        Write-Host "Error registering connector: $_" -ForegroundColor Red
    }
}

Start-Sleep -Seconds 3
Write-Host "Current Connector Status:" -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "$ConnectUrl/connectors/postgres-cdc-connector/status" -Method Get
    $status | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "Could not fetch status: $_" -ForegroundColor Yellow
}
