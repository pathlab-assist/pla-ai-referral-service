"""Test matching request and response schemas."""
from pydantic import BaseModel, Field

from app.schemas.referral import MatchedTest


class TestMatchRequest(BaseModel):
    """Request to match test names to catalog."""

    tests: list[str] = Field(..., min_length=1, description="List of test names to match")


class TestMatchResponse(BaseModel):
    """Response from test matching endpoint."""

    success: bool = True
    data: list[MatchedTest] = Field(
        ..., description="Matched tests with confidence scores"
    )
