from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def create_server_keys(env_file=".env", key_dir=None, overwrite=False):
    """
    Generate an RSA server keypair, store them securely (default: ~/.cadet_api/),
    and optionally update a .env file.

    Args:
        env_file: Path to .env file, or None to skip
        key_dir: Directory to store key files
        overwrite: If True, regenerate keys even if they exist
    """
    key_dir = Path(key_dir or Path.home() / ".cadet_api").resolve()
    key_dir.mkdir(parents=True, exist_ok=True)

    priv_path = key_dir / "private_key.pem"
    pub_path = key_dir / "public_key.pem"

    if not overwrite and (priv_path.exists() or pub_path.exists()):
        print(f"Keys already exist at: {key_dir}")
        return

    print(f"Generating keypair in: {key_dir}")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    with open(priv_path, "wb") as f:
        f.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ))

    with open(pub_path, "wb") as f:
        f.write(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    if env_file:
        from dotenv import set_key
        env_path = Path(env_file).resolve()
        env_path.touch(exist_ok=True)
        set_key(str(env_path), "PRIVATE_KEY_PATH", str(priv_path))
        set_key(str(env_path), "PUBLIC_KEY_PATH", str(pub_path))
        print(f".env updated with:\n  PRIVATE_KEY_PATH={priv_path}\n  PUBLIC_KEY_PATH={pub_path}")

    print("Keys created.")

if __name__ == "__main__":
    create_server_keys()
