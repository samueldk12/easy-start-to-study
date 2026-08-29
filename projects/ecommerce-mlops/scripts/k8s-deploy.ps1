Write-Host "Deploying ecommerce-mlops to Kubernetes (stack-ecommerce-mlops)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-ecommerce-mlops -w
