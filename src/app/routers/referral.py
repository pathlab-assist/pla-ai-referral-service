"""Referral scanning API endpoints."""
import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.dependencies import AuthContext, get_current_user
from app.schemas.referral import (
    ConfidenceScores,
    ReferralData,
    ScanResponse,
)
from app.schemas.test_match import TestMatchRequest, TestMatchResponse
from app.services.claude_vision import ClaudeVisionService
from app.services.test_matcher import TestMatcherService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/referral", tags=["referral"])


@router.post("/scan", response_model=ScanResponse, response_model_by_alias=True)
async def scan_referral(
    image: Annotated[UploadFile, File(description="Referral image to scan")],
    auth: Annotated[AuthContext, Depends(get_current_user)],
) -> ScanResponse:
    """Scan a referral image and extract structured data.

    Extracts patient information, doctor details, requested tests, and clinical notes
    from a pathology referral form using Claude Vision AI.

    Args:
        image: Uploaded referral image (JPEG, PNG, etc.)
        auth: Authenticated user context from JWT

    Returns:
        ScanResponse with extracted data and confidence scores

    Raises:
        HTTPException: If scan fails or image is invalid
    """
    start_time = time.time()

    # Check if API key is configured
    if not settings.anthropic_api_key:
        logger.error("Anthropic API key not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Claude API key not configured",
        )

    # Validate file exists
    if not image or not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided",
        )

    # Check file size (convert MB to bytes)
    max_size_bytes = settings.max_image_size_mb * 1024 * 1024
    image_bytes = await image.read()

    if len(image_bytes) > max_size_bytes:
        logger.warning(
            "Image too large",
            file_size_mb=len(image_bytes) / 1024 / 1024,
            max_size_mb=settings.max_image_size_mb,
            organization_id=auth.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Maximum size: {settings.max_image_size_mb}MB (Claude Vision API limit: 5MB when base64 encoded)",
        )

    # Determine and validate image type
    image_type = image.content_type or "image/jpeg"

    # Validate content type
    valid_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if image_type not in valid_types:
        logger.warning(
            "Invalid image content type",
            content_type=image_type,
            organization_id=auth.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type: {image_type}. Supported types: JPEG, PNG, GIF, WebP",
        )

    logger.info(
        "Starting referral scan",
        filename=image.filename,
        content_type=image_type,
        file_size_kb=len(image_bytes) // 1024,
        organization_id=auth.organization_id,
        user_id=auth.user_id,
    )

    try:
        # Extract data using Claude Vision
        vision_service = ClaudeVisionService()
        extracted_data = await vision_service.extract_referral_data(
            image_bytes, image_type
        )

        # Check for error in extraction
        if "error" in extracted_data:
            logger.warning(
                "Extraction error",
                error=extracted_data["error"],
                organization_id=auth.organization_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=extracted_data["error"],
            )

        # Fuzzy match tests to catalog if tests were extracted
        matched_tests = []
        if "tests" in extracted_data and extracted_data["tests"]:
            test_matcher = TestMatcherService(organization_id=auth.organization_id)
            matched_tests = await test_matcher.match_tests(extracted_data["tests"])

        # Calculate overall confidence
        confidence_data = extracted_data.get("confidence", {})
        patient_conf = confidence_data.get("patient", 0.0)
        doctor_conf = confidence_data.get("doctor", 0.0)
        tests_conf = confidence_data.get("tests", 0.0)
        overall_conf = (patient_conf + doctor_conf + tests_conf) / 3.0

        # Build response
        referral_data = ReferralData(
            patient=extracted_data.get("patient", {}),
            doctor=extracted_data.get("doctor", {}),
            tests=extracted_data.get("tests", []),
            matched_tests=matched_tests,
            clinical_notes=extracted_data.get("clinicalNotes"),
            urgent=extracted_data.get("urgent", False),
            collection_date=extracted_data.get("collectionDate"),
            confidence=ConfidenceScores(
                patient=patient_conf,
                doctor=doctor_conf,
                tests=tests_conf,
                overall=overall_conf,
            ),
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Referral scan complete",
            processing_time_ms=processing_time_ms,
            tests_matched=len(matched_tests),
            overall_confidence=overall_conf,
            organization_id=auth.organization_id,
        )

        return ScanResponse(
            success=True,
            data=referral_data,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except ValidationError as e:
        # Client validation errors (e.g., image too large)
        logger.warning(
            "Validation error scanning referral",
            error=str(e),
            organization_id=auth.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Error scanning referral",
            error=str(e),
            error_type=type(e).__name__,
            organization_id=auth.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/tests/match", response_model=TestMatchResponse, response_model_by_alias=True)
async def match_test_names(
    request: TestMatchRequest,
    auth: Annotated[AuthContext, Depends(get_current_user)],
) -> TestMatchResponse:
    """Match test names to catalog without image scanning.

    Performs fuzzy matching of test names against the test catalog service
    to identify standard test codes and display names.

    Args:
        request: List of test names to match
        auth: Authenticated user context from JWT

    Returns:
        TestMatchResponse with matched tests and confidence scores

    Raises:
        HTTPException: If matching fails
    """
    logger.info(
        "Matching test names",
        test_count=len(request.tests),
        organization_id=auth.organization_id,
        user_id=auth.user_id,
    )

    try:
        test_matcher = TestMatcherService(organization_id=auth.organization_id)
        matched_tests = await test_matcher.match_tests(request.tests)

        logger.info(
            "Test matching complete",
            matched_count=len(matched_tests),
            organization_id=auth.organization_id,
        )

        return TestMatchResponse(success=True, data=matched_tests)

    except Exception as e:
        logger.error(
            "Error matching test names",
            error=str(e),
            error_type=type(e).__name__,
            organization_id=auth.organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
