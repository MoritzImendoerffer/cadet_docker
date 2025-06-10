#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.yml"

if [ "$1" != "" ]; then
  COMPOSE_FILE="$1"
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Error: Compose file '$COMPOSE_FILE' not found!"
  exit 1
fi

echo "Building Docker images using $COMPOSE_FILE..."

docker-compose -f "$COMPOSE_FILE" build

echo "✅ Build complete."
