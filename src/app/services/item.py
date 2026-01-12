"""Item service containing business logic."""
from uuid import uuid4

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.item import Item
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate

logger = get_logger(__name__)


class ItemService:
    """Service layer for Item business logic."""

    def __init__(self, repository: ItemRepository) -> None:
        """Initialize service.

        Args:
            repository: Item repository
        """
        self.repository = repository

    async def get_item(self, item_id: str, organization_id: str) -> Item:
        """Get an item by ID.

        Args:
            item_id: Item ID
            organization_id: Organization ID

        Returns:
            Item entity

        Raises:
            NotFoundError: If item not found
        """
        item = await self.repository.get(item_id, organization_id)
        if not item:
            raise NotFoundError("Item", item_id)

        return item

    async def list_items(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Item], int]:
        """List items for an organization.

        Args:
            organization_id: Organization ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status (optional)

        Returns:
            Tuple of (items list, total count)
        """
        offset = (page - 1) * page_size

        items = await self.repository.list(
            organization_id=organization_id,
            limit=page_size,
            offset=offset,
            status=status,
        )

        total = await self.repository.count(organization_id=organization_id, status=status)

        return items, total

    async def create_item(
        self,
        data: ItemCreate,
        organization_id: str,
        user_id: str,
    ) -> Item:
        """Create a new item.

        Args:
            data: Item creation data
            organization_id: Organization ID
            user_id: User ID creating the item

        Returns:
            Created item

        Raises:
            ValidationError: If validation fails
        """
        # Business validation
        if data.name and len(data.name.strip()) == 0:
            raise ValidationError("Item name cannot be empty", field="name")

        # Create entity
        item = Item(
            id=str(uuid4()),
            name=data.name,
            description=data.description,
            status="active",
            metadata=data.metadata,
            organization_id=organization_id,
            created_by=user_id,
            updated_by=user_id,
        )

        # Persist
        created_item = await self.repository.create(item)

        logger.info("Item created", item_id=created_item.id, name=created_item.name)
        return created_item

    async def update_item(
        self,
        item_id: str,
        data: ItemUpdate,
        organization_id: str,
        user_id: str,
    ) -> Item:
        """Update an existing item.

        Args:
            item_id: Item ID
            data: Update data
            organization_id: Organization ID
            user_id: User ID updating the item

        Returns:
            Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If validation fails
        """
        # Get existing item
        item = await self.get_item(item_id, organization_id)

        # Apply updates
        if data.name is not None:
            if len(data.name.strip()) == 0:
                raise ValidationError("Item name cannot be empty", field="name")
            item.name = data.name

        if data.description is not None:
            item.description = data.description

        if data.status is not None:
            item.status = data.status

        if data.metadata is not None:
            item.metadata = data.metadata

        # Update audit fields
        item.update_audit_fields(user_id)

        # Persist
        updated_item = await self.repository.update(item)

        logger.info("Item updated", item_id=updated_item.id)
        return updated_item

    async def delete_item(self, item_id: str, organization_id: str) -> None:
        """Delete an item.

        Args:
            item_id: Item ID
            organization_id: Organization ID

        Raises:
            NotFoundError: If item not found
        """
        deleted = await self.repository.delete(item_id, organization_id)
        if not deleted:
            raise NotFoundError("Item", item_id)

        logger.info("Item deleted", item_id=item_id)

    async def activate_item(self, item_id: str, organization_id: str, user_id: str) -> Item:
        """Activate an item.

        Args:
            item_id: Item ID
            organization_id: Organization ID
            user_id: User ID performing the action

        Returns:
            Updated item
        """
        item = await self.get_item(item_id, organization_id)
        item.activate()
        item.update_audit_fields(user_id)

        updated_item = await self.repository.update(item)
        logger.info("Item activated", item_id=item_id)
        return updated_item

    async def deactivate_item(self, item_id: str, organization_id: str, user_id: str) -> Item:
        """Deactivate an item.

        Args:
            item_id: Item ID
            organization_id: Organization ID
            user_id: User ID performing the action

        Returns:
            Updated item
        """
        item = await self.get_item(item_id, organization_id)
        item.deactivate()
        item.update_audit_fields(user_id)

        updated_item = await self.repository.update(item)
        logger.info("Item deactivated", item_id=item_id)
        return updated_item
