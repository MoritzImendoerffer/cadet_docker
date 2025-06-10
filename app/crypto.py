from base64 import b64encode, b64decode
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_rsa_keypair() -> Tuple[str, str, rsa.RSAPrivateKey]:
    """
    Generate a 4096-bit RSA key pair and return
    (public_pem, private_pem, private_key_object).
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return pub_pem, priv_pem, key


def sign_bytes(data: bytes, priv: rsa.RSAPrivateKey) -> str:
    sig = priv.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return b64encode(sig).decode()


def verify_bytes(data: bytes, sig_b64: str, pub) -> bool:
    try:
        pub.verify(
            b64decode(sig_b64),
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
