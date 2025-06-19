"""
Simplified unit tests for SecretsSettings - self-contained without external fixtures.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.settings import SecretsSettings, SECRETS_DIR
from app.crypto import generate_rsa_keypair
from app.config import load_private_key, load_public_key, load_client_keys


class TestSecretsSettings:
    """Test the SecretsSettings class."""
    
    def test_load_from_files(self):
        """Test loading secrets from files."""
        # Generate test keys
        server_pub, server_priv, _ = generate_rsa_keypair()
        client_pub, client_priv, _ = generate_rsa_keypair()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Write keys to files
            (secrets_dir / "private_key_server.pem").write_text(server_priv)
            (secrets_dir / "public_key_server.pem").write_text(server_pub)
            (secrets_dir / "public_key_client_alice.pem").write_text(client_pub)
            
            # Load settings
            settings = SecretsSettings(secrets_dir=secrets_dir)
            
            # Verify keys loaded correctly
            assert settings.private_key_pem == server_priv
            assert settings.public_key_pem == server_pub
            assert 'alice' in settings.client_keys
            assert settings.client_keys['alice'] == client_pub
    
    def test_load_from_env_vars(self):
        """Test loading secrets from environment variables."""
        # Generate test keys
        server_pub, server_priv, _ = generate_rsa_keypair()
        client_pub, client_priv, _ = generate_rsa_keypair()
        
        # Save current env
        saved_env = {}
        env_keys = ['PRIVATE_KEY_SERVER', 'PUBLIC_KEY_SERVER', 'PUBLIC_KEY_CLIENT_test']
        for key in env_keys:
            if key in os.environ:
                saved_env[key] = os.environ[key]
        
        try:
            # Set environment variables
            os.environ['PRIVATE_KEY_SERVER'] = server_priv
            os.environ['PUBLIC_KEY_SERVER'] = server_pub
            os.environ['PUBLIC_KEY_CLIENT_test'] = client_pub
            
            # Use non-existent directory to force env fallback
            settings = SecretsSettings(
                secrets_dir=Path("/non/existent/path"),
                env_fallback=True
            )
            
            # Verify keys loaded from environment
            assert settings.private_key_pem == server_priv
            assert settings.public_key_pem == server_pub
            assert 'test' in settings.client_keys
            assert settings.client_keys['test'] == client_pub
            
        finally:
            # Restore environment
            for key in env_keys:
                if key in saved_env:
                    os.environ[key] = saved_env[key]
                elif key in os.environ:
                    del os.environ[key]
    
    def test_files_take_precedence(self):
        """Test that files take precedence over environment variables."""
        # Generate different keys for files and env
        file_server_pub, file_server_priv, _ = generate_rsa_keypair()
        env_server_pub, env_server_priv, _ = generate_rsa_keypair()
        
        # Save current env
        saved_env = {}
        env_keys = ['PRIVATE_KEY_SERVER', 'PUBLIC_KEY_SERVER']
        for key in env_keys:
            if key in os.environ:
                saved_env[key] = os.environ[key]
        
        try:
            # Set environment variables
            os.environ['PRIVATE_KEY_SERVER'] = env_server_priv
            os.environ['PUBLIC_KEY_SERVER'] = env_server_pub
            
            with tempfile.TemporaryDirectory() as tmpdir:
                secrets_dir = Path(tmpdir)
                
                # Write different keys to files
                (secrets_dir / "private_key_server.pem").write_text(file_server_priv)
                (secrets_dir / "public_key_server.pem").write_text(file_server_pub)
                (secrets_dir / "public_key_client_test.pem").write_text("client_key")
                
                # Load settings with env_fallback=True
                settings = SecretsSettings(secrets_dir=secrets_dir, env_fallback=True)
                
                # Should use file values, not env values
                assert settings.private_key_pem == file_server_priv
                assert settings.public_key_pem == file_server_pub
                
        finally:
            # Restore environment
            for key in env_keys:
                if key in saved_env:
                    os.environ[key] = saved_env[key]
                elif key in os.environ:
                    del os.environ[key]
    
    def test_missing_private_key_error(self):
        """Test error when private key is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Only write public key and client key
            (secrets_dir / "public_key_server.pem").write_text("public_key")
            (secrets_dir / "public_key_client_test.pem").write_text("client_key")
            
            # Should raise error
            with pytest.raises(ValueError) as exc_info:
                SecretsSettings(secrets_dir=secrets_dir, env_fallback=False)
            
            assert "No server private key found" in str(exc_info.value)
    
    def test_missing_public_key_error(self):
        """Test error when public key is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Only write private key and client key
            (secrets_dir / "private_key_server.pem").write_text("private_key")
            (secrets_dir / "public_key_client_test.pem").write_text("client_key")
            
            # Should raise error
            with pytest.raises(ValueError) as exc_info:
                SecretsSettings(secrets_dir=secrets_dir, env_fallback=False)
            
            assert "No server public key found" in str(exc_info.value)
    
    def test_missing_client_keys_error(self):
        """Test error when no client keys are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Only write server keys
            (secrets_dir / "private_key_server.pem").write_text("private_key")
            (secrets_dir / "public_key_server.pem").write_text("public_key")
            
            # Should raise error
            with pytest.raises(ValueError) as exc_info:
                SecretsSettings(secrets_dir=secrets_dir, env_fallback=False)
            
            assert "No client public keys found" in str(exc_info.value)
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from loaded keys."""
        # Generate test keys
        server_pub, server_priv, _ = generate_rsa_keypair()
        client_pub, client_priv, _ = generate_rsa_keypair()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Write keys with extra whitespace
            (secrets_dir / "private_key_server.pem").write_text(f"\n\n{server_priv}\n\n")
            (secrets_dir / "public_key_server.pem").write_text(f"  {server_pub}  \t")
            (secrets_dir / "public_key_client_test.pem").write_text(f"\r\n{client_pub}\r\n")
            
            # Load settings
            settings = SecretsSettings(secrets_dir=secrets_dir)
            
            # Whitespace should be stripped
            assert settings.private_key_pem == server_priv
            assert settings.public_key_pem == server_pub
            assert settings.client_keys['test'] == client_pub


class TestCryptoIntegration:
    """Test integration with crypto loading functions."""
    
    def test_load_crypto_objects(self):
        """Test loading secrets into cryptography objects."""
        # Generate valid test keys
        server_pub, server_priv, _ = generate_rsa_keypair()
        client_pub, client_priv, _ = generate_rsa_keypair()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Write keys to files
            (secrets_dir / "private_key_server.pem").write_text(server_priv)
            (secrets_dir / "public_key_server.pem").write_text(server_pub)
            (secrets_dir / "public_key_client_test.pem").write_text(client_pub)
            
            # Create settings
            settings = SecretsSettings(secrets_dir=secrets_dir)
            
            # Patch the settings singleton
            with patch('app.config.settings', settings):
                # Load crypto objects
                private_key = load_private_key()
                public_key = load_public_key()
                client_keys = load_client_keys()
                
                # Check types
                from cryptography.hazmat.primitives.asymmetric import rsa
                assert isinstance(private_key, rsa.RSAPrivateKey)
                assert isinstance(public_key, rsa.RSAPublicKey)
                assert all(isinstance(k, rsa.RSAPublicKey) for k in client_keys.values())
                
                # Check client IDs
                assert 'test' in client_keys
    
    def test_sign_and_verify(self):
        """Test signing and verifying with loaded keys."""
        from app.crypto import sign_bytes, verify_bytes
        
        # Generate valid test keys
        server_pub, server_priv, _ = generate_rsa_keypair()
        client_pub, client_priv, _ = generate_rsa_keypair()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_dir = Path(tmpdir)
            
            # Write keys to files
            (secrets_dir / "private_key_server.pem").write_text(server_priv)
            (secrets_dir / "public_key_server.pem").write_text(server_pub)
            (secrets_dir / "public_key_client_test.pem").write_text(client_pub)
            
            # Create settings
            settings = SecretsSettings(secrets_dir=secrets_dir)
            
            # Patch the settings singleton
            with patch('app.config.settings', settings):
                # Load keys
                private_key = load_private_key()
                public_key = load_public_key()
                
                # Sign data
                data = b"Test message"
                signature = sign_bytes(data, private_key)
                
                # Verify signature
                assert verify_bytes(data, signature, public_key)
                
                # Verify fails with wrong data
                assert not verify_bytes(b"Wrong message", signature, public_key)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])