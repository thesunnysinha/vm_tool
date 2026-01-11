"""Secrets management with support for multiple backends."""

import logging
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value by key."""
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret value."""
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete secret."""
        pass

    @abstractmethod
    def list_secrets(self) -> list:
        """List all secret keys."""
        pass


class VaultBackend(SecretsBackend):
    """HashiCorp Vault secrets backend."""

    def __init__(
        self,
        vault_url: str,
        vault_token: Optional[str] = None,
        mount_point: str = "secret",
    ):
        self.vault_url = vault_url.rstrip("/")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point

        if not self.vault_token:
            raise ValueError("Vault token required (set VAULT_TOKEN env var)")

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault."""
        import requests

        url = f"{self.vault_url}/v1/{self.mount_point}/data/{key}"
        headers = {"X-Vault-Token": self.vault_token}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("data", {}).get("value")
        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Vault."""
        import requests

        url = f"{self.vault_url}/v1/{self.mount_point}/data/{key}"
        headers = {"X-Vault-Token": self.vault_token}
        payload = {"data": {"value": value}}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Secret '{key}' stored in Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault."""
        import requests

        url = f"{self.vault_url}/v1/{self.mount_point}/metadata/{key}"
        headers = {"X-Vault-Token": self.vault_token}

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Secret '{key}' deleted from Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False

    def list_secrets(self) -> list:
        """List all secrets in Vault."""
        import requests

        url = f"{self.vault_url}/v1/{self.mount_point}/metadata"
        headers = {"X-Vault-Token": self.vault_token}

        try:
            response = requests.get(url, headers=headers, params={"list": "true"})
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("keys", [])
        except Exception as e:
            logger.error(f"Failed to list secrets from Vault: {e}")
            return []


class AWSSecretsBackend(SecretsBackend):
    """AWS Secrets Manager backend."""

    def __init__(self, region: str = "us-east-1"):
        try:
            import boto3

            self.client = boto3.client("secretsmanager", region_name=region)
        except ImportError:
            raise ImportError(
                "boto3 required for AWS Secrets Manager (pip install boto3)"
            )

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=key)
            return response.get("SecretString")
        except Exception as e:
            logger.error(f"Failed to get secret from AWS: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager."""
        try:
            # Try to update existing secret first
            try:
                self.client.update_secret(SecretId=key, SecretString=value)
            except self.client.exceptions.ResourceNotFoundException:
                # Create new secret if it doesn't exist
                self.client.create_secret(Name=key, SecretString=value)

            logger.info(f"Secret '{key}' stored in AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in AWS: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager."""
        try:
            self.client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            logger.info(f"Secret '{key}' deleted from AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from AWS: {e}")
            return False

    def list_secrets(self) -> list:
        """List all secrets in AWS Secrets Manager."""
        try:
            response = self.client.list_secrets()
            return [s["Name"] for s in response.get("SecretList", [])]
        except Exception as e:
            logger.error(f"Failed to list secrets from AWS: {e}")
            return []


class EncryptedFileBackend(SecretsBackend):
    """Encrypted file-based secrets backend."""

    def __init__(
        self, secrets_file: str = ".secrets.enc", encryption_key: Optional[str] = None
    ):
        self.secrets_file = secrets_file
        self.encryption_key = encryption_key or os.getenv("SECRETS_KEY")

        if not self.encryption_key:
            raise ValueError("Encryption key required (set SECRETS_KEY env var)")

        self.secrets = self._load_secrets()

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from encrypted file."""
        return self.secrets.get(key)

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in encrypted file."""
        self.secrets[key] = value
        return self._save_secrets()

    def delete_secret(self, key: str) -> bool:
        """Delete secret from encrypted file."""
        if key in self.secrets:
            del self.secrets[key]
            return self._save_secrets()
        return False

    def list_secrets(self) -> list:
        """List all secret keys."""
        return list(self.secrets.keys())

    def _load_secrets(self) -> Dict[str, str]:
        """Load and decrypt secrets from file."""
        if not os.path.exists(self.secrets_file):
            return {}

        try:
            from cryptography.fernet import Fernet

            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()

            fernet = Fernet(self.encryption_key.encode())
            decrypted_data = fernet.decrypt(encrypted_data)

            import json

            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return {}

    def _save_secrets(self) -> bool:
        """Encrypt and save secrets to file."""
        try:
            from cryptography.fernet import Fernet
            import json

            fernet = Fernet(self.encryption_key.encode())
            data = json.dumps(self.secrets).encode()
            encrypted_data = fernet.encrypt(data)

            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)

            return True
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
            return False


class SecretsManager:
    """Unified secrets manager supporting multiple backends."""

    def __init__(self, backend: SecretsBackend):
        self.backend = backend

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value."""
        value = self.backend.get_secret(key)
        return value if value is not None else default

    def set(self, key: str, value: str) -> bool:
        """Set secret value."""
        return self.backend.set_secret(key, value)

    def delete(self, key: str) -> bool:
        """Delete secret."""
        return self.backend.delete_secret(key)

    def list(self) -> list:
        """List all secret keys."""
        return self.backend.list_secrets()

    @classmethod
    def from_vault(cls, vault_url: str, **kwargs):
        """Create secrets manager with Vault backend."""
        return cls(VaultBackend(vault_url, **kwargs))

    @classmethod
    def from_aws(cls, region: str = "us-east-1"):
        """Create secrets manager with AWS backend."""
        return cls(AWSSecretsBackend(region))

    @classmethod
    def from_file(cls, secrets_file: str = ".secrets.enc", **kwargs):
        """Create secrets manager with encrypted file backend."""
        return cls(EncryptedFileBackend(secrets_file, **kwargs))
