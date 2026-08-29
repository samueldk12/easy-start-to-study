Write-Host "Deploying clean-lakehouse to Kubernetes (stack-clean-lakehouse)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-clean-lakehouse -w
