# app/settings.py
import os
from pathlib import Path
from typing import Dict

PRIVATE_KEY_SERVER_ENV        = "PRIVATE_KEY_SERVER"
PUBLIC_KEY_SERVER_ENV         = "PUBLIC_KEY_SERVER"
PUBLIC_KEY_CLIENT_ENV_PREFIX  = "PUBLIC_KEY_CLIENT_"

PRIVATE_KEY_SERVER_FILE       = "private_key_server.pem"
PUBLIC_KEY_SERVER_FILE        = "public_key_server.pem"
PUBLIC_KEY_CLIENT_FILE_PREFIX = "public_key_client_"

SECRETS_DIR  = Path("secrets")
#SECRETS_DIR_DOCKER = Path("/run/secrets")

class SecretsSettings:
    def __init__(
        self,
        secrets_dir: Path = SECRETS_DIR,
        env_fallback: bool = True,
        client_file_prefix: str = PUBLIC_KEY_CLIENT_FILE_PREFIX,
        client_env_prefix: str = PUBLIC_KEY_CLIENT_ENV_PREFIX,
    ):
        self.secrets_dir = secrets_dir
        self.env_fallback = env_fallback
        self.client_file_prefix = client_file_prefix
        self.client_env_prefix = client_env_prefix

        self.private_key_pem: str | None = os.getenv(PRIVATE_KEY_SERVER_ENV)
        self.public_key_pem: str | None = os.getenv(PUBLIC_KEY_SERVER_ENV)
        self.client_keys: Dict[str, str] = {}

        self._load_server_keys()
        self._load_client_keys()

    def _load_server_keys(self):
        if not self.private_key_pem:
            path = self.secrets_dir / PRIVATE_KEY_SERVER_FILE
            self.private_key_pem = path.read_text().strip()

        if not self.public_key_pem:
            path = self.secrets_dir / PUBLIC_KEY_SERVER_FILE
            self.public_key_pem = path.read_text().strip()

        if not self.private_key_pem or not self.public_key_pem:
            raise ValueError("Server key(s) missing (env or secrets file).")

    def _load_client_keys(self):
        keys: Dict[str, str] = {}

        if self.secrets_dir.is_dir():
            for path in self.secrets_dir.glob(f"{self.client_file_prefix}*"):
                cid = path.name[len(self.client_file_prefix):]
                if cid.endswith(".pem"):
                    cid = cid[:-4]
                keys[cid] = path.read_text().strip()

        if self.env_fallback:
            for key, value in os.environ.items():
                if key.startswith(self.client_env_prefix):
                    cid = key[len(self.client_env_prefix):]
                    keys[cid] = value.strip()

        if not keys:
            raise ValueError("No client public keys discovered.")

        self.client_keys = keys


# Singleton instance
settings = SecretsSettings()
