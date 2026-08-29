Write-Host "Port-forwarding Kubernetes services for fintech-backend-queue (stack-fintech-backend-queue)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-fintech-backend-queue svc/postgres 5434:5432 &
kubectl port-forward -n stack-fintech-backend-queue svc/redis 6380:6379 &
kubectl port-forward -n stack-fintech-backend-queue svc/rabbitmq 15672:15672 &
