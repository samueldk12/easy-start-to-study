Write-Host "Deleting ecommerce-mlops from Kubernetes (stack-ecommerce-mlops)..." -ForegroundColor Yellow
kubectl delete -k k8s/
