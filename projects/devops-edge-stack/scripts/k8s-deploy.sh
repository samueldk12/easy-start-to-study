#!/bin/bash
echo "Deploying devops-edge-stack to Kubernetes (stack-devops-edge-stack)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-devops-edge-stack -w
