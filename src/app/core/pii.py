"""PII (Personally Identifiable Information) masking utilities."""
import re
from typing import Any


def mask_medicare_number(medicare: str) -> str:
    """Mask a Medicare number for logging/display.

    Args:
        medicare: Medicare number (10 digits)

    Returns:
        Masked Medicare number (e.g., "2***5")
    """
    if not medicare or len(medicare) < 4:
        return "[MASKED]"

    # Show first and last digit only
    return f"{medicare[0]}***{medicare[-1]}"


def mask_email(email: str) -> str:
    """Mask an email address for logging/display.

    Args:
        email: Email address

    Returns:
        Masked email (e.g., "j***@example.com")
    """
    if not email or "@" not in email:
        return "[MASKED]"

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number for logging/display.

    Args:
        phone: Phone number

    Returns:
        Masked phone number (e.g., "***1234")
    """
    # Remove non-digit characters
    digits = re.sub(r"\D", "", phone)

    if len(digits) < 4:
        return "[MASKED]"

    # Show last 4 digits only
    return f"***{digits[-4:]}"


def sanitize_for_logging(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a dictionary for safe logging by masking PII fields.

    Args:
        data: Dictionary that may contain PII

    Returns:
        Dictionary with PII fields masked
    """
    pii_fields = {
        "medicare_number": mask_medicare_number,
        "email": mask_email,
        "phone": mask_phone,
        "mobile": mask_phone,
        "date_of_birth": lambda x: "[MASKED]",
        "password": lambda x: "[MASKED]",
        "token": lambda x: "[MASKED]",
        "api_key": lambda x: "[MASKED]",
    }

    sanitized = data.copy()

    for field, mask_fn in pii_fields.items():
        if field in sanitized and sanitized[field]:
            sanitized[field] = mask_fn(str(sanitized[field]))

    return sanitized
