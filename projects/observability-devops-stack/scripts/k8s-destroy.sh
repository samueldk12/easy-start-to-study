#!/bin/bash
echo "Deleting observability-devops-stack from Kubernetes (stack-observability-devops-stack)..."
kubectl delete -k k8s/
