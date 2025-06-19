#!/usr/bin/env python3
"""
Diagnostic script to test PEM key handling through environment variables.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.crypto import generate_rsa_keypair, sign_bytes, verify_bytes
from cryptography.hazmat.primitives import serialization


def test_pem_through_env():
    """Test that PEM keys work correctly when passed through environment variables."""
    
    # Generate test keys
    pub_pem, priv_pem, priv_key = generate_rsa_keypair()
    
    print("Original PEM format:")
    print(f"Private key lines: {len(priv_pem.splitlines())}")
    print(f"Public key lines: {len(pub_pem.splitlines())}")
    print(f"First line: {priv_pem.splitlines()[0]}")
    print(f"Last line: {priv_pem.splitlines()[-1]}")
    
    # Set environment variables
    os.environ["TEST_PRIVATE_KEY"] = priv_pem
    os.environ["TEST_PUBLIC_KEY"] = pub_pem
    
    # Read back from environment
    retrieved_priv = os.environ["TEST_PRIVATE_KEY"]
    retrieved_pub = os.environ["TEST_PUBLIC_KEY"]
    
    print("\nRetrieved from environment:")
    print(f"Private key matches: {retrieved_priv == priv_pem}")
    print(f"Public key matches: {retrieved_pub == pub_pem}")
    
    # Test loading the keys
    try:
        loaded_priv = serialization.load_pem_private_key(retrieved_priv.encode(), None)
        loaded_pub = serialization.load_pem_public_key(retrieved_pub.encode())
        print("\nKey loading: SUCCESS")
        
        # Test signing and verification
        test_data = b"Hello, World!"
        signature = sign_bytes(test_data, loaded_priv)
        verified = verify_bytes(test_data, signature, loaded_pub)
        print(f"Signature verification: {'SUCCESS' if verified else 'FAILED'}")
        
    except Exception as e:
        print(f"\nKey loading: FAILED - {e}")
    
    # Clean up
    del os.environ["TEST_PRIVATE_KEY"]
    del os.environ["TEST_PUBLIC_KEY"]


def test_settings_with_env():
    """Test SecretsSettings with environment variables."""
    from app.settings import SecretsSettings
    
    # Generate test keys
    server_pub, server_priv, _ = generate_rsa_keypair()
    client_pub, client_priv, _ = generate_rsa_keypair()
    
    # Set environment variables
    os.environ["PRIVATE_KEY_SERVER"] = server_priv
    os.environ["PUBLIC_KEY_SERVER"] = server_pub
    os.environ["PUBLIC_KEY_CLIENT_test"] = client_pub
    
    try:
        # Create settings with non-existent directory to force env fallback
        settings = SecretsSettings(
            secrets_dir=Path("/non/existent/path"),
            env_fallback=True
        )
        
        print("\nSecretsSettings test:")
        print(f"Loaded server private key: {len(settings.private_key_pem)} chars")
        print(f"Loaded server public key: {len(settings.public_key_pem)} chars")
        print(f"Loaded client keys: {list(settings.client_keys.keys())}")
        
        # Test that keys can be loaded
        from app.config import load_private_key, load_public_key, load_client_keys
        from unittest.mock import patch
        
        with patch('app.config.settings', settings):
            priv = load_private_key()
            pub = load_public_key()
            clients = load_client_keys()
            
            print("Key loading through config: SUCCESS")
            print(f"Client keys loaded: {list(clients.keys())}")
            
    except Exception as e:
        print(f"\nSecretsSettings test: FAILED - {e}")
    finally:
        # Clean up
        del os.environ["PRIVATE_KEY_SERVER"]
        del os.environ["PUBLIC_KEY_SERVER"]
        del os.environ["PUBLIC_KEY_CLIENT_test"]


if __name__ == "__main__":
    print("Testing PEM key handling through environment variables...")
    test_pem_through_env()
    print("\n" + "="*50 + "\n")
    test_settings_with_env()