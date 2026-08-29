#!/bin/bash
echo "Deleting devops-edge-stack from Kubernetes (stack-devops-edge-stack)..."
kubectl delete -k k8s/
