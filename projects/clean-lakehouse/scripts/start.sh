#!/bin/bash
echo "Starting clean-lakehouse..."
docker compose up -d
echo "Services started!"
docker compose ps
