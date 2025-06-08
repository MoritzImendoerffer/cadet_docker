#!/bin/bash

set -e

CERT_DIR="certs"
KEY_FILE="$CERT_DIR/privkey.pem"
CERT_FILE="$CERT_DIR/fullchain.pem"

if [[ "$DEVELOP" != "true" ]]; then
  echo "Refusing to generate a development certificate because DEVELOP != true"
  echo "Set DEVELOP=true in your .env for local development"
  exit 1
fi

mkdir -p "$CERT_DIR"

echo "[DEVELOPMENT ONLY] Generating self-signed TLS certificate..."
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -subj "/C=DE/ST=Dev/L=Local/O=Dev/CN=localhost"

echo "TLS certs generated at: $CERT_DIR"
