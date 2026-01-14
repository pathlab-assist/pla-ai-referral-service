"""Application configuration using Pydantic Settings."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    service_name: str = "ai-referral-service"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8011

    # AWS
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None  # For LocalStack
    dynamodb_table_prefix: str = "pla-dev-"

    # JWT
    jwt_enabled: bool = False
    jwt_jwks_url: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""

    # CORS
    cors_enabled: bool = True
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    max_image_size_mb: float = 10.0  # Allow decimal precision for size limits
    scan_timeout_seconds: int = 120

    # External Services
    test_catalog_service_url: str = "http://localhost:8003"

    # OAuth Client Credentials (for service-to-service auth)
    oauth_enabled: bool = True
    oauth_token_url: str = "http://pathlab-assist-auth:8080/v1/oauth/token"
    oauth_client_id: str = "ai-referral-service"
    oauth_client_secret: str = "ai-referral-secret"
    oauth_scopes: str = "system:catalog:read system/Test.read"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True  # Default: JSON logs (production-ready)


# Global settings instance
settings = Settings()
