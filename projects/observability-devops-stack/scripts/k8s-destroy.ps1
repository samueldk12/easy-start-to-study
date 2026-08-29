Write-Host "Deleting observability-devops-stack from Kubernetes (stack-observability-devops-stack)..." -ForegroundColor Yellow
kubectl delete -k k8s/
