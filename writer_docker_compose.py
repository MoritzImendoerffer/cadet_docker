import yaml
from app.settings import settings

# Compose service name and image context
SERVICE_NAME = "cadet-api"
SECRETS_DIR = "run/secrets"
DOCKER_FILE = "Dockerfile_ubuntu"
ENV_FILE = ".env"

all_secrets = {
    "private_key_server.pem": "private_key_server.pem",
    "public_key_server.pem": "public_key_server.pem",
    **{
        f"public_key_client_{cid}.pem": f"public_key_client_{cid}.pem"
        for cid in settings.client_keys
    },
}

compose = {
    "version": "3.8",
    "services": {
        SERVICE_NAME: {
            "image": "cadet-api",
            "build": {
                "context": ".",
                "dockerfile": DOCKER_FILE
            },
            "ports": ["8001:8001"],
            "secrets": list(all_secrets.keys()),
            "env_file": "docker.env",
        },
    },
    "secrets": {
        name: {
            "file": f"{SECRETS_DIR}/{filename}"
        }
        for name, filename in all_secrets.items()
    }
}

# Output to docker-compose.yml
with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

print("docker-compose.yml generated.")
