Write-Host "Port-forwarding Kubernetes services for crypto-trading-stream (stack-crypto-trading-stream)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-crypto-trading-stream svc/postgres 5434:5432 &
kubectl port-forward -n stack-crypto-trading-stream svc/redis 6380:6379 &
kubectl port-forward -n stack-crypto-trading-stream svc/rabbitmq 15672:15672 &
