#!/bin/bash
echo "Deploying ecommerce-mlops to Kubernetes (stack-ecommerce-mlops)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-ecommerce-mlops -w
