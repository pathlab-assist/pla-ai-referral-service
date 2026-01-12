# ============================================================================
# AI Referral Service - Test Matching Tests
# ============================================================================
# Tests for POST /api/v1/referral/tests/match endpoint
# Matches test names to catalog via test-catalog-service
# Requires: test-catalog-service running on port 8003

# Test 1: Match Valid Test Names
# Purpose: Verify successful batch matching with exact codes
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": ["{{TEST_CODE_FBC}}", "{{TEST_CODE_UEC}}", "{{TEST_CODE_LFT}}"]
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" count == 3
jsonpath "$.data[0].original" == "{{TEST_CODE_FBC}}"
jsonpath "$.data[0].matched" == "Full Blood Count"
jsonpath "$.data[0].testId" == "{{TEST_CODE_FBC}}"
jsonpath "$.data[0].confidence" > 0.9
jsonpath "$.data[1].original" == "{{TEST_CODE_UEC}}"
jsonpath "$.data[1].testId" == "{{TEST_CODE_UEC}}"
jsonpath "$.data[2].original" == "{{TEST_CODE_LFT}}"
jsonpath "$.data[2].testId" == "{{TEST_CODE_LFT}}"


# Test 2: Match Test Names (Fuzzy Matching)
# Purpose: Verify fuzzy matching with full test names
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": ["Full Blood Count", "Electrolytes", "Liver Function"]
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" count == 3
jsonpath "$.data[*].testId" includes "{{TEST_CODE_FBC}}"
jsonpath "$.data[*].testId" includes "{{TEST_CODE_UEC}}"
jsonpath "$.data[*].testId" includes "{{TEST_CODE_LFT}}"
# Note: Fuzzy matching may not always return 1.0 confidence
jsonpath "$.data[*].confidence" nth 0 > 0.7
jsonpath "$.data[*].confidence" nth 1 > 0.3
jsonpath "$.data[*].confidence" nth 2 > 0.7


# Test 3: Match Unknown Tests
# Purpose: Verify handling of unknown test names
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": ["UNKNOWN_TEST_9999", "INVALID_CODE"]
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" count == 2
jsonpath "$.data[0].confidence" < 0.5
jsonpath "$.data[1].confidence" < 0.5


# Test 4: Match Mixed Valid and Invalid
# Purpose: Verify correct handling of mixed test names
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": ["{{TEST_CODE_FBC}}", "UNKNOWN", "{{TEST_CODE_UEC}}"]
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" count == 3
jsonpath "$.data[0].confidence" > 0.9
jsonpath "$.data[1].confidence" < 0.5
jsonpath "$.data[2].confidence" > 0.9


# Test 5: Match Empty Array
# Purpose: Verify validation rejects empty test array
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": []
}

HTTP 422
[Asserts]
jsonpath "$.error" == "ValidationError"
jsonpath "$.details" exists


# Test 6: Match Missing Tests Field
# Purpose: Verify validation requires tests field
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "other": "field"
}

HTTP 422
[Asserts]
jsonpath "$.error" == "ValidationError"
jsonpath "$.details" exists


# Test 7: Match Test Aliases
# Purpose: Verify alias matching returns high confidence
POST {{BASE_URL}}/api/v1/referral/tests/match
Authorization: Bearer {{access_token}}
Content-Type: application/json
{
  "tests": ["CBC", "U&E", "FBE"]
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" count == 3
jsonpath "$.data[*].testId" includes "{{TEST_CODE_FBC}}"
jsonpath "$.data[*].testId" includes "{{TEST_CODE_UEC}}"
# Alias matching should return reasonable confidence scores
jsonpath "$.data[*].confidence" nth 0 > 0.7
jsonpath "$.data[*].confidence" nth 1 > 0.7
