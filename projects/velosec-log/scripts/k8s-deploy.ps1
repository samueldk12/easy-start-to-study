Write-Host "Deploying velosec-log to Kubernetes (stack-velosec-log)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-velosec-log -w
