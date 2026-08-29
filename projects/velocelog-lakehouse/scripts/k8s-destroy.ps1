Write-Host "Deleting velocelog-lakehouse from Kubernetes (stack-velocelog-lakehouse)..." -ForegroundColor Yellow
kubectl delete -k k8s/
