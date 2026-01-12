"""Application configuration using Pydantic Settings."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service
    service_name: str = "template-service"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

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

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True


# Global settings instance
settings = Settings()
