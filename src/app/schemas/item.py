"""Schemas for Item resource requests and responses."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Request Schemas


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: str | None = Field(None, max_length=1000, description="Item description")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


class ItemUpdate(BaseModel):
    """Schema for updating an existing item."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Item name")
    description: str | None = Field(None, max_length=1000, description="Item description")
    status: Literal["active", "inactive", "archived"] | None = Field(None, description="Item status")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")


# Response Schemas


class ItemResponse(BaseModel):
    """Schema for item in API responses."""

    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str | None = Field(None, description="Item description")
    status: Literal["active", "inactive", "archived"] = Field(..., description="Item status")
    metadata: dict[str, str] | None = Field(None, description="Additional metadata")
    organization_id: str = Field(..., description="Organization ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Created by user ID")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: str = Field(..., description="Updated by user ID")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ItemListResponse(BaseModel):
    """Schema for list of items (non-paginated)."""

    items: list[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
