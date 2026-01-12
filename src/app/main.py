"""FastAPI application entry point."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, setup_logging
from app.core.security import JWKSClient, JWTValidator
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.routers import health, item
from app.schemas.common import ErrorDetail, ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events.

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup
    setup_logging(
        service_name=settings.service_name,
        environment=settings.environment,
        log_level=settings.log_level,
        log_json=settings.log_json,
    )
    logger = get_logger(__name__)
    logger.info(
        "Application starting",
        service=settings.service_name,
        environment=settings.environment,
    )

    yield

    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.service_name,
    version="0.1.0",
    description="Production-ready Python/FastAPI microservice template",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Get logger
logger = get_logger(__name__)


# Exception handlers


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Args:
        request: FastAPI request
        exc: Application exception

    Returns:
        JSON error response
    """
    logger.warning(
        "Application exception",
        error=exc.detail,
        status_code=exc.status_code,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON error response
    """
    logger.warning("Validation error", path=request.url.path, errors=exc.errors())

    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            code=error["type"],
        )
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details=details,
            request_id=getattr(request.state, "request_id", None),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(
        "Unexpected error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=getattr(request.state, "request_id", None),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


# Middleware (order matters - applied in reverse)

# CORS
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

# JWT Authentication
if settings.jwt_enabled:
    jwks_client = JWKSClient(settings.jwt_jwks_url)
    jwt_validator = JWTValidator(
        jwks_client=jwks_client,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    app.add_middleware(JWTAuthMiddleware, jwt_validator=jwt_validator)

# Logging
app.add_middleware(LoggingMiddleware)

# Request ID (should be first, applied last)
app.add_middleware(RequestIDMiddleware)


# Routers
app.include_router(health.router)
app.include_router(item.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint redirect to docs.

    Returns:
        Redirect message
    """
    return {
        "message": f"Welcome to {settings.service_name}",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
