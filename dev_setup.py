#!/usr/bin/env python3
"""dev_setup.py – Ensure host‑side key & certificate hierarchy for Cadet

This helper is meant to be executed **before** `docker compose up` (e.g. it is
invoked from `dev_setup.sh`).  It guarantees that the directory expected by the
container (`~/.cadet_api` by default) exists and contains:

    private_key.pem   – RSA 4096‑bit private key used by the API & TLS
    public_key.pem    – Matching public key (exported from the private key)
    client_keys/      – Folder for per‑client public keys (created if missing)
    tls/
        server.key    – Symlink (or copy) of private_key.pem
        server.crt    – Self‑signed certificate for https://localhost:8001

If any of these artefacts are missing they are generated **idempotently** –
existing files are preserved.

The root directory can be overridden with the `CADET_KEY_HOME` environment
variable, allowing flexible setups (CI runners, different host OS, etc.).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

HOME: Final[Path] = Path.home()
CADET_HOME: Final[Path] = Path(
    os.getenv("CADET_KEY_HOME", HOME / ".cadet_api")  # default ~/.cadet_api
).expanduser()

SERVER_KEY: Final[Path] = CADET_HOME / "private_key.pem"
SERVER_PUB: Final[Path] = CADET_HOME / "public_key.pem"
CLIENT_KEYS_DIR: Final[Path] = CADET_HOME / "client_keys"
TLS_DIR: Final[Path] = CADET_HOME / "tls"
TLS_KEY: Final[Path] = TLS_DIR / "server.key"
TLS_CERT: Final[Path] = TLS_DIR / "server.crt"


def _run(cmd: str) -> None:
    """Run *cmd* with the user's shell, abort on non‑zero exit."""
    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Key / cert creation
# ---------------------------------------------------------------------------

def _generate_server_keys() -> None:
    print(f"Generating server RSA key‑pair in {CADET_HOME}")
    _run(f'openssl genrsa -out "{SERVER_KEY}" 4096')
    _run(f'openssl rsa -in "{SERVER_KEY}" -pubout -out "{SERVER_PUB}"')


def _generate_tls_cert() -> None:
    print(f"Generating self‑signed TLS cert in {TLS_DIR}")
    subj = "/CN=localhost/O=Cadet Dev/C=US"
    # Re‑use the same private key for convenience.
    _run(f'cp "{SERVER_KEY}" "{TLS_KEY}"')
    _run(
        f'openssl req -new -x509 -nodes -days 365 '
        f'-subj "{subj}" '
        f'-key "{TLS_KEY}" -out "{TLS_CERT}"'
    )


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401 – simple function
    """Create the full directory tree & artefacts if they don’t exist."""
    # 1. Directory skeleton
    for d in (CADET_HOME, CLIENT_KEYS_DIR, TLS_DIR):
        _ensure_dir(d)

    # 2. Server key‑pair
    if not SERVER_KEY.exists() or not SERVER_PUB.exists():
        _generate_server_keys()
    else:
        print("Server key‑pair already present – nothing to do")

    # 3. TLS artefacts
    if not TLS_KEY.exists() or not TLS_CERT.exists():
        _generate_tls_cert()
    else:
        print("TLS certificate already present – nothing to do")

    print("\n dev_setup.py finished – layout ready:")
    print(f"    {CADET_HOME}")
    print("  ├── private_key.pem")
    print("  ├── public_key.pem")
    print("  ├── client_keys/")
    print("  └── tls/")
    print("      ├── server.key")
    print("      └── server.crt")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc.cmd}", file=sys.stderr)
        sys.exit(exc.returncode)
