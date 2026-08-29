Write-Host "Deploying fintech-backend-queue to Kubernetes (stack-fintech-backend-queue)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-fintech-backend-queue -w
