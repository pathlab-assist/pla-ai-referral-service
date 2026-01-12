"""Common schemas used across the application."""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# Pagination


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        """Create a paginated response.

        Args:
            items: List of items for the current page
            total: Total number of items
            page: Current page number
            page_size: Number of items per page

        Returns:
            Paginated response
        """
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# Health


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current server timestamp")
    service: str | None = Field(None, description="Service name")
    version: str | None = Field(None, description="Service version")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual dependency checks")
    timestamp: datetime = Field(..., description="Current server timestamp")


# Errors


class ErrorDetail(BaseModel):
    """Detail about a specific error."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type or title")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Error timestamp")
