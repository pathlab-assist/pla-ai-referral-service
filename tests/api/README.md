# AI Referral Service - API Tests

Comprehensive API test suite using [Hurl](https://hurl.dev/) for testing the AI referral scanning service endpoints.

## Prerequisites

1. **Hurl Installed**
   ```bash
   # macOS
   brew install hurl

   # Linux
   curl --location --remote-name https://github.com/Orange-OpenSource/hurl/releases/download/4.1.0/hurl_4.1.0_amd64.deb
   sudo dpkg -i hurl_4.1.0_amd64.deb
   ```

2. **Services Running**
   - AI Referral Service on port 8011
   - Test Catalog Service on port 8003 (for test matching)

3. **Environment Variables**
   - `ANTHROPIC_API_KEY` configured in `tests/api/.env`

## Test Structure

```
tests/api/
├── .env                          # Environment variables
├── health/
│   └── health.hurl              # Health check tests (2 tests)
├── referral/
│   ├── referral_scan.hurl       # Scan endpoint tests (4 tests)
│   └── test_match.hurl          # Test matching tests (7 tests)
└── fixtures/
    └── sample-referral.png      # Sample referral image
```

## Running Tests

### All Tests
```bash
make test-api
```

### Individual Test Suites
```bash
# Health checks only (fast, no external dependencies)
make test-api-health

# Referral scanning (requires Anthropic API key, ~3-5 seconds per test)
make test-api-scan

# Test matching (requires test-catalog-service)
make test-api-match
```

### Manual Hurl Execution
```bash
# Run specific file
hurl --test tests/api/health/health.hurl --variables-file tests/api/.env

# Run with verbose output
hurl --test --very-verbose tests/api/referral/referral_scan.hurl --variables-file tests/api/.env

# Run all tests
hurl --test tests/api/**/*.hurl --variables-file tests/api/.env
```

## Test Coverage

### Health Endpoints (2 tests)
- ✅ GET /health - Service running check
- ✅ GET /ready - Service readiness check

### Referral Scan (4 tests)
- ✅ Complete extraction from sample referral image
  - Patient: SMITH, JOHN (M, DOB: 15/05/1985)
  - Medicare: 1234 56789 1 / 1
  - Tests: FBE, U&E, LFT, Lipid Profile, Glucose (Fasting)
  - Doctor: Dr. Sarah Jane (Prov: 1234567A)
  - Clinical notes: "Routine annual health screening"
- ✅ Missing image validation
- ✅ Invalid file type validation
- ✅ Empty image handling

### Test Matching (7 tests)
- ✅ Exact code matching (FBC, UEC, LFT)
- ✅ Fuzzy name matching (Full Blood Count, Electrolytes)
- ✅ Unknown test handling
- ✅ Mixed valid/invalid tests
- ✅ Empty array handling
- ✅ Missing field validation
- ✅ Alias matching (CBC, U&E, FBE)

## Expected Results

### Sample Referral Scan Expected Output

```json
{
  "success": true,
  "data": {
    "patient": {
      "firstName": "JOHN",
      "lastName": "SMITH",
      "sex": "M",
      "dateOfBirth": "1985-05-15",
      "medicareNumber": "1234 56789 1 / 1",
      "address": "123 Sample St, Sydney, NSW, 2000"
    },
    "doctor": {
      "name": "Dr. Sarah Jane",
      "providerNumber": "1234567A",
      "address": "45 Medical Lane, Sydney, NSW, 2000"
    },
    "tests": ["FBE", "U&E", "LFT", "Lipid Profile", "Glucose (Fasting)"],
    "matchedTests": [
      {
        "original": "FBE",
        "matched": "Full Blood Count",
        "testId": "FBC",
        "confidence": 1.0
      }
      // ... more matches
    ],
    "clinicalNotes": "Routine annual health screening.",
    "urgent": false,
    "confidence": {
      "patient": 0.95,
      "doctor": 0.90,
      "tests": 0.98,
      "overall": 0.94
    }
  },
  "processingTimeMs": 2500,
  "timestamp": "2026-01-12T..."
}
```

## Troubleshooting

### Test Failures

**"Connection refused" errors:**
```bash
# Check if service is running
curl http://localhost:8011/health

# Start service
docker-compose up -d
# or
make dev
```

**"Anthropic API key" errors:**
```bash
# Verify API key is set
grep ANTHROPIC_API_KEY tests/api/.env

# Test key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

**Test catalog service errors:**
```bash
# Check test-catalog-service is running
curl http://localhost:8003/health

# Start test-catalog-service
cd ../pla-test-catalog-service
make up-full && make setup-db && make seed
```

**Image file not found:**
```bash
# Verify sample image exists
ls -la tests/api/fixtures/sample-referral.png

# If missing, copy sample referral image to fixtures directory
```

### Confidence Score Variations

Claude Vision confidence scores may vary slightly between runs due to:
- Model non-determinism
- Image quality interpretation
- Text extraction variations

**Acceptable ranges:**
- Patient extraction: 0.85-1.0
- Doctor extraction: 0.80-0.95
- Test extraction: 0.90-1.0
- Overall: 0.85-0.98

If scores are consistently below these ranges, check:
1. Image quality (resolution, clarity)
2. API key validity
3. Model version in config

## Performance Benchmarks

**Expected timings:**
- Health checks: ~10ms
- Test matching: ~50ms (batch endpoint)
- Referral scan: 2-5 seconds (Claude Vision API call)

**Total test suite:** ~15-20 seconds (including 1 full scan)

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run API Tests
  run: |
    # Start services
    docker-compose up -d
    sleep 5  # Wait for services to be ready

    # Run tests
    make test-api
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Adding New Tests

### Template for New Test

```hurl
# Test N: Test Description
# Purpose: What this test verifies
POST {{BASE_URL}}/api/v1/your-endpoint
Content-Type: application/json
{
  "field": "value"
}

HTTP 200
[Asserts]
jsonpath "$.success" == true
jsonpath "$.data" exists
```

### Best Practices

1. **Descriptive names** - Clear test purpose in comments
2. **Specific assertions** - Test exact values, not just existence
3. **Error cases** - Test validation and error handling
4. **Cleanup** - Tests should not leave side effects
5. **Independence** - Each test should run standalone

## Resources

- [Hurl Documentation](https://hurl.dev/docs/manual.html)
- [JSONPath Syntax](https://goessner.net/articles/JsonPath/)
- [Anthropic API Docs](https://docs.anthropic.com/en/api/messages)
