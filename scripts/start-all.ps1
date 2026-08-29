Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Starting Event-Driven Lakehouse Local Environment..." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

docker compose up -d

Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Checking service statuses:" -ForegroundColor Cyan
docker compose ps

Write-Host "Registering Debezium PostgreSQL CDC Connector..." -ForegroundColor Yellow
& "$PSScriptRoot\register-connector.ps1"

Write-Host "======================================================" -ForegroundColor Green
Write-Host " Environment ready!" -ForegroundColor Green
Write-Host " - Postgres (OLTP): localhost:5432" -ForegroundColor White
Write-Host " - Kafka: localhost:9092" -ForegroundColor White
Write-Host " - Schema Registry: http://localhost:8081" -ForegroundColor White
Write-Host " - Kafka Connect (Debezium): http://localhost:8083" -ForegroundColor White
Write-Host " - MinIO Console: http://localhost:9001 (admin / password123)" -ForegroundColor White
Write-Host " - Iceberg REST Catalog: http://localhost:8181" -ForegroundColor White
Write-Host " - Spark Master UI: http://localhost:8080" -ForegroundColor White
Write-Host " - Trino UI: http://localhost:8085" -ForegroundColor White
Write-Host " - Airflow Webserver: http://localhost:8088 (admin / admin)" -ForegroundColor White
Write-Host "======================================================" -ForegroundColor Green
