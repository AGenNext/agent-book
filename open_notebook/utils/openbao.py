"""
OpenBAO Secrets Manager

Integrate with OpenBAO (Vault) for secrets management.
OpenBAO runs at secrets.unboxd.cloud (port 8200)
"""

import os
from typing import Optional, Any
from dataclasses import dataclass

from loguru import logger


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class OpenBAOConfig:
    """OpenBAO connection configuration."""
    addr: str = "http://127.0.0.1:8200"
    token: Optional[str] = None
    mount_point: str = "secret"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "OpenBAOConfig":
        """Load config from environment variables."""
        return cls(
            addr=os.getenv("OPENBAO_ADDR", "http://127.0.0.1:8200"),
            token=os.getenv("OPENBAO_TOKEN"),
            mount_point=os.getenv("OPENBAO_MOUNT_POINT", "secret"),
        )


# =============================================================================
# Secrets Client
# =============================================================================


class OpenBAOSecrets:
    """Client for reading secrets from OpenBAO."""

    def __init__(self, config: Optional[OpenBAOConfig] = None):
        self.config = config or OpenBAOConfig.from_env()
        self._cache: dict = {}
        self._client = None

    async def get_secret(self, path: str, key: str = None) -> Optional[Any]:
        """
        Get a secret from OpenBAO.
        
        Args:
            path: Secret path (e.g., "data/open-notebook/api-keys")
            key: Specific key to retrieve (optional, returns whole secret if None)
        
        Returns:
            Secret value or None if not found
        """
        cache_key = f"{path}:{key}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            import httpx
            
            url = f"{self.config.addr}/v1/{self.config.mount_point}/data/{path}"
            headers = {
                "X-Vault-Token": self.config.token or os.getenv("VAULT_TOKEN", ""),
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                resp = await client.get(url, headers=headers)
                
                if resp.status_code == 404:
                    logger.warning(f"Secret not found: {path}")
                    return None
                
                if resp.status_code != 200:
                    logger.error(f"OpenBAO error: {resp.status_code} - {resp.text}")
                    return None
                
                data = resp.json()
                secret_data = data.get("data", {}).get("data", {})
                
                if key:
                    value = secret_data.get(key)
                    self._cache[cache_key] = value
                    return value
                
                # Return all keys
                self._cache[cache_key] = secret_data
                return secret_data
                
        except Exception as e:
            logger.error(f"Failed to get secret from OpenBAO: {e}")
            return None

    async def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get an API key for a specific provider.
        
        Args:
            provider: Provider name (openai, anthropic, google, etc.)
        
        Returns:
            API key or None
        """
        return await self.get_secret(f"data/open-notebook/api-keys", provider)

    async def get_database_creds(self) -> dict:
        """Get database credentials."""
        return await self.get_secret("data/open-notebook/database") or {}

    async def get_smtp_config(self) -> dict:
        """Get SMTP configuration."""
        return await self.get_secret("data/open-notebook/smtp") or {}

    async def get_messaging_config(self) -> dict:
        """Get messaging platform configs (Slack, Twilio, Discord)."""
        return await self.get_secret("data/open-notebook/messaging") or {}

    async def get_oidc_config(self) -> dict:
        """Get OIDC/SSO configuration."""
        return await self.get_secret("data/open-notebook/oidc") or {}

    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()


# =============================================================================
# Integration with FastAPI
# =============================================================================


async def init_openbao(app, config: Optional[OpenBAOConfig] = None):
    """Initialize OpenBAO client and attach to app state."""
    secrets = OpenBAOSecrets(config)
    
    # Test connection
    test = await secrets.get_secret("data/open-notebook/test")
    if test is not None or config is None:
        logger.info("OpenBAO client initialized")
    
    return secrets


# =============================================================================
# Usage Examples
# =============================================================================

"""
Environment variables needed:
- OPENBAO_ADDR=http://secrets.unboxd.cloud:8200 (or internal IP)
- OPENBAO_TOKEN=your-token
- VAULT_TOKEN=alternative token env var

Secret paths in OpenBAO:
- secret/data/open-notebook/api-keys    - AI provider API keys
- secret/data/open-notebook/database    - Database credentials
- secret/data/open-notebook/smtp        - Email/SMTP config
- secret/data/open-notebook/messaging   - Slack, Twilio, Discord
- secret/data/open-notebook/oidc        - SSO config
- secret/data/open-notebook/app         - General app config
"""


__all__ = [
    "OpenBAOConfig",
    "OpenBAOSecrets",
    "init_openbao",
]