"""FastAPI dependency injection."""
from typing import Annotated

from fastapi import Depends, Request

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.repositories.item import ItemRepository
from app.routers.item import AuthContext
from app.services.item import ItemService

# Repository dependencies


def get_item_repository() -> ItemRepository:
    """Get Item repository instance.

    Returns:
        ItemRepository instance
    """
    table_name = f"{settings.dynamodb_table_prefix}items"
    return ItemRepository(
        table_name=table_name,
        aws_region=settings.aws_region,
        aws_endpoint_url=settings.aws_endpoint_url,
    )


# Service dependencies


def get_item_service(
    repository: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ItemService:
    """Get Item service instance.

    Args:
        repository: Item repository

    Returns:
        ItemService instance
    """
    return ItemService(repository=repository)


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
