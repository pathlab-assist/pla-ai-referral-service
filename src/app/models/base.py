"""Base models and mixins for business entities."""
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TenantMixin(BaseModel):
    """Mixin for multi-tenant models."""

    organization_id: str = Field(..., description="Organization ID for multi-tenancy")


class AuditMixin(BaseModel):
    """Mixin for audit trail fields (NPAAC compliance)."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when record was created",
    )
    created_by: str = Field(..., description="User ID who created the record")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when record was last updated",
    )
    updated_by: str = Field(..., description="User ID who last updated the record")

    def update_audit_fields(self, user_id: str) -> None:
        """Update audit fields for modifications.

        Args:
            user_id: ID of user making the update
        """
        self.updated_at = datetime.now(UTC)
        self.updated_by = user_id


class BaseEntity(TenantMixin, AuditMixin):
    """Base class for all business entities with multi-tenancy and audit support."""

    id: str = Field(..., description="Unique identifier")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
