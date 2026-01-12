"""Item repository implementation using DynamoDB."""
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.item import Item
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ItemRepository(BaseRepository[Item]):
    """DynamoDB-based repository for Items.

    Table Schema:
        PK: ORG#{organization_id}
        SK: ITEM#{item_id}
        GSI1PK: ORG#{organization_id}
        GSI1SK: STATUS#{status}#CREATED#{created_at}
    """

    def __init__(
        self,
        table_name: str,
        aws_region: str,
        aws_endpoint_url: str | None = None,
    ) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name
            aws_region: AWS region
            aws_endpoint_url: AWS endpoint URL (for LocalStack)
        """
        self.table_name = table_name

        # Create DynamoDB resource
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=aws_region,
            endpoint_url=aws_endpoint_url,
        )
        self.table = dynamodb.Table(table_name)

    def _to_item_dict(self, item: Item) -> dict[str, Any]:
        """Convert Item entity to DynamoDB item.

        Args:
            item: Item entity

        Returns:
            DynamoDB item dictionary
        """
        return {
            "PK": f"ORG#{item.organization_id}",
            "SK": f"ITEM#{item.id}",
            "GSI1PK": f"ORG#{item.organization_id}",
            "GSI1SK": f"STATUS#{item.status}#CREATED#{item.created_at.isoformat()}",
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "status": item.status,
            "metadata": item.metadata,
            "organization_id": item.organization_id,
            "created_at": item.created_at.isoformat(),
            "created_by": item.created_by,
            "updated_at": item.updated_at.isoformat(),
            "updated_by": item.updated_by,
        }

    def _from_item_dict(self, item_dict: dict[str, Any]) -> Item:
        """Convert DynamoDB item to Item entity.

        Args:
            item_dict: DynamoDB item dictionary

        Returns:
            Item entity
        """
        return Item(
            id=item_dict["id"],
            name=item_dict["name"],
            description=item_dict.get("description"),
            status=item_dict["status"],
            metadata=item_dict.get("metadata"),
            organization_id=item_dict["organization_id"],
            created_at=item_dict["created_at"],
            created_by=item_dict["created_by"],
            updated_at=item_dict["updated_at"],
            updated_by=item_dict["updated_by"],
        )

    async def get(self, id: str, organization_id: str) -> Item | None:
        """Get an item by ID."""
        try:
            response = self.table.get_item(
                Key={"PK": f"ORG#{organization_id}", "SK": f"ITEM#{id}"}
            )

            if "Item" not in response:
                return None

            return self._from_item_dict(response["Item"])

        except Exception as e:
            logger.error("Failed to get item", item_id=id, organization_id=organization_id, error=str(e))
            raise

    async def list(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        **filters: Any,
    ) -> list[Item]:
        """List items for an organization."""
        try:
            # Use GSI1 to query by organization and optionally filter by status
            key_condition = Key("GSI1PK").eq(f"ORG#{organization_id}")

            if status:
                key_condition &= Key("GSI1SK").begins_with(f"STATUS#{status}#")  # type: ignore[assignment]

            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=key_condition,
                Limit=limit + offset,  # Fetch extra to handle offset
            )

            items = response.get("Items", [])

            # Apply offset
            items = items[offset:offset + limit]

            return [self._from_item_dict(item) for item in items]

        except Exception as e:
            logger.error("Failed to list items", organization_id=organization_id, error=str(e))
            raise

    async def count(self, organization_id: str, status: str | None = None, **filters: Any) -> int:
        """Count items for an organization."""
        try:
            key_condition = Key("GSI1PK").eq(f"ORG#{organization_id}")

            if status:
                key_condition &= Key("GSI1SK").begins_with(f"STATUS#{status}#")  # type: ignore[assignment]

            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression=key_condition,
                Select="COUNT",
            )

            return response.get("Count", 0)

        except Exception as e:
            logger.error("Failed to count items", organization_id=organization_id, error=str(e))
            raise

    async def create(self, item: Item) -> Item:
        """Create a new item."""
        try:
            item_dict = self._to_item_dict(item)

            # Use condition to prevent overwriting existing items
            self.table.put_item(
                Item=item_dict,
                ConditionExpression="attribute_not_exists(PK)",
            )

            logger.info("Item created", item_id=item.id, organization_id=item.organization_id)
            return item

        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            raise ConflictError(f"Item with id '{item.id}' already exists") from None
        except Exception as e:
            logger.error("Failed to create item", item_id=item.id, error=str(e))
            raise

    async def update(self, item: Item) -> Item:
        """Update an existing item."""
        try:
            # Check if item exists
            existing = await self.get(item.id, item.organization_id)
            if not existing:
                raise NotFoundError("Item", item.id)

            item_dict = self._to_item_dict(item)

            self.table.put_item(Item=item_dict)

            logger.info("Item updated", item_id=item.id, organization_id=item.organization_id)
            return item

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to update item", item_id=item.id, error=str(e))
            raise

    async def delete(self, id: str, organization_id: str) -> bool:
        """Delete an item."""
        try:
            # Check if item exists first
            existing = await self.get(id, organization_id)
            if not existing:
                return False

            self.table.delete_item(Key={"PK": f"ORG#{organization_id}", "SK": f"ITEM#{id}"})

            logger.info("Item deleted", item_id=id, organization_id=organization_id)
            return True

        except Exception as e:
            logger.error("Failed to delete item", item_id=id, error=str(e))
            raise
