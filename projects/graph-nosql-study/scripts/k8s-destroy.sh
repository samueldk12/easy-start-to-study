#!/bin/bash
echo "Deleting graph-nosql-study from Kubernetes (stack-graph-nosql-study)..."
kubectl delete -k k8s/
