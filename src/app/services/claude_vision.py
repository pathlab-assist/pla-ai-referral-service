"""Claude Vision service for extracting structured data from referral images."""
import base64
import json
from typing import Any

import anthropic

from app.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Extraction prompt for Claude Vision
EXTRACTION_PROMPT = """You are a medical data extraction assistant for Australian pathology referrals.

Analyze the uploaded pathology referral form and extract the following information in JSON format:

{
  "patient": {
    "firstName": "patient's first/given name",
    "lastName": "patient's surname/family name",
    "dateOfBirth": "YYYY-MM-DD format",
    "sex": "M or F or U (unknown)",
    "medicareNumber": "10 digit Medicare number if visible",
    "address": "full address if visible"
  },
  "doctor": {
    "name": "referring doctor's name",
    "providerNumber": "provider number if visible",
    "practice": "practice/clinic name if visible",
    "phone": "contact phone if visible",
    "address": "practice address if visible"
  },
  "tests": [
    "list of requested pathology tests - extract exactly as written"
  ],
  "clinicalNotes": "any clinical notes or indications mentioned",
  "urgent": true/false (whether marked urgent or STAT),
  "collectionDate": "preferred collection date if mentioned",
  "confidence": {
    "patient": 0-1 (confidence in patient data extraction),
    "doctor": 0-1 (confidence in doctor data extraction),
    "tests": 0-1 (confidence in test identification)
  }
}

IMPORTANT:
- If a field is not visible or unclear, use null
- For tests, extract the exact wording from the form
- Common Australian test abbreviations: FBC, UEC, LFT, TFT, HbA1c, CRP, ESR
- Be conservative with confidence scores (0.5-0.7 for handwritten, 0.8-1.0 for printed)
- If the image is not a pathology referral, return {"error": "Not a pathology referral"}

Extract data from this referral form:"""


class ClaudeVisionService:
    """Service for extracting structured data from referral images using Claude Vision."""

    def __init__(self) -> None:
        """Initialize Claude Vision service."""
        if not settings.anthropic_api_key:
            logger.warning("Anthropic API key not configured")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    async def extract_referral_data(
        self, image_bytes: bytes, image_type: str = "image/jpeg"
    ) -> dict[str, Any]:
        """Extract structured data from referral image using Claude Vision.

        Args:
            image_bytes: Image file bytes
            image_type: MIME type (image/jpeg, image/png, etc.)

        Returns:
            Extracted data as dictionary

        Raises:
            Exception: If extraction fails or API error occurs
        """
        # Encode image to base64
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        try:
            # Call Claude API with vision
            logger.debug(
                "Calling Claude Vision API",
                model=self.model,
                image_type=image_type,
                image_size_bytes=len(image_bytes),
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_type,
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": EXTRACTION_PROMPT},
                        ],
                    }
                ],
            )

            # Extract JSON from Claude's response
            response_text = message.content[0].text

            logger.debug("Claude API response received", response_length=len(response_text))

            # Parse JSON from response (handle markdown code blocks)
            extracted_data = self._parse_json_response(response_text)

            # Log extraction metadata (NO PII)
            if "error" not in extracted_data:
                patient_fields = len(
                    [v for v in extracted_data.get("patient", {}).values() if v is not None]
                )
                doctor_fields = len(
                    [v for v in extracted_data.get("doctor", {}).values() if v is not None]
                )
                test_count = len(extracted_data.get("tests", []))

                logger.info(
                    "Extraction complete",
                    patient_fields_extracted=patient_fields,
                    doctor_fields_extracted=doctor_fields,
                    tests_extracted=test_count,
                    overall_confidence=extracted_data.get("confidence", {}).get("overall"),
                )

            return extracted_data

        except anthropic.BadRequestError as e:
            # Client errors (400) - invalid request, image too large, etc.
            logger.warning("Claude API client error", error=str(e), error_type=type(e).__name__)
            error_msg = str(e)
            if "exceeds" in error_msg.lower() or "maximum" in error_msg.lower():
                raise ValidationError("Image file too large. Maximum size is 5MB when base64 encoded.")
            raise ValidationError(f"Invalid request: {error_msg}")
        except anthropic.APIError as e:
            # Server errors (500+) or other API errors
            logger.error("Claude API error", error=str(e), error_type=type(e).__name__)
            raise Exception(f"Claude API error: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response as JSON", error=str(e))
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}") from e
        except Exception as e:
            logger.error(
                "Extraction failed", error=str(e), error_type=type(e).__name__
            )
            raise Exception(f"Extraction failed: {str(e)}") from e

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON from Claude's response, handling markdown code blocks.

        Args:
            response_text: Raw text response from Claude

        Returns:
            Parsed JSON as dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        # Claude sometimes wraps JSON in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        return json.loads(response_text)  # type: ignore[no-any-return]
