Write-Host "Deploying crypto-trading-stream to Kubernetes (stack-crypto-trading-stream)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-crypto-trading-stream -w
