#!/bin/bash
echo "Deploying telemetry-governance-stack to Kubernetes (stack-telemetry-governance-stack)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-telemetry-governance-stack -w
