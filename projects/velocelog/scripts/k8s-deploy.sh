#!/bin/bash
echo "Deploying velocelog to Kubernetes (stack-velocelog)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-velocelog -w
