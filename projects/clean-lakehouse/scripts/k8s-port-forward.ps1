Write-Host "Port-forwarding Kubernetes services for clean-lakehouse (stack-clean-lakehouse)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-clean-lakehouse svc/postgres 5434:5432 &
kubectl port-forward -n stack-clean-lakehouse svc/redis 6380:6379 &
kubectl port-forward -n stack-clean-lakehouse svc/rabbitmq 15672:15672 &
