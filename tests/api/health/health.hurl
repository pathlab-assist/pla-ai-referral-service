# ============================================================================
# AI Referral Service - Health Check Tests
# ============================================================================
# Tests for service health and readiness endpoints
# No authentication required

# Test 1: Health Check - Service Running
# Purpose: Verify service is responsive
GET {{BASE_URL}}/health
HTTP 200
[Asserts]
jsonpath "$.status" == "healthy"
jsonpath "$.service" == "{{SERVICE_NAME}}"
jsonpath "$.version" exists
jsonpath "$.timestamp" exists


# Test 2: Ready Check - Service Ready
# Purpose: Verify service is ready to accept requests
GET {{BASE_URL}}/ready
HTTP 200
[Asserts]
jsonpath "$.ready" == true
jsonpath "$.checks" exists
jsonpath "$.timestamp" exists
