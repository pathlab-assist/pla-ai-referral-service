"""Base repository interface."""
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for repositories.

    Provides standard CRUD operations with multi-tenancy support.
    All queries must be scoped by organization_id for tenant isolation.
    """

    @abstractmethod
    async def get(self, id: str, organization_id: str) -> T | None:
        """Get an entity by ID within an organization.

        Args:
            id: Entity ID
            organization_id: Organization ID for multi-tenancy

        Returns:
            Entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def list(
        self,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[T]:
        """List entities for an organization.

        Args:
            organization_id: Organization ID for multi-tenancy
            limit: Maximum number of items to return
            offset: Number of items to skip
            **filters: Additional filter criteria

        Returns:
            List of entities
        """
        ...

    @abstractmethod
    async def count(self, organization_id: str, **filters: Any) -> int:
        """Count entities for an organization.

        Args:
            organization_id: Organization ID for multi-tenancy
            **filters: Filter criteria

        Returns:
            Number of matching entities
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        ...

    @abstractmethod
    async def delete(self, id: str, organization_id: str) -> bool:
        """Delete an entity by ID within an organization.

        Args:
            id: Entity ID
            organization_id: Organization ID for multi-tenancy

        Returns:
            True if deleted, False if not found
        """
        ...
