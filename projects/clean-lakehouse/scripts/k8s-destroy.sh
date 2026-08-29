#!/bin/bash
echo "Deleting clean-lakehouse from Kubernetes (stack-clean-lakehouse)..."
kubectl delete -k k8s/
