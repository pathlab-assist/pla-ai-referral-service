"""JWT authentication middleware."""
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.core.security import JWTValidator, extract_bearer_token

logger = get_logger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""

    # Paths that don't require authentication
    EXCLUDED_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app: Any, jwt_validator: JWTValidator) -> None:
        """Initialize middleware.

        Args:
            app: FastAPI application
            jwt_validator: JWT validator instance
        """
        super().__init__(app)
        self.jwt_validator = jwt_validator

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and validate JWT.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response from endpoint

        Raises:
            UnauthorizedError: If authentication fails
        """
        # Skip authentication for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        try:
            # Extract and validate token
            authorization = request.headers.get("Authorization")
            token = extract_bearer_token(authorization)
            claims = await self.jwt_validator.validate_token(token)

            # Extract standard claims
            request.state.user_id = claims.get("sub")
            request.state.organization_id = claims.get("organization_id") or claims.get("org_id")
            request.state.roles = claims.get("roles", [])
            request.state.email = claims.get("email")

            # Validate required claims
            if not request.state.user_id:
                raise UnauthorizedError("Token missing 'sub' claim")

            if not request.state.organization_id:
                raise UnauthorizedError("Token missing 'organization_id' claim")

            logger.debug(
                "Request authenticated",
                user_id=request.state.user_id,
                organization_id=request.state.organization_id,
            )

            return await call_next(request)

        except UnauthorizedError:
            raise
        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            raise UnauthorizedError("Authentication failed") from e


