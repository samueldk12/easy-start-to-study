Write-Host "Port-forwarding Kubernetes services for graph-nosql-study (stack-graph-nosql-study)..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n stack-graph-nosql-study svc/postgres 5434:5432 &
kubectl port-forward -n stack-graph-nosql-study svc/redis 6380:6379 &
kubectl port-forward -n stack-graph-nosql-study svc/rabbitmq 15672:15672 &
