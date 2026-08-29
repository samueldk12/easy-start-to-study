Write-Host "Deploying velocelog to Kubernetes (stack-velocelog)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-velocelog -w
