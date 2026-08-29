Write-Host "Port-forwarding Kubernetes services for ecommerce-mlops (stack-ecommerce-mlops)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-ecommerce-mlops svc/postgres 5434:5432 &
kubectl port-forward -n stack-ecommerce-mlops svc/redis 6380:6379 &
kubectl port-forward -n stack-ecommerce-mlops svc/rabbitmq 15672:15672 &
