"""Example Item entity model."""
from typing import Literal

from pydantic import Field

from app.models.base import BaseEntity


class Item(BaseEntity):
    """Example business entity representing an item.

    This is a template example showing how to create domain models.
    Replace this with your actual business entities.
    """

    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: str | None = Field(None, max_length=1000, description="Item description")
    status: Literal["active", "inactive", "archived"] = Field(
        default="active", description="Item status"
    )
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")

    def activate(self) -> None:
        """Activate the item."""
        self.status = "active"

    def deactivate(self) -> None:
        """Deactivate the item."""
        self.status = "inactive"

    def archive(self) -> None:
        """Archive the item."""
        self.status = "archived"

    def is_active(self) -> bool:
        """Check if item is active.

        Returns:
            True if item is active
        """
        return self.status == "active"
