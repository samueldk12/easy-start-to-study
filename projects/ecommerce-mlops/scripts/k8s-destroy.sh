#!/bin/bash
echo "Deleting ecommerce-mlops from Kubernetes (stack-ecommerce-mlops)..."
kubectl delete -k k8s/
