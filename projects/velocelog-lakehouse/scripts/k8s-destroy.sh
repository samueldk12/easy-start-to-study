#!/bin/bash
echo "Deleting velocelog-lakehouse from Kubernetes (stack-velocelog-lakehouse)..."
kubectl delete -k k8s/
