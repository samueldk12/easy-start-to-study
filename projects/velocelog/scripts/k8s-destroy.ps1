Write-Host "Deleting velocelog from Kubernetes (stack-velocelog)..." -ForegroundColor Yellow
kubectl delete -k k8s/
