Write-Host "Deleting telemetry-governance-stack from Kubernetes (stack-telemetry-governance-stack)..." -ForegroundColor Yellow
kubectl delete -k k8s/
