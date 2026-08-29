Write-Host "Port-forwarding Kubernetes services for velosec-log (stack-velosec-log)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-velosec-log svc/postgres 5434:5432 &
kubectl port-forward -n stack-velosec-log svc/redis 6380:6379 &
kubectl port-forward -n stack-velosec-log svc/rabbitmq 15672:15672 &
