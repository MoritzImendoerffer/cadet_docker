# CADET API Settings System

The `SecretsSettings` class manages cryptographic keys for the CADET API. It supports two modes of operation:

## 1. File Mode (Production/Docker)

Keys are loaded from PEM files in the secrets directory:
- `run/secrets/private_key_server.pem` - Server private key
- `run/secrets/public_key_server.pem` - Server public key  
- `run/secrets/public_key_client_<client_id>.pem` - Client public keys

```bash
# Generate keys
python tests/generate_secrets.py run/secrets

# Keys are automatically loaded when running with Docker
docker compose up
```

## 2. Environment Mode (Testing/Development)

When files are not found, the system falls back to environment variables:
- `PRIVATE_KEY_SERVER` - Server private key PEM content
- `PUBLIC_KEY_SERVER` - Server public key PEM content
- `PUBLIC_KEY_CLIENT_<client_id>` - Client public key PEM content

```bash
# Set environment variables
export PRIVATE_KEY_SERVER="-----BEGIN PRIVATE KEY-----..."
export PUBLIC_KEY_SERVER="-----BEGIN PUBLIC KEY-----..."
export PUBLIC_KEY_CLIENT_acme="-----BEGIN PUBLIC KEY-----..."

# Run tests
pytest tests/test_simulate_endpoint.py
```

## How It Works

The `SecretsSettings` class:
1. First tries to load keys from files in the secrets directory
2. If files are not found AND `env_fallback=True`, checks environment variables
3. Raises an error if keys cannot be found in either location

## Usage in Code

```python
from app.settings import settings

# Access loaded keys
print(settings.private_key_pem)  # Server private key PEM string
print(settings.public_key_pem)   # Server public key PEM string
print(settings.client_keys)      # Dict of {client_id: public_key_pem}

# Load into cryptography objects
from app.config import load_private_key, load_public_key, load_client_keys

private_key = load_private_key()    # RSAPrivateKey object
public_key = load_public_key()      # RSAPublicKey object  
client_keys = load_client_keys()    # Dict of {client_id: RSAPublicKey}
```

## Design Principles

1. **Encapsulation**: All secret loading logic is contained in `SecretsSettings`
2. **No Magic Constants**: Environment variable names are internal to the class
3. **Fail Fast**: Raises clear errors if keys cannot be found
4. **Docker-First**: Designed for Docker secrets, with env vars as a fallback

## Troubleshooting

Run the diagnostic script to check your settings:
```bash
python test_settings.py
```

This will show:
- Which mode is being used (files vs environment)
- Which keys were successfully loaded
- Any errors in the configuration