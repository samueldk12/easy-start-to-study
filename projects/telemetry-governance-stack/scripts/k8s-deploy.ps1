Write-Host "Deploying telemetry-governance-stack to Kubernetes (stack-telemetry-governance-stack)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-telemetry-governance-stack -w
