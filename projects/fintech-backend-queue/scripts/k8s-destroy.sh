#!/bin/bash
echo "Deleting fintech-backend-queue from Kubernetes (stack-fintech-backend-queue)..."
kubectl delete -k k8s/
