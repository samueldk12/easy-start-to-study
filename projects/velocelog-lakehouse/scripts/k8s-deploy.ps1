Write-Host "Deploying velocelog-lakehouse to Kubernetes (stack-velocelog-lakehouse)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-velocelog-lakehouse -w
