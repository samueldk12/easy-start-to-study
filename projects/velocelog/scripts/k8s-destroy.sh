#!/bin/bash
echo "Deleting velocelog from Kubernetes (stack-velocelog)..."
kubectl delete -k k8s/
