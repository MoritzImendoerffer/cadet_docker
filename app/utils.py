import base64
import dill
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


def _generate_keypair(priv_path: str, pub_path: str) -> rsa.RSAPrivateKey:
    """Generate a new RSA keypair and save to the specified file paths."""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    with open(priv_path, "wb") as fh:
        fh.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
    with open(pub_path, "wb") as fh:
        fh.write(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    return key


def load_private_key(priv_path: str, pub_path: str) -> rsa.RSAPrivateKey:
    """Load an existing RSA private key or generate a new one if not found."""
    if not Path(priv_path).exists():
        return _generate_keypair(priv_path, pub_path)
    with open(priv_path, "rb") as fh:
        return serialization.load_pem_private_key(
            fh.read(), password=None, backend=default_backend()
        )


def load_public_key(path: str):
    """Load a public RSA key from a PEM file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Public key not found at: {path}")
    with open(path, "rb") as fh:
        return serialization.load_pem_public_key(
            fh.read(), backend=default_backend()
        )


def sign_bytes(data: bytes, private_key: rsa.RSAPrivateKey) -> str:
    """Sign bytes using RSA private key with PSS padding and return base64 signature."""
    sig = private_key.sign(
        data,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode()


def verify_bytes(data: bytes, sig_b64: str, public_key) -> bool:
    """Verify a base64-encoded RSA signature."""
    try:
        public_key.verify(
            base64.b64decode(sig_b64),
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def dill_serialize(obj, signer_priv: rsa.RSAPrivateKey) -> tuple[str, str]:
    """Serialize a Python object with dill and return (base64_serialized, base64_signature)."""
    pickled = dill.dumps(obj)
    sig = sign_bytes(pickled, signer_priv)
    return base64.b64encode(pickled).decode(), sig


def dill_deserialize(b64: str):
    """Deserialize a base64-encoded dill object."""
    return dill.loads(base64.b64decode(b64))
