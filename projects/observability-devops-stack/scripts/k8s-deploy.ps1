Write-Host "Deploying observability-devops-stack to Kubernetes (stack-observability-devops-stack)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-observability-devops-stack -w
