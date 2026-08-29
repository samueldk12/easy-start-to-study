Write-Host "Deleting devops-edge-stack from Kubernetes (stack-devops-edge-stack)..." -ForegroundColor Yellow
kubectl delete -k k8s/
