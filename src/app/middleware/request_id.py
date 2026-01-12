"""Request ID middleware for tracking requests."""
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate request IDs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and add request ID.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response with X-Request-ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Bind to structlog context
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Store in request state for handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        # Clear context
        structlog.contextvars.clear_contextvars()

        return response
