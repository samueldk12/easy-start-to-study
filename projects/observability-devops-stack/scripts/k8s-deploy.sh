#!/bin/bash
echo "Deploying observability-devops-stack to Kubernetes (stack-observability-devops-stack)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-observability-devops-stack -w
