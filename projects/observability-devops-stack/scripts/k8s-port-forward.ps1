Write-Host "Port-forwarding Kubernetes services for observability-devops-stack (stack-observability-devops-stack)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-observability-devops-stack svc/postgres 5434:5432 &
kubectl port-forward -n stack-observability-devops-stack svc/redis 6380:6379 &
kubectl port-forward -n stack-observability-devops-stack svc/rabbitmq 15672:15672 &
