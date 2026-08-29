#!/bin/bash
echo "Deploying graph-nosql-study to Kubernetes (stack-graph-nosql-study)..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n stack-graph-nosql-study -w
