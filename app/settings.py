# app/settings.py
import os
from pathlib import Path
from typing import Dict

# File names for secrets (these are public as they define the file structure)
PRIVATE_KEY_SERVER_FILE = "private_key_server.pem"
PUBLIC_KEY_SERVER_FILE = "public_key_server.pem"
PUBLIC_KEY_CLIENT_FILE_PREFIX = "public_key_client_"

# Default secrets directory
DEFAULT_SECRETS_DIR = Path("./run/secrets")

# Determine secrets directory based on environment
def get_secrets_dir() -> Path:
    # Allow custom secrets directory via environment variable
    if custom_dir := os.getenv("SECRETS_DIR"):
        return Path(custom_dir)
    
    # Use Docker secrets directory if DOCKER_SECRETS is set
    if os.getenv("DOCKER_SECRETS") == "1":
        return Path("/run/secrets")
    
    # Default to local run/secrets
    return DEFAULT_SECRETS_DIR


class SecretsSettings:
    """
    Manages loading of cryptographic keys from files or environment variables.
    
    File mode: Reads from secrets_dir/*.pem files
    Env mode: Falls back to environment variables if files not found
    
    Environment variables:
    - PRIVATE_KEY_SERVER: Server private key PEM content
    - PUBLIC_KEY_SERVER: Server public key PEM content  
    - PUBLIC_KEY_CLIENT_<client_id>: Client public key PEM content
    """
    
    # Internal environment variable names
    _PRIVATE_KEY_ENV = "PRIVATE_KEY_SERVER"
    _PUBLIC_KEY_ENV = "PUBLIC_KEY_SERVER"
    _CLIENT_KEY_PREFIX = "PUBLIC_KEY_CLIENT_"
    
    def __init__(
        self,
        secrets_dir: Path = None,
        env_fallback: bool = True,
    ):
        # Use provided directory or determine from environment
        self.secrets_dir = secrets_dir or get_secrets_dir()
        self.env_fallback = env_fallback
        self.client_file_prefix = PUBLIC_KEY_CLIENT_FILE_PREFIX
        self.client_keys: Dict[str, str] = {}

        self._load_server_keys()
        self._load_client_keys()

    def _load_server_keys(self):
        # Try to load private key
        private_key_path = self.secrets_dir / PRIVATE_KEY_SERVER_FILE
        if private_key_path.exists():
            self.private_key_pem = private_key_path.read_text().strip()
        elif self.env_fallback and os.getenv(self._PRIVATE_KEY_ENV):
            self.private_key_pem = os.getenv(self._PRIVATE_KEY_ENV).strip()
        else:
            raise ValueError(
                f"No server private key found at {private_key_path} "
                f"or in environment variable {self._PRIVATE_KEY_ENV}"
            )

        # Try to load public key
        public_key_path = self.secrets_dir / PUBLIC_KEY_SERVER_FILE
        if public_key_path.exists():
            self.public_key_pem = public_key_path.read_text().strip()
        elif self.env_fallback and os.getenv(self._PUBLIC_KEY_ENV):
            self.public_key_pem = os.getenv(self._PUBLIC_KEY_ENV).strip()
        else:
            raise ValueError(
                f"No server public key found at {public_key_path} "
                f"or in environment variable {self._PUBLIC_KEY_ENV}"
            )

    def _load_client_keys(self):
        keys: Dict[str, str] = {}

        # First, try to load from files
        if self.secrets_dir.exists():
            for path in self.secrets_dir.glob(f"{self.client_file_prefix}*.pem"):
                cid = path.name[len(self.client_file_prefix):-4]  # Remove prefix and .pem
                keys[cid] = path.read_text().strip()

        # Then, check environment variables if env_fallback is enabled
        if self.env_fallback:
            for env_name, env_value in os.environ.items():
                if env_name.startswith(self._CLIENT_KEY_PREFIX):
                    cid = env_name[len(self._CLIENT_KEY_PREFIX):]
                    if cid:  # Ensure client_id is not empty
                        keys[cid] = env_value.strip()

        if not keys:
            raise ValueError(
                f"No client public keys found in {self.secrets_dir} "
                f"or in environment variables starting with {self._CLIENT_KEY_PREFIX}"
            )

        self.client_keys = keys


# Singleton instance
settings = SecretsSettings()