# app/settings.py
import os
from pathlib import Path
from typing import Dict

PRIVATE_KEY_SERVER_FILE       = "private_key_server.pem"
PUBLIC_KEY_SERVER_FILE        = "public_key_server.pem"
PUBLIC_KEY_CLIENT_FILE_PREFIX = "public_key_client_"

CLIENT_ENV_PREFIX = "PUBLIC_KEY_CLIENT_"
SECRETS_DIR = Path("./run/secrets")

if os.getenv("DOCKER_SECRETS") == "1":
    SECRETS_DIR = Path("/run/secrets")

class SecretsSettings:
    def __init__(
        self,
        secrets_dir: Path = SECRETS_DIR,
        env_fallback: bool = True,
    ):  
        
        self.secrets_dir = secrets_dir
        self.env_fallback = env_fallback
        self.client_file_prefix = PUBLIC_KEY_CLIENT_FILE_PREFIX
        self.client_keys: Dict[str, str] = {}

        self._load_server_keys()
        self._load_client_keys()

    def _load_server_keys(self):
        path = self.secrets_dir / PRIVATE_KEY_SERVER_FILE
        try:
            self.private_key_pem = path.read_text().strip()
        except Exception as e:
            print(f"No server private key found {e}")
        
        try:
            path = self.secrets_dir / PUBLIC_KEY_SERVER_FILE
            self.public_key_pem = path.read_text().strip()
        except Exception as e:
            print(f"No server private key found {e}")
            
    def _load_client_keys(self):
        keys: Dict[str, str] = {}

        for path in self.secrets_dir.glob(f"{self.client_file_prefix}*"):
            cid = path.name[len(self.client_file_prefix):]
            if cid.endswith(".pem"):
                cid = cid[:-4]
            keys[cid] = path.read_text().strip()

        if not keys:
            raise ValueError("No client public keys discovered.")

        self.client_keys = keys


# Singleton instance
settings = SecretsSettings()
