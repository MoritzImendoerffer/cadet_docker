#!/usr/bin/env bash
set -euo pipefail

echo "[dev_setup.sh] Loading environment..."
export DEVELOP=true

# NEW: guarantee keys & certs are ready
python "$(dirname "$0")/dev_setup.py"

# Export PEM content into env vars for docker compose
export PRIVATE_KEY_PEM=$(<~/.cadet_api/private_key.pem)
export PUBLIC_KEY_PEM=$(<~/.cadet_api/public_key.pem)

echo "[dev_setup.sh] Starting Docker Compose with HTTPS..."
docker compose -f docker-compose_ubuntu.yml up --build
