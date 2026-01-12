"""Custom application exceptions."""
from typing import Any


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, detail: str, status_code: int = 500, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            detail: Human-readable error message
            status_code: HTTP status code
            **kwargs: Additional context for the error
        """
        self.detail = detail
        self.status_code = status_code
        self.context = kwargs
        super().__init__(detail)


class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str) -> None:
        """Initialize the exception.

        Args:
            resource: Type of resource (e.g., "Item", "User")
            identifier: Resource identifier
        """
        super().__init__(
            detail=f"{resource} with id '{identifier}' not found",
            status_code=404,
            resource=resource,
            identifier=identifier,
        )


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(self, detail: str, field: str | None = None) -> None:
        """Initialize the exception.

        Args:
            detail: Validation error message
            field: Field that failed validation (optional)
        """
        super().__init__(
            detail=detail,
            status_code=422,
            field=field,
        )


class ConflictError(AppException):
    """Raised when a resource conflict occurs."""

    def __init__(self, detail: str) -> None:
        """Initialize the exception.

        Args:
            detail: Conflict error message
        """
        super().__init__(detail=detail, status_code=409)


class UnauthorizedError(AppException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Unauthorized") -> None:
        """Initialize the exception.

        Args:
            detail: Authentication error message
        """
        super().__init__(detail=detail, status_code=401)


class ForbiddenError(AppException):
    """Raised when authorization fails."""

    def __init__(self, detail: str = "Forbidden") -> None:
        """Initialize the exception.

        Args:
            detail: Authorization error message
        """
        super().__init__(detail=detail, status_code=403)
