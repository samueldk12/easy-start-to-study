#!/bin/bash
echo "Deploying velocelog-lakehouse to Kubernetes (stack-velocelog-lakehouse)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-velocelog-lakehouse -w
