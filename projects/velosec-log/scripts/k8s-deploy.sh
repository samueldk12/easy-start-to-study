#!/bin/bash
echo "Deploying velosec-log to Kubernetes (stack-velosec-log)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-velosec-log -w
