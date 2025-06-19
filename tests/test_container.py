#!/usr/bin/env python3
"""
Test the CADET API running in a Docker container.
This assumes the container is already running via `docker compose up`.

Usage:
    1. Start the container: docker compose up -d
    2. Run this test: python tests/test_running_container.py
"""

import base64
import sys
import time
from pathlib import Path

import dill
import requests
from cryptography.hazmat.primitives import serialization

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.crypto import sign_bytes, verify_bytes
from app.settings import SecretsSettings
from tests.cadet_utils import make_process


# Configuration
API_BASE_URL = "http://0.0.0.0:8001"
CLIENT_ID = "acme"
TIMEOUT = 10  # seconds to wait for API availability

# Load settings to find where secrets are stored
settings = SecretsSettings()
SECRETS_DIR = settings.secrets_dir
CLIENT_PRIVATE_KEY_PATH = SECRETS_DIR / f"client_private_key_{CLIENT_ID}.pem"


def wait_for_api():
    """Wait for the API to become available."""
    print(f"Waiting for API at {API_BASE_URL}...")
    for i in range(TIMEOUT):
        try:
            resp = requests.get(f"{API_BASE_URL}/public_key", timeout=1)
            if resp.ok:
                print("API is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        print(f"  Retry {i+1}/{TIMEOUT}...")
    return False


def load_client_private_key():
    """Load the client private key from the filesystem."""
    if not CLIENT_PRIVATE_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Client private key not found at {CLIENT_PRIVATE_KEY_PATH}\n"
            f"Run: python tests/generate_secrets.py {SECRETS_DIR}"
        )
    
    key_pem = CLIENT_PRIVATE_KEY_PATH.read_bytes()
    return serialization.load_pem_private_key(key_pem, password=None)


def test_public_key_endpoint():
    """Test the /public_key endpoint."""
    print("\n[TEST] GET /public_key")
    resp = requests.get(f"{API_BASE_URL}/public_key")
    assert resp.ok, f"Failed: {resp.status_code} - {resp.text}"
    
    data = resp.json()
    assert "public_key" in data
    assert data["public_key"].startswith("-----BEGIN PUBLIC KEY-----")


def test_simulate_endpoint():
    """Test the /simulate endpoint with a valid request."""
    print("\n[TEST] POST /simulate")
    
    resp = requests.get(f"{API_BASE_URL}/public_key")
    assert resp.ok, f"Failed to get public key: {resp.status_code} - {resp.text}"
    server_pub_key_pem = resp.json()["public_key"]
    # Load client private key
    client_priv = load_client_private_key()
    
    # Create a test process
    process = make_process()
    process_bytes = dill.dumps(process)
    process_b64 = base64.b64encode(process_bytes).decode()
    signature = sign_bytes(process_bytes, client_priv)
    
    # Send request
    resp = requests.post(
        f"{API_BASE_URL}/simulate",
        json={
            "client_id": CLIENT_ID,
            "process_serialized": process_b64,
            "signature": signature,
        },
        timeout=300,  # Simulation can take time
    )
    
    assert resp.ok, f"Failed: {resp.status_code} - {resp.text}"
    data = resp.json()
    
    # Verify response structure
    assert "results_serialized" in data
    assert "signature" in data
    
    # Verify server signature
    server_pub = serialization.load_pem_public_key(server_pub_key_pem.encode())
    results_bytes = base64.b64decode(data["results_serialized"])
    assert verify_bytes(results_bytes, data["signature"], server_pub)
    
    # Verify we can deserialize the results
    results = dill.loads(results_bytes)
    assert hasattr(results, "solution")
    
    print("Simulate endpoint works")
    print(f"  - Process simulated successfully")
    print(f"  - Server signature verified")
    print(f"  - Results deserialized successfully")


def test_invalid_client_id():
    """Test with an unknown client ID."""
    print("\n[TEST] Invalid client ID")
    
    # Use a valid key but wrong client ID
    client_priv = load_client_private_key()
    process = make_process()
    process_bytes = dill.dumps(process)
    
    resp = requests.post(
        f"{API_BASE_URL}/simulate",
        json={
            "client_id": "unknown_client",
            "process_serialized": base64.b64encode(process_bytes).decode(),
            "signature": sign_bytes(process_bytes, client_priv),
        },
    )
    
    assert resp.status_code == 400
    assert "Unknown client_id" in resp.text
    print("Unknown client rejected correctly")


def test_invalid_signature():
    """Test with an invalid signature."""
    print("\n[TEST] Invalid signature")
    
    process = make_process()
    process_bytes = dill.dumps(process)
    
    resp = requests.post(
        f"{API_BASE_URL}/simulate",
        json={
            "client_id": CLIENT_ID,
            "process_serialized": base64.b64encode(process_bytes).decode(),
            "signature": "invalid_signature_here",
        },
    )
    
    assert resp.status_code == 400
    assert "Invalid signature" in resp.text
    print("✓ Invalid signature rejected correctly")


def test_invalid_process_data():
    """Test with invalid process data."""
    print("\n[TEST] Invalid process data")
    
    client_priv = load_client_private_key()
    bad_data = b"not a valid dill object"
    
    resp = requests.post(
        f"{API_BASE_URL}/simulate",
        json={
            "client_id": CLIENT_ID,
            "process_serialized": base64.b64encode(bad_data).decode(),
            "signature": sign_bytes(bad_data, client_priv),
        },
    )
    
    assert resp.status_code == 400
    assert "Deserialization failed" in resp.text
    print("✓ Invalid process data rejected correctly")


def main():
    """Run all tests against the running container."""
    print("="*60)
    print("Testing CADET API Container")
    print("="*60)
    
    # Check if API is available
    if not wait_for_api():
        print("API is not available!")
        print("Make sure the container is running:")
        print("  docker compose up -d")
        sys.exit(1)
    
    try:
        # Run tests
        server_pub_key = test_public_key_endpoint()
        test_simulate_endpoint(server_pub_key)
        test_invalid_client_id()
        test_invalid_signature()
        test_invalid_process_data()
        
        print("\n" + "="*60)
        print("All tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_simulate_endpoint()