# Container Testing Guide

## Quick Start

```bash
# Automated setup and test
chmod +x test_container_setup.sh
./test_container_setup.sh
```

## Manual Steps

### 1. Generate Secrets (if needed)
```bash
python tests/generate_secrets.py run/secrets
```

### 2. Build and Start Container
```bash
docker compose build
docker compose up -d
```

### 3. Run Tests
```bash
# Test against running container
python tests/test_running_container.py

# Or use the built-in compose test (starts/stops container itself)
pytest tests/test_container.py -v
```

### 4. Example Client Usage
```bash
# Run the example client
python example_client.py
```

## Files Overview

- **`test_running_container.py`** - Tests against already-running container
- **`test_container.py`** - Original test that manages container lifecycle
- **`example_client.py`** - Example of how to use the API as a client
- **`test_container_setup.sh`** - Automated setup script

## Debugging

### View Container Logs
```bash
docker compose logs -f
```

### Check Container Status
```bash
docker compose ps
```

### Test Individual Endpoints
```bash
# Test public key endpoint
curl http://localhost:8001/public_key

# Test health (should return 404 as there's no health endpoint)
curl http://localhost:8001/
```

### Stop Container
```bash
docker compose down
```

## Common Issues

### Port Already in Use
If port 8001 is already in use:
```bash
# Find what's using the port
lsof -i :8001
# Or change the port in docker-compose.yml
```

### Container Won't Start
Check logs:
```bash
docker compose logs
```

### Secrets Not Found
Ensure secrets are generated:
```bash
ls -la run/secrets/
```
Should show:
- `private_key_server.pem`
- `public_key_server.pem`
- `public_key_client_acme.pem`
- `client_private_key_acme.pem`