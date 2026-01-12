#!/bin/bash
#
# Setup DynamoDB tables in LocalStack
#

set -e

# Configuration
AWS_ENDPOINT="http://localhost:4566"
AWS_REGION="us-east-1"
TABLE_PREFIX="pla-dev-"

echo "Setting up DynamoDB tables in LocalStack..."
echo "Endpoint: $AWS_ENDPOINT"
echo "Region: $AWS_REGION"
echo "Table Prefix: $TABLE_PREFIX"
echo ""

# Create Items table
TABLE_NAME="${TABLE_PREFIX}items"
echo "Creating table: $TABLE_NAME"

aws dynamodb create-table \
  --endpoint-url "$AWS_ENDPOINT" \
  --region "$AWS_REGION" \
  --table-name "$TABLE_NAME" \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"GSI1\",
        \"KeySchema\": [
          {\"AttributeName\": \"GSI1PK\", \"KeyType\": \"HASH\"},
          {\"AttributeName\": \"GSI1SK\", \"KeyType\": \"RANGE\"}
        ],
        \"Projection\": {\"ProjectionType\": \"ALL\"},
        \"ProvisionedThroughput\": {
          \"ReadCapacityUnits\": 5,
          \"WriteCapacityUnits\": 5
        }
      }
    ]" \
  --provisioned-throughput \
    ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --no-cli-pager

echo ""
echo "✓ Table created: $TABLE_NAME"
echo ""

# Verify tables
echo "Listing tables..."
aws dynamodb list-tables \
  --endpoint-url "$AWS_ENDPOINT" \
  --region "$AWS_REGION" \
  --no-cli-pager

echo ""
echo "✓ DynamoDB setup complete!"
