$ConnectUrl = "http://localhost:8083"
$ConfigFile = Join-Path $PSScriptRoot "..\debeziumegister-postgres.json"
Write-Host "Registering Debezium Connector..." -ForegroundColor Cyan
$jsonBody = Get-Content -Raw -Path $ConfigFile
Invoke-RestMethod -Uri "$ConnectUrl/connectors" -Method Post -Body $jsonBody -ContentType "application/json"
Write-Host "Connector registered!" -ForegroundColor Green
