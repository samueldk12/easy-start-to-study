Write-Host "Port-forwarding Kubernetes services for devops-edge-stack (stack-devops-edge-stack)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-devops-edge-stack svc/postgres 5434:5432 &
kubectl port-forward -n stack-devops-edge-stack svc/redis 6380:6379 &
kubectl port-forward -n stack-devops-edge-stack svc/rabbitmq 15672:15672 &
