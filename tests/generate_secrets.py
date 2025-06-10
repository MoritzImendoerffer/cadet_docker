#!/usr/bin/env python3
"""
Generate demo PEM files for the CADet API and write them to ./secrets
(or to a custom directory you pass as an argument).

Creates:
  private_key_server.pem        – server private key
  public_key_server.pem         – server public key
  client_private_key_acme.pem   – local-dev private key for client “acme”
  public_key_client_acme.pem    – public key for client “acme”
"""

from __future__ import annotations
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# -----------------------------------------------------------------------------
CLIENT_ID = "acme"               # change or add more clients if desired


def _gen_keypair(bits: int = 4096) -> tuple[bytes, bytes]:
    """Return (private_pem, public_pem)."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def main(out_dir: str | Path = "secrets") -> None:
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    # server keys ----------------------------------------------------------
    srv_priv, srv_pub = _gen_keypair()
    (out / "private_key_server.pem").write_bytes(srv_priv)
    (out / "public_key_server.pem").write_bytes(srv_pub)

    # client keys ----------------------------------------------------------
    cli_priv, cli_pub = _gen_keypair()
    (out / f"client_private_key_{CLIENT_ID}.pem").write_bytes(cli_priv)
    (out / f"public_key_client_{CLIENT_ID}.pem").write_bytes(cli_pub)

    print(
        f"Secrets written to {out}:\n"
        "private_key_server.pem\n"
        "public_key_server.pem\n"
        f"client_private_key_{CLIENT_ID}.pem\n"
        f"public_key_client_{CLIENT_ID}.pem"
    )


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "secrets"
    main(target)
