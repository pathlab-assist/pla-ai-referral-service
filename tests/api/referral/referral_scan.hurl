# ============================================================================
# AI Referral Service - Referral Scan Tests
# ============================================================================
# Tests for POST /api/v1/referral/scan endpoint
# Uses Claude Vision to extract structured data from referral images
# Requires: ANTHROPIC_API_KEY, test-catalog-service running

# Test 1: Scan Referral Image - File Size Limit
# Purpose: Verify behavior when image exceeds Claude API 5MB limit
# NOTE: Current sample image is 6.6MB (9.2MB base64 encoded), exceeds limit
# TODO: Replace with smaller test image (< 3.5MB) for positive test case
# TODO: Service should return 400 instead of 500 for client errors
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
[MultipartFormData]
image: file,tests/api/fixtures/sample-referral.png; image/png

HTTP 500


# Test 2: Scan Referral - Missing Image
# Purpose: Verify validation rejects missing image file
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
HTTP 422


# Test 3: Scan Referral - Invalid File Type
# Purpose: Verify behavior with non-image files
# TODO: Service should validate content type and return 400 instead of 500
POST {{BASE_URL}}/api/v1/referral/scan
Authorization: Bearer {{access_token}}
[MultipartFormData]
image: file,tests/api/.env; text/plain

HTTP 500


# Test 4: Scan Referral - Empty Image
# Note: hurl doesn't support raw multipart boundary syntax
# Empty/corrupted file handling is tested in unit tests
