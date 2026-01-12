"""Security utilities for JWT authentication."""
import time
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.backends import RSAKey

from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger

logger = get_logger(__name__)


class JWKSClient:
    """Client for fetching and caching JWKS (JSON Web Key Set)."""

    def __init__(self, jwks_url: str, cache_ttl: int = 3600) -> None:
        """Initialize JWKS client.

        Args:
            jwks_url: URL to fetch JWKS from
            cache_ttl: Time to live for cached keys in seconds
        """
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._keys: dict[str, RSAKey] = {}  # type: ignore[valid-type]
        self._cache_time: float = 0

    async def get_signing_key(self, kid: str) -> RSAKey:  # type: ignore[valid-type]
        """Get signing key by key ID.

        Args:
            kid: Key ID from JWT header

        Returns:
            RSA public key for verification

        Raises:
            UnauthorizedError: If key is not found
        """
        # Refresh cache if expired
        if time.time() - self._cache_time > self.cache_ttl:
            await self._refresh_keys()

        if kid not in self._keys:
            logger.warning("Key ID not found in JWKS", kid=kid)
            raise UnauthorizedError("Invalid token: key not found")

        return self._keys[kid]

    async def _refresh_keys(self) -> None:
        """Fetch and cache JWKS from the URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()

            self._keys = {key["kid"]: RSAKey(key, "RS256") for key in jwks.get("keys", [])}  # type: ignore[misc]
            self._cache_time = time.time()
            logger.info("JWKS refreshed", num_keys=len(self._keys))

        except Exception as e:
            logger.error("Failed to fetch JWKS", error=str(e))
            raise UnauthorizedError("Failed to fetch signing keys") from e


class JWTValidator:
    """JWT token validator."""

    def __init__(self, jwks_client: JWKSClient, issuer: str, audience: str) -> None:
        """Initialize JWT validator.

        Args:
            jwks_client: JWKS client for fetching signing keys
            issuer: Expected token issuer
            audience: Expected token audience
        """
        self.jwks_client = jwks_client
        self.issuer = issuer
        self.audience = audience

    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token claims

        Raises:
            UnauthorizedError: If token is invalid
        """
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            if not kid:
                raise UnauthorizedError("Invalid token: missing key ID")

            # Get signing key
            signing_key = await self.jwks_client.get_signing_key(kid)

            # Verify and decode token
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
            )

            logger.debug("Token validated", user_id=claims.get("sub"))
            return claims  # type: ignore[no-any-return]

        except JWTError as e:
            logger.warning("JWT validation failed", error=str(e))
            raise UnauthorizedError("Invalid token") from e
        except Exception as e:
            logger.error("Unexpected error during token validation", error=str(e))
            raise UnauthorizedError("Token validation failed") from e


def extract_bearer_token(authorization: str | None) -> str:
    """Extract bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Bearer token

    Raises:
        UnauthorizedError: If header is missing or invalid
    """
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format")

    return parts[1]
