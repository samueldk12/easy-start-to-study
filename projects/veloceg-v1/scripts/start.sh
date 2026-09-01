#!/bin/bash
echo "Starting veloceg-v1..."
docker compose up -d
echo "Services started!"
docker compose ps
echo "Running automated service health tests..."
python tests/test_services.py
