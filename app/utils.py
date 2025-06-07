# utils.py
import os, base64, dill
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


def _generate_keypair(priv_path: str, pub_path: str) -> rsa.RSAPrivateKey:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048,
                                   backend=default_backend())
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
    if not os.path.exists(priv_path):
        return _generate_keypair(priv_path, pub_path)
    with open(priv_path, "rb") as fh:
        return serialization.load_pem_private_key(fh.read(), None, default_backend())


def load_public_key(path: str):
    with open(path, "rb") as fh:
        return serialization.load_pem_public_key(fh.read(), backend=default_backend())


def sign_bytes(data: bytes, private_key: rsa.RSAPrivateKey) -> str:
    sig = private_key.sign(
        data,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode()


def verify_bytes(data: bytes, sig_b64: str, public_key) -> bool:
    try:
        public_key.verify(
            base64.b64decode(sig_b64),
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False

def dill_serialize(obj, signer_priv: rsa.RSAPrivateKey) -> tuple[str, str]:
    pickled = dill.dumps(obj)
    sig = sign_bytes(pickled, signer_priv)
    return base64.b64encode(pickled).decode(), sig

def dill_deserialize(b64: str):
    return dill.loads(base64.b64decode(b64))
