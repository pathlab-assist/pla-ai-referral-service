# PathLab Assist - Python/FastAPI Microservice Template

Production-ready Python/FastAPI microservice template for PathLab Assist services. Designed for AI/ML services with comprehensive support for multi-tenancy, authentication, structured logging, and AWS integration.

## Features

- ✅ **FastAPI** - Modern, fast Python web framework
- ✅ **Pythonic Architecture** - Clean separation: models, schemas, repositories, services, routers
- ✅ **Multi-Tenancy** - Organization-scoped data access with JWT-based tenant isolation
- ✅ **JWT Authentication** - JWKS-based token validation with configurable middleware
- ✅ **Structured Logging** - `structlog` with PII masking and JSON output
- ✅ **DynamoDB Repository** - Example implementation with GSI patterns
- ✅ **NPAAC Compliance** - Audit trails on all entities (created_by, updated_by, timestamps)
- ✅ **Privacy Act 1988** - PII masking in logs (Medicare numbers, DOB, email, phone)
- ✅ **Docker & docker-compose** - Multi-stage build, non-root user, health checks
- ✅ **LocalStack Support** - Local AWS services for development
- ✅ **Type Safety** - Full mypy type checking
- ✅ **Code Quality** - Ruff for linting and formatting
- ✅ **Testing** - pytest with async support and coverage
- ✅ **CI/CD** - GitHub Actions workflow

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- AWS CLI (for LocalStack operations)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pathlab-assist/pla-python-microservice-template.git
   cd pla-python-microservice-template
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

### Development

**Run locally with auto-reload:**
```bash
make dev
```

The service will be available at `http://localhost:8080`

- API Docs: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- Health Check: `http://localhost:8080/health`

### Docker Development

**Start with LocalStack:**
```bash
make up-full
```

**View logs:**
```bash
make logs
```

**Setup DynamoDB tables:**
```bash
make setup-db
```

**Stop services:**
```bash
make down
```

## Project Structure

```
pla-python-microservice-template/
├── src/app/                    # Main application package
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Pydantic Settings configuration
│   ├── dependencies.py         # FastAPI dependency injection
│   │
│   ├── models/                 # Business entities (domain layer)
│   │   ├── base.py             # TenantMixin, AuditMixin, BaseEntity
│   │   └── item.py             # Example entity
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── common.py           # Pagination, errors, health
│   │   └── item.py             # Item schemas
│   │
│   ├── repositories/           # Data access layer
│   │   ├── base.py             # BaseRepository ABC
│   │   └── item.py             # DynamoDB implementation
│   │
│   ├── services/               # Business logic layer
│   │   └── item.py             # Item service
│   │
│   ├── routers/                # API endpoints (FastAPI routers)
│   │   ├── health.py           # /health, /ready
│   │   └── item.py             # /items CRUD
│   │
│   ├── middleware/             # Request middleware
│   │   ├── request_id.py       # Request ID tracking
│   │   ├── logging.py          # Request/response logging
│   │   └── auth.py             # JWT authentication
│   │
│   └── core/                   # Core utilities
│       ├── exceptions.py       # Custom exceptions
│       ├── logging.py          # Structlog setup
│       ├── pii.py              # PII masking utilities
│       └── security.py         # JWT/JWKS utilities
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
├── scripts/                    # Utility scripts
│   └── setup-db.sh             # DynamoDB table creation
│
├── .github/workflows/          # CI/CD
│   └── ci.yml                  # GitHub Actions
│
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Local development setup
├── Makefile                    # Build automation
└── pyproject.toml              # Project configuration
```

## Architecture Patterns

### Multi-Tenancy

All data operations are scoped by `organization_id` extracted from JWT:

```python
# In routers - via dependency injection
async def create_item(
    data: ItemCreate,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
):
    item = await service.create_item(
        data=data,
        organization_id=auth.organization_id,  # From JWT
        user_id=auth.user_id,
    )
```

### Audit Trails (NPAAC Compliance)

All entities inherit from `BaseEntity` with automatic audit fields:

```python
class Item(BaseEntity):
    # Inherits:
    # - organization_id: str
    # - created_at: datetime
    # - created_by: str
    # - updated_at: datetime
    # - updated_by: str
```

### PII Masking (Privacy Act 1988)

Structured logging automatically masks PII:

```python
logger.info("User registered", email="user@example.com")
# Output: {"event": "User registered", "email": "[MASKED]"}
```

Masked fields: `medicare_number`, `date_of_birth`, `email`, `phone`, `password`, `token`, `api_key`

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service name | `template-service` |
| `ENVIRONMENT` | Environment (development, staging, production) | `development` |
| `JWT_ENABLED` | Enable JWT authentication | `false` |
| `JWT_JWKS_URL` | JWKS endpoint for token validation | - |
| `JWT_ISSUER` | Expected token issuer | - |
| `AWS_ENDPOINT_URL` | AWS endpoint (for LocalStack) | `http://localhost:4566` |
| `DYNAMODB_TABLE_PREFIX` | DynamoDB table prefix | `pla-dev-` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_JSON` | JSON log output | `true` |

## Development Workflow

### Code Quality

```bash
# Format code
make format

# Lint
make lint

# Type check
make typecheck

# Run all checks
make ci
```

### Testing

```bash
# Run all tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run
```

## DynamoDB Schema

The template includes an example Items table with GSI for efficient queries:

**Table: `pla-dev-items`**
- **PK**: `ORG#{organization_id}`
- **SK**: `ITEM#{item_id}`
- **GSI1PK**: `ORG#{organization_id}`
- **GSI1SK**: `STATUS#{status}#CREATED#{created_at}`

**Queries:**
- Get item: `PK = ORG#{org_id} AND SK = ITEM#{item_id}`
- List all items: `GSI1: GSI1PK = ORG#{org_id}`
- List by status: `GSI1: GSI1PK = ORG#{org_id} AND GSI1SK BEGINS_WITH STATUS#{status}`

## JWT Authentication

When `JWT_ENABLED=true`:

1. Requests must include `Authorization: Bearer <token>`
2. Token validated against JWKS endpoint
3. Claims extracted: `sub` (user_id), `organization_id`, `roles`
4. Available in routers via `get_current_user` dependency

**Excluded paths:** `/health`, `/ready`, `/docs`, `/redoc`, `/openapi.json`

## Extending the Template

### 1. Add a New Entity

**Create model:**
```python
# src/app/models/product.py
from app.models.base import BaseEntity

class Product(BaseEntity):
    name: str
    price: float
```

**Create schemas:**
```python
# src/app/schemas/product.py
class ProductCreate(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    # ... audit fields
```

**Create repository:**
```python
# src/app/repositories/product.py
class ProductRepository(BaseRepository[Product]):
    # DynamoDB implementation
```

**Create service:**
```python
# src/app/services/product.py
class ProductService:
    async def create_product(self, ...): ...
```

**Create router:**
```python
# src/app/routers/product.py
router = APIRouter(prefix="/products", tags=["Products"])

@router.post("")
async def create_product(...): ...
```

**Register router:**
```python
# src/app/main.py
from app.routers import product
app.include_router(product.router)
```

### 2. Add External Service Client

For AI/ML services, add clients:

```python
# src/app/clients/anthropic.py (example for AI services)
from anthropic import AsyncAnthropic

class ClaudeClient:
    async def analyze_document(self, content: bytes): ...
```

## CI/CD

GitHub Actions workflow runs on push/PR:

1. ✅ Code formatting check
2. ✅ Linting (ruff)
3. ✅ Type checking (mypy)
4. ✅ Tests with coverage
5. ✅ Docker build
6. ✅ Upload coverage to Codecov

## License

MIT

## Support

For issues or questions, please create an issue in the GitHub repository.
