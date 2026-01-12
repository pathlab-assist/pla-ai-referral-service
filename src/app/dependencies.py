"""FastAPI dependency injection."""
from fastapi import Request

from app.config import settings
from app.core.exceptions import UnauthorizedError


class AuthContext:
    """Authentication context from JWT."""

    def __init__(self, user_id: str, organization_id: str, roles: list[str]) -> None:
        """Initialize auth context.

        Args:
            user_id: User ID from JWT
            organization_id: Organization ID from JWT
            roles: User roles from JWT
        """
        self.user_id = user_id
        self.organization_id = organization_id
        self.roles = roles


# Authentication dependencies


def get_current_user(request: Request) -> AuthContext:
    """Get current authenticated user from request state.

    Args:
        request: FastAPI request

    Returns:
        AuthContext with user info

    Raises:
        UnauthorizedError: If JWT auth is enabled but user not authenticated
    """
    if settings.jwt_enabled:
        # JWT middleware should have set these
        user_id = getattr(request.state, "user_id", None)
        organization_id = getattr(request.state, "organization_id", None)
        roles = getattr(request.state, "roles", [])

        if not user_id or not organization_id:
            raise UnauthorizedError("Authentication required")

        return AuthContext(
            user_id=user_id,
            organization_id=organization_id,
            roles=roles,
        )
    else:
        # JWT disabled - use mock values for development
        # TODO: Remove in production or make configurable
        return AuthContext(
            user_id="dev-user",
            organization_id="dev-org",
            roles=["admin"],
        )
