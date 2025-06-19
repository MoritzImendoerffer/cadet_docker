# Test vs Production Setup

## Production Mode (Docker)
- Keys are loaded from files in `/run/secrets/` (Docker secrets)
- `DOCKER_SECRETS=1` is set in `docker.env`
- No environment variables with PEM content
- Secure and follows Docker best practices

## Test Mode
- Keys are passed via environment variables
- `TEST_MODE=1` is set by test scripts
- `SecretsSettings` falls back to environment variables when files don't exist
- PEM formatting is preserved through environment variables

## Key Environment Variables

### Production
- `DOCKER_SECRETS=1` - Indicates running in Docker with mounted secrets

### Testing
- `TEST_MODE=1` - Indicates test environment
- `PRIVATE_KEY_SERVER` - Server private key PEM content
- `PUBLIC_KEY_SERVER` - Server public key PEM content
- `PUBLIC_KEY_CLIENT_<client_id>` - Client public key PEM content

## How It Works

1. **SecretsSettings** checks for keys in this order:
   - First: Files in the secrets directory
   - Second: Environment variables (if `env_fallback=True`)

2. **Tests** generate keys on the fly and pass them via environment variables

3. **Production** uses Docker secrets mounted as files

## Debugging

Run the diagnostic script to check PEM handling:
```bash
python test_pem_handling.py
```

This separation ensures:
- Tests are self-contained and don't need file system setup
- Production uses secure Docker secrets
- PEM formatting is preserved correctly
- Clear distinction between environments