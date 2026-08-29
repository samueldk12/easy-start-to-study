#!/bin/bash
echo "Deleting telemetry-governance-stack from Kubernetes (stack-telemetry-governance-stack)..."
kubectl delete -k k8s/
