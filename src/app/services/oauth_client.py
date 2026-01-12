"""OAuth client credentials service for service-to-service authentication."""
import time
from typing import Optional

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OAuthTokenCache:
    """Simple in-memory token cache with expiration."""

    def __init__(self) -> None:
        """Initialize token cache."""
        self._token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> Optional[str]:
        """Get cached token if still valid.

        Returns:
            Token string if valid, None if expired
        """
        if self._token and time.time() < self._expires_at - 60:  # 60s buffer
            return self._token
        return None

    def set_token(self, token: str, expires_in: int) -> None:
        """Cache token with expiration.

        Args:
            token: OAuth access token
            expires_in: Token lifetime in seconds
        """
        self._token = token
        self._expires_at = time.time() + expires_in


class OAuthClient:
    """OAuth client credentials flow for service-to-service auth."""

    def __init__(self) -> None:
        """Initialize OAuth client."""
        self.token_url = settings.oauth_token_url
        self.client_id = settings.oauth_client_id
        self.client_secret = settings.oauth_client_secret
        self.scopes = settings.oauth_scopes
        self.enabled = settings.oauth_enabled
        self._cache = OAuthTokenCache()

    async def get_access_token(self) -> Optional[str]:
        """Get OAuth access token using client credentials flow.

        Returns cached token if valid, otherwise requests new token.

        Returns:
            Access token string, or None if OAuth disabled or request fails
        """
        if not self.enabled:
            logger.debug("OAuth disabled, skipping token retrieval")
            return None

        # Check cache first
        cached_token = self._cache.get_token()
        if cached_token:
            logger.debug("Using cached OAuth token")
            return cached_token

        # Request new token
        try:
            logger.debug(
                "Requesting OAuth token",
                token_url=self.token_url,
                client_id=self.client_id,
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": self.scopes,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )

                if response.status_code != 200:
                    logger.error(
                        "OAuth token request failed",
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return None

                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)

                if not access_token:
                    logger.error("OAuth response missing access_token")
                    return None

                # Cache token
                self._cache.set_token(access_token, expires_in)

                logger.info(
                    "OAuth token retrieved successfully",
                    expires_in=expires_in,
                )

                return access_token

        except httpx.TimeoutException:
            logger.error("OAuth token request timeout")
            return None
        except Exception as e:
            logger.error(
                "OAuth token request error",
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
