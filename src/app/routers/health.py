"""Health check endpoints."""
from datetime import UTC, datetime

from fastapi import APIRouter, status

from app.config import settings
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint to verify service is running",
)
async def health_check() -> HealthResponse:
    """Check if the service is healthy.

    Returns:
        Health status response
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        service=settings.service_name,
        version="0.1.0",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Readiness check to verify service dependencies are available",
)
async def readiness_check() -> ReadinessResponse:
    """Check if the service is ready to handle requests.

    This should check all critical dependencies (database, cache, etc.)

    Returns:
        Readiness status response
    """
    checks: dict[str, bool] = {}

    # TODO: Add actual dependency checks
    # Example:
    # checks["database"] = await check_database()
    # checks["cache"] = await check_cache()

    # For now, assume all checks pass
    checks["example"] = True

    all_ready = all(checks.values())

    return ReadinessResponse(
        ready=all_ready,
        checks=checks,
        timestamp=datetime.now(UTC),
    )
