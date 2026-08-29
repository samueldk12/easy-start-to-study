#!/bin/bash
echo "Deploying clean-lakehouse to Kubernetes (stack-clean-lakehouse)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-clean-lakehouse -w
