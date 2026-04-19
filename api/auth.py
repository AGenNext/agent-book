from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

from open_notebook.utils.encryption import get_secret_from_env


class PasswordAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check password authentication for all API requests.
    Always active with default password if OPEN_NOTEBOOK_PASSWORD is not set.
    Supports Docker secrets via OPEN_NOTEBOOK_PASSWORD_FILE.
    """

    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip authentication if no password is set
        if not self.password:
            return await call_next(request)

        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip authentication for CORS preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Expected format: "Bearer {password}"
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check password
        if credentials != self.password:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid password"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Password is correct, proceed with the request
        response = await call_next(request)
        return response


# OIDC/OAuth2 Authentication Router
oidc_router = APIRouter(prefix="/auth", tags=["authentication"])


class OIDCConfig:
    """OIDC/OAuth2 configuration from environment variables."""

    def __init__(self):
        self.issuer = get_secret_from_env("OIDC_ISSUER")
        self.client_id = get_secret_from_env("OIDC_CLIENT_ID")
        self.client_secret = get_secret_from_env("OIDC_CLIENT_SECRET")
        self.callback_url = get_secret_from_env("OIDC_CALLBACK_URL")
        self.scopes = get_secret_from_env("OIDC_SCOPES", "openid,profile,email")

        # Google OAuth
        self.google_client_id = get_secret_from_env("GOOGLE_CLIENT_ID")
        self.google_client_secret = get_secret_from_env("GOOGLE_CLIENT_SECRET")

        # GitHub OAuth
        self.github_client_id = get_secret_from_env("GITHUB_CLIENT_ID")
        self.github_client_secret = get_secret_from_env("GITHUB_CLIENT_SECRET")

        # Microsoft Azure AD
        self.microsoft_client_id = get_secret_from_env("MICROSOFT_CLIENT_ID")
        self.microsoft_client_secret = get_secret_from_env("MICROSOFT_CLIENT_SECRET")
        self.microsoft_tenant_id = get_secret_from_env("MICROSOFT_TENANT_ID")

    @property
    def is_configured(self) -> bool:
        """Check if any OIDC provider is configured."""
        return bool(
            self.issuer
            or self.google_client_id
            or self.github_client_id
            or self.microsoft_client_id
        )

    def get_oidc_config(self) -> Optional[dict]:
        """Get generic OIDC configuration."""
        if not self.issuer or not self.client_id:
            return None
        return {
            "issuer": self.issuer,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "callback_url": self.callback_url,
            "scopes": self.scopes,
        }

    def get_google_config(self) -> Optional[dict]:
        """Get Google OAuth configuration."""
        if not self.google_client_id:
            return None
        return {
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
        }

    def get_github_config(self) -> Optional[dict]:
        """Get GitHub OAuth configuration."""
        if not self.github_client_id:
            return None
        return {
            "client_id": self.github_client_id,
            "client_secret": self.github_client_secret,
        }

    def get_microsoft_config(self) -> Optional[dict]:
        """Get Microsoft Azure AD configuration."""
        if not self.microsoft_client_id:
            return None
        return {
            "client_id": self.microsoft_client_id,
            "client_secret": self.microsoft_client_secret,
            "tenant_id": self.microsoft_tenant_id,
        }


# Global OIDC configuration instance
oidc_config = OIDCConfig()


@oidc_router.get("/login")
async def oidc_login(provider: str = "oidc"):
    """
    Initiate OIDC/OAuth2 login flow.
    
    Args:
        provider: OAuth provider (oidc, google, github, microsoft)
    """
    config = oidc_config.get_oidc_config() if provider == "oidc" else None

    if provider == "google":
        config = oidc_config.get_google_config()
        if config:
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={oidc_config.callback_url or 'http://localhost:5055/api/auth/callback'}&"
                f"response_type=code&"
                f"scope=openid%20profile%20email&"
                f"state=google"
            )
            return RedirectResponse(url=auth_url)

    elif provider == "github":
        config = oidc_config.get_github_config()
        if config:
            auth_url = (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={oidc_config.callback_url or 'http://localhost:5055/api/auth/callback'}&"
                f"scope=read:user&"
                f"state=github"
            )
            return RedirectResponse(url=auth_url)

    elif provider == "microsoft":
        config = oidc_config.get_microsoft_config()
        if config and config.get("tenant_id"):
            auth_url = (
                f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/authorize?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={oidc_config.callback_url or 'http://localhost:5055/api/auth/callback'}&"
                f"response_type=code&"
                f"scope=openid%20profile%20email&"
                f"state=microsoft"
            )
            return RedirectResponse(url=auth_url)

    elif provider == "oidc" and config:
        auth_url = (
            f"{config['issuer']}/authorize?"
            f"client_id={config['client_id']}&"
            f"redirect_uri={config['callback_url']}&"
            f"response_type=code&"
            f"scope={config['scopes']}&"
            f"state=oidc"
        )
        return RedirectResponse(url=auth_url)

    raise HTTPException(
        status_code=400,
        detail=f"OAuth provider '{provider}' not configured",
    )


@oidc_router.get("/callback")
async def oidc_callback(code: str, state: str = "oidc"):
    """
    OIDC/OAuth2 callback handler.
    
    Args:
        code: Authorization code from provider
        state: OAuth state parameter
    """
    # In production, exchange code for tokens and create session
    # This is a stub implementation
    logger.info(f"OIDC callback received with state: {state}")

    # TODO: Implement token exchange and session creation
    return JSONResponse(
        status_code=501,
        content={"detail": "OIDC callback not fully implemented"},
    )


@oidc_router.get("/logout")
async def oidc_logout():
    """Logout and clear session."""
    return JSONResponse(
        status_code=501,
        content={"detail": "OIDC logout not fully implemented"},
    )


@oidc_router.get("/providers")
async def oidc_providers():
    """List available OAuth providers."""
    providers = []
    if oidc_config.get_oidc_config():
        providers.append("oidc")
    if oidc_config.get_google_config():
        providers.append("google")
    if oidc_config.get_github_config():
        providers.append("github")
    if oidc_config.get_microsoft_config():
        providers.append("microsoft")

    return {
        "providers": providers,
        "configured": bool(providers),
    }


# Optional: HTTPBearer security scheme for OpenAPI documentation
security = HTTPBearer(auto_error=False)


def check_api_password(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    """
    Utility function to check API password.
    Can be used as a dependency in individual routes if needed.
    Supports Docker secrets via OPEN_NOTEBOOK_PASSWORD_FILE.
    Returns True without checking credentials if OPEN_NOTEBOOK_PASSWORD is not configured.
    Raises 401 if credentials are missing or don't match the configured password.
    """
    password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")

    # No password configured - skip authentication
    if not password:
        return True

    # No credentials provided
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check password
    if credentials.credentials != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
