#!/bin/bash
echo "Deleting crypto-trading-stream from Kubernetes (stack-crypto-trading-stream)..."
kubectl delete -k k8s/
