Write-Host "Deleting clean-lakehouse from Kubernetes (stack-clean-lakehouse)..." -ForegroundColor Yellow
kubectl delete -k k8s/
