#!/bin/bash
echo "Deploying crypto-trading-stream to Kubernetes (stack-crypto-trading-stream)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-crypto-trading-stream -w
