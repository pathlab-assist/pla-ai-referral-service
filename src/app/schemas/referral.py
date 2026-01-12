"""Referral scanning request and response schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PatientInfo(BaseModel):
    """Patient information extracted from referral."""

    model_config = ConfigDict(populate_by_name=True)

    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    date_of_birth: str | None = Field(
        None, alias="dateOfBirth", description="Date in YYYY-MM-DD format"
    )
    sex: Literal["M", "F", "U"] | None = Field(None, description="M=Male, F=Female, U=Unknown")
    medicare_number: str | None = Field(None, alias="medicareNumber")
    address: str | None = None


class DoctorInfo(BaseModel):
    """Referring doctor information extracted from referral."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    provider_number: str | None = Field(None, alias="providerNumber")
    practice: str | None = None
    phone: str | None = None
    address: str | None = None


class MatchedTest(BaseModel):
    """Test matched to catalog with confidence score."""

    model_config = ConfigDict(populate_by_name=True)

    original: str = Field(..., description="Original test name from referral")
    matched: str = Field(..., description="Matched test display name from catalog")
    test_id: str = Field(..., alias="testId", description="Test identifier in catalog")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)"
    )


class ConfidenceScores(BaseModel):
    """Confidence scores for each extraction category."""

    patient: float = Field(..., ge=0.0, le=1.0, description="Patient data confidence")
    doctor: float = Field(..., ge=0.0, le=1.0, description="Doctor data confidence")
    tests: float = Field(..., ge=0.0, le=1.0, description="Test identification confidence")
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")


class ReferralData(BaseModel):
    """Extracted referral data."""

    model_config = ConfigDict(populate_by_name=True)

    patient: PatientInfo
    doctor: DoctorInfo
    tests: list[str] = Field(default_factory=list, description="Raw test names extracted")
    matched_tests: list[MatchedTest] = Field(
        default_factory=list,
        alias="matchedTests",
        description="Tests matched to catalog",
    )
    clinical_notes: str | None = Field(None, alias="clinicalNotes")
    urgent: bool = False
    collection_date: str | None = Field(
        None, alias="collectionDate", description="Preferred collection date if mentioned"
    )
    confidence: ConfidenceScores


class ScanResponse(BaseModel):
    """Response from referral scan endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    data: ReferralData
    processing_time_ms: int | None = Field(None, alias="processingTimeMs")
    timestamp: datetime


class ScanErrorResponse(BaseModel):
    """Error response from referral scan endpoint."""

    success: bool = False
    error: str
    timestamp: datetime
