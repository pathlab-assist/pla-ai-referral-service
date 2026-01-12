"""Item CRUD endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_item_service
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


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


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create item",
    description="Create a new item within the organization",
)
async def create_item(
    data: ItemCreate,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Create a new item.

    Args:
        data: Item creation data
        auth: Authentication context
        service: Item service

    Returns:
        Created item
    """
    item = await service.create_item(
        data=data,
        organization_id=auth.organization_id,
        user_id=auth.user_id,
    )
    return ItemResponse.model_validate(item)


@router.get(
    "",
    response_model=PaginatedResponse[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List items",
    description="List items for the organization with pagination",
)
async def list_items(
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> PaginatedResponse[ItemResponse]:
    """List items with pagination.

    Args:
        auth: Authentication context
        service: Item service
        pagination: Pagination parameters
        status_filter: Filter by status

    Returns:
        Paginated list of items
    """
    items, total = await service.list_items(
        organization_id=auth.organization_id,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status_filter,
    )

    item_responses = [ItemResponse.model_validate(item) for item in items]

    return PaginatedResponse.create(
        items=item_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get item",
    description="Get a single item by ID",
)
async def get_item(
    item_id: str,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Get an item by ID.

    Args:
        item_id: Item ID
        auth: Authentication context
        service: Item service

    Returns:
        Item details
    """
    item = await service.get_item(item_id, auth.organization_id)
    return ItemResponse.model_validate(item)


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update item",
    description="Update an existing item",
)
async def update_item(
    item_id: str,
    data: ItemUpdate,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Update an item.

    Args:
        item_id: Item ID
        data: Update data
        auth: Authentication context
        service: Item service

    Returns:
        Updated item
    """
    item = await service.update_item(
        item_id=item_id,
        data=data,
        organization_id=auth.organization_id,
        user_id=auth.user_id,
    )
    return ItemResponse.model_validate(item)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an item",
)
async def delete_item(
    item_id: str,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> None:
    """Delete an item.

    Args:
        item_id: Item ID
        auth: Authentication context
        service: Item service
    """
    await service.delete_item(item_id, auth.organization_id)


@router.post(
    "/{item_id}/activate",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate item",
    description="Activate an item",
)
async def activate_item(
    item_id: str,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Activate an item.

    Args:
        item_id: Item ID
        auth: Authentication context
        service: Item service

    Returns:
        Updated item
    """
    item = await service.activate_item(item_id, auth.organization_id, auth.user_id)
    return ItemResponse.model_validate(item)


@router.post(
    "/{item_id}/deactivate",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate item",
    description="Deactivate an item",
)
async def deactivate_item(
    item_id: str,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Deactivate an item.

    Args:
        item_id: Item ID
        auth: Authentication context
        service: Item service

    Returns:
        Updated item
    """
    item = await service.deactivate_item(item_id, auth.organization_id, auth.user_id)
    return ItemResponse.model_validate(item)
