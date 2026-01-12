# ============================================================================
# AI Referral Service - Referral Scan Tests
# ============================================================================
# Tests for POST /api/v1/referral/scan endpoint
# Uses Claude Vision to extract structured data from referral images
# Requires: ANTHROPIC_API_KEY, test-catalog-service running

# Test 1: Scan Referral Image - Successful Extraction
# Purpose: Verify end-to-end referral scanning with sample image
# NOTE: Image is 1.7MB (~2.3MB base64), within Claude's 5MB limit
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
[MultipartFormData]
image: file,tests/api/fixtures/sample-referral.png; image/png

HTTP 200
[Asserts]
# Response structure
jsonpath "$.success" == true
jsonpath "$.data" exists
jsonpath "$.processingTimeMs" exists
jsonpath "$.timestamp" exists

# Extracted fields
jsonpath "$.data.patient" exists
jsonpath "$.data.doctor" exists
jsonpath "$.data.tests" exists
jsonpath "$.data.matchedTests" exists

# Confidence scores
jsonpath "$.data.confidence" exists
jsonpath "$.data.confidence.overall" > 0.5


# Test 2: Scan Referral - Missing Image
# Purpose: Verify validation rejects missing image file
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
HTTP 422


# Test 3: Scan Referral - Invalid File Type
# Purpose: Verify validation rejects non-image files
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
[MultipartFormData]
image: file,tests/api/.env; text/plain

HTTP 400
[Asserts]
jsonpath "$.detail" contains "Invalid image type"


# Test 4: Scan Referral - Oversized Image
# Purpose: Verify validation rejects images exceeding Claude's 5MB base64 limit
# NOTE: Using original 6.6MB image which becomes 9.2MB when base64 encoded
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
[MultipartFormData]
image: file,tests/api/fixtures/sample-referral-original.png; image/png

HTTP 422
[Asserts]
jsonpath "$.error" == "ValidationError"
jsonpath "$.message" contains "too large"


# Test 5: Scan Referral - Empty Image
# Note: hurl doesn't support raw multipart boundary syntax
# Empty/corrupted file handling is tested in unit tests
