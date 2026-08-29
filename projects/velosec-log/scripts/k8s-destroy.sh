#!/bin/bash
echo "Deleting velosec-log from Kubernetes (stack-velosec-log)..."
kubectl delete -k k8s/
