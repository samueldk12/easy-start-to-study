Write-Host "Starting velocelog-lakehouse..." -ForegroundColor Cyan
docker compose up -d
Write-Host "Services started!" -ForegroundColor Green
docker compose ps
Write-Host "Running automated service health tests..." -ForegroundColor Yellow
python tests/test_services.py
