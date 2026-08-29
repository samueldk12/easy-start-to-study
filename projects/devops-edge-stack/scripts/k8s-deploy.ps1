Write-Host "Deploying devops-edge-stack to Kubernetes (stack-devops-edge-stack)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-devops-edge-stack -w
