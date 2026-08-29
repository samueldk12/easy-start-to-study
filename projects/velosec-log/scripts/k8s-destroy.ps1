Write-Host "Deleting velosec-log from Kubernetes (stack-velosec-log)..." -ForegroundColor Yellow
kubectl delete -k k8s/
