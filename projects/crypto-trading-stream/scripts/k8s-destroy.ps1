Write-Host "Deleting crypto-trading-stream from Kubernetes (stack-crypto-trading-stream)..." -ForegroundColor Yellow
kubectl delete -k k8s/
