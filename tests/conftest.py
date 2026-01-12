"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture
def sample_organization_id() -> str:
    """Sample organization ID for testing.

    Returns:
        Organization ID
    """
    return "org-123"


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for testing.

    Returns:
        User ID
    """
    return "user-456"
