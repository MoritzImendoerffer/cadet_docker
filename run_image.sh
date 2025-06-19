#!/bin/bash

set -e  # Exit on error

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo "docker compose not found. Please install Docker Compose."
    exit 1
fi

# Generate secrets if needed
if [ ! -f "run/secrets/private_key_server.pem" ]; then
    echo "Generating secrets..."
    python tests/generate_secrets.py run/secrets
else
    echo "Secrets already exist"
fi

# Build the container
echo -e "Building container..."
docker compose build

# Stop any existing container
echo -e "Stopping any existing containers..."
docker compose down

# Start the container
echo -e "Starting container..."
docker compose up -d

# Wait a moment for startup
echo -e "Waiting for container to start..."
sleep 3

# Check container status
echo -e "Container status:"
docker compose ps