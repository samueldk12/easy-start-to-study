Write-Host "Deploying graph-nosql-study to Kubernetes (stack-graph-nosql-study)..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n stack-graph-nosql-study -w
