# CLAUDE.md - Python/FastAPI Microservice Template Context

## Overview

This is a production-ready Python/FastAPI microservice template for PathLab Assist services. It provides a scaffolding project with best practices for building scalable, compliant, and maintainable microservices.

## Purpose

**This is a TEMPLATE** - designed to be cloned and customized for specific services like:
- AI/ML services (e.g., AI Referral Scanning)
- Data processing services
- Integration services
- API gateways

## Architecture

### Pythonic Design (NOT Java/Go patterns)

- **`models/`** - Business entities (domain layer), NOT `domain/`
- **`schemas/`** - Pydantic request/response models, NOT `dto/`
- **`repositories/`** - Data access layer
- **`services/`** - Business logic
- **`routers/`** - FastAPI endpoints, NOT `handlers/` or `api/`

### Layers

```
Request → Router → Service → Repository → DynamoDB
         ↓
      Schemas (validation)
                  ↓
              Models (business logic)
```

## Key Patterns

### 1. Multi-Tenancy

**CRITICAL:** All data access MUST be scoped by `organization_id`

```python
# Always from JWT, NEVER from request body
organization_id = auth.organization_id

# All queries scoped
items = await repo.list(organization_id=organization_id, ...)
```

**DynamoDB Keys:**
- PK: `ORG#{organization_id}`
- SK: `{ENTITY_TYPE}#{id}`

### 2. Audit Trails (NPAAC Compliance)

All entities must track:
- `created_at`, `created_by`
- `updated_at`, `updated_by`

Use `BaseEntity` mixin:

```python
from app.models.base import BaseEntity

class MyEntity(BaseEntity):
    # Automatically includes audit fields
    name: str
```

### 3. PII Masking (Privacy Act 1988)

**NEVER log PII in plaintext:**
- Medicare numbers
- Date of birth
- Email addresses
- Phone numbers

Logging middleware automatically masks these fields.

### 4. Error Handling

Use custom exceptions:

```python
from app.core.exceptions import NotFoundError, ValidationError

raise NotFoundError("Item", item_id)
raise ValidationError("Name cannot be empty", field="name")
```

## File Structure Conventions

### Models (`src/app/models/`)

Business entities with domain logic:

```python
class Item(BaseEntity):
    name: str
    status: Literal["active", "inactive"]

    def activate(self) -> None:
        self.status = "active"
```

### Schemas (`src/app/schemas/`)

API contracts (request/response):

```python
class ItemCreate(BaseModel):  # Request
    name: str

class ItemResponse(BaseModel):  # Response
    id: str
    name: str
    created_at: datetime
```

### Repositories (`src/app/repositories/`)

Data access only (no business logic):

```python
class ItemRepository(BaseRepository[Item]):
    async def get(self, id: str, organization_id: str) -> Item | None:
        # DynamoDB query
```

### Services (`src/app/services/`)

Business logic orchestration:

```python
class ItemService:
    async def create_item(self, data: ItemCreate, org_id: str, user_id: str) -> Item:
        # Validate
        # Create entity
        # Save via repository
```

### Routers (`src/app/routers/`)

FastAPI endpoints (thin layer):

```python
@router.post("/items")
async def create_item(
    data: ItemCreate,
    auth: Annotated[AuthContext, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
):
    return await service.create_item(data, auth.organization_id, auth.user_id)
```

## Common Tasks

### Adding a New Entity

1. **Model** - `src/app/models/{entity}.py`
2. **Schemas** - `src/app/schemas/{entity}.py`
3. **Repository** - `src/app/repositories/{entity}.py`
4. **Service** - `src/app/services/{entity}.py`
5. **Router** - `src/app/routers/{entity}.py`
6. **Register** - Add router to `src/app/main.py`

### Adding External Clients

For AI/ML integrations, create client modules:

```python
# src/app/clients/anthropic.py
class ClaudeClient:
    async def analyze(...): ...
```

### DynamoDB Table Design

Follow single-table design patterns:
- **PK**: `ORG#{organization_id}` (tenant isolation)
- **SK**: `{TYPE}#{id}` (entity type + ID)
- **GSIs**: For queries (status, date ranges, etc.)

Example GSI for filtering:
- **GSI1PK**: `ORG#{organization_id}`
- **GSI1SK**: `STATUS#{status}#CREATED#{created_at}`

## Configuration

### Environment Variables

All config via `src/app/config.py` using Pydantic Settings:

```python
class Settings(BaseSettings):
    service_name: str = "my-service"
    jwt_enabled: bool = False
    # ...
```

### Feature Flags

Use environment variables for feature toggles:
- `JWT_ENABLED` - Authentication
- `LOG_JSON` - JSON vs console logging
- `CORS_ENABLED` - CORS middleware

## Testing

### Unit Tests

Test services and business logic:

```python
# tests/unit/test_item_service.py
async def test_create_item():
    repo = Mock(ItemRepository)
    service = ItemService(repo)
    # ...
```

### Integration Tests

Test repositories with LocalStack:

```python
# tests/integration/test_item_repository.py
async def test_create_and_get(dynamodb_table):
    repo = ItemRepository(...)
    # ...
```

## Security

### JWT Authentication

When `JWT_ENABLED=true`:
- All requests require `Authorization: Bearer <token>`
- Token validated via JWKS
- Claims extracted: `user_id`, `organization_id`, `roles`

### PII Protection

Structured logging masks:
- `medicare_number`
- `date_of_birth`
- `email`
- `phone`
- `password`
- `token`

## Deployment

### Docker

Multi-stage build:
1. Builder stage: Install dependencies
2. Runtime stage: Copy app + dependencies
3. Non-root user: `appuser` (UID 1000)

### LocalStack

For local development:
1. Start: `make up-full`
2. Create tables: `make setup-db`
3. Access: `http://localhost:4566`

## Common Pitfalls

❌ **DON'T:**
- Accept `organization_id` from request body (use JWT)
- Log PII in plaintext
- Forget audit fields on mutations
- Use blocking I/O operations
- Store sensitive data in environment

✅ **DO:**
- Extract `organization_id` from JWT
- Use structured logging with PII masking
- Always populate audit fields
- Use `async/await` for I/O
- Use AWS Secrets Manager for secrets

## Template Usage

This is a **scaffolding project**. When creating a new service:

1. Clone this template
2. Replace `template-service` with your service name
3. Update port in `docker-compose.yml`
4. Remove example `Item` entity
5. Add your domain entities
6. Update `CLAUDE.md` with service-specific context

## Version

Template Version: 0.1.0
Python Version: 3.11
FastAPI Version: 0.109+

---

*This file is for AI assistants (like Claude Code) to understand the project context and patterns.*
