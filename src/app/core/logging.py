"""Structured logging configuration using structlog."""
import logging
import sys
from typing import Any

import structlog
from structlog.typing import EventDict, WrappedLogger


def mask_pii(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Mask PII fields in log events.

    Args:
        logger: The wrapped logger instance
        method_name: Name of the method being called
        event_dict: The event dictionary

    Returns:
        Event dictionary with PII fields masked
    """
    pii_fields = [
        "medicare_number",
        "date_of_birth",
        "email",
        "phone",
        "mobile",
        "password",
        "token",
        "api_key",
    ]

    for key in pii_fields:
        if key in event_dict:
            event_dict[key] = "[MASKED]"

    # Also check nested dicts
    for _key, value in event_dict.items():
        if isinstance(value, dict):
            for pii_field in pii_fields:
                if pii_field in value:
                    value[pii_field] = "[MASKED]"

    return event_dict


def setup_logging(service_name: str, environment: str, log_level: str, log_json: bool) -> None:
    """Configure structlog for the application.

    Args:
        service_name: Name of the service
        environment: Environment (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_json: Whether to output JSON logs
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Shared processors for all configurations
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        mask_pii,  # Custom PII masking
    ]

    if log_json:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Console output with colors
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bind service context
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment=environment,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
