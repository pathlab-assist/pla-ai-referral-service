"""Request logging middleware."""
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process and log request/response.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response from endpoint
        """
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) if request.url.query else None,
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise
