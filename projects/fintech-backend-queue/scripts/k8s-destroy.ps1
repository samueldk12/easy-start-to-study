Write-Host "Deleting fintech-backend-queue from Kubernetes (stack-fintech-backend-queue)..." -ForegroundColor Yellow
kubectl delete -k k8s/
