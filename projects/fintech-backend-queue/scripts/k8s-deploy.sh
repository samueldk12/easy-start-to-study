#!/bin/bash
echo "Deploying fintech-backend-queue to Kubernetes (stack-fintech-backend-queue)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-fintech-backend-queue -w
