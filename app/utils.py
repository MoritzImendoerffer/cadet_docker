import os, base64, dill
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

def serialize(data, priv_key_path, pub_key_path):
    pickled = dill.dumps(data)
    _private_key = load_private_key(priv_key_path, pub_key_path)
    signature = _private_key.sign(
        pickled,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    
    data_dill = base64.b64encode(pickled).decode()
    signature = base64.b64encode(signature).decode()
    
    return data_dill, signature
    
def generate_keypair(path_priv: str, path_pub: str) -> rsa.RSAPrivateKey:
    """Create a fresh RSA‑2048 key‑pair (if none exist) and save both PEMs."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048,
                                   backend=default_backend())

    with open(path_priv, "wb") as fh:
        fh.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(path_pub, "wb") as fh:
        fh.write(
            key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return key


def load_private_key(priv_path: str, pub_path: str) -> rsa.RSAPrivateKey:
    if not os.path.exists(priv_path):
        return generate_keypair(priv_path, pub_path)
    
    with open(priv_path, "rb") as fh:
        return serialization.load_pem_private_key(
            fh.read(), password=None, backend=default_backend()
        )
        
def load_public_key(priv_path: str, pub_path: str) -> rsa.RSAPrivateKey:
    if not os.path.exists(pub_path):
        return generate_keypair(priv_path, pub_path)
    
    with open(pub_path, "rb") as fh:
        return serialization.load_pem_public_key(
            fh.read(), password=None, backend=default_backend()
        )
        