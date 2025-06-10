# app/config.py
from cryptography.hazmat.primitives import serialization
from app.settings import settings


def load_private_key():
    return serialization.load_pem_private_key(
        settings.private_key_pem.encode(), password=None
    )


def load_public_key():
    return serialization.load_pem_public_key(settings.public_key_pem.encode())


def load_client_keys():
    """Return {client_id: RSAPublicKey}."""
    return {
        cid: serialization.load_pem_public_key(pem.encode())
        for cid, pem in settings.client_keys.items()
    }
