#!/bin/bash
# Script to get JWT access token from auth service
# Used by make test-api-jwt

set -e

AUTH_URL="${AUTH_URL:-http://localhost:8080}"
ORG_SLUG="${ORG_SLUG:-pathlab}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@pathlab.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-PathLab2024!}"

# Check if auth service is reachable
if ! curl -s -f "${AUTH_URL}/health" >/dev/null 2>&1; then
    echo "❌ Error: Auth service not reachable at ${AUTH_URL}" >&2
    echo "   Make sure pathlab-assist-auth is running" >&2
    exit 1
fi

# Get access token
response=$(curl -s -X POST "${AUTH_URL}/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"organizationSlug\":\"${ORG_SLUG}\",\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")

# Extract token
token=$(echo "$response" | jq -r '.accessToken // empty')

if [ -z "$token" ] || [ "$token" = "null" ]; then
    echo "❌ Error: Failed to get access token" >&2
    echo "   Response: $response" >&2
    exit 1
fi

echo "$token"
