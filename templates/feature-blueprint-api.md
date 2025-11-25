# Feature Blueprint: New API Endpoint

Use this template when creating a new API endpoint.

## Steps

### 1. Create Route Handler

Create `src/api/[feature_name].py`:

```python
"""
[Feature Name] API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from src.utils.http_exceptions import not_found, bad_request
from src.tenants.tenant_isolation import get_current_tenant

router = APIRouter()


# Request/Response Models
class [Feature]Create(BaseModel):
    """Create [feature] request"""
    name: str
    description: Optional[str] = None


class [Feature]Update(BaseModel):
    """Update [feature] request"""
    name: Optional[str] = None
    description: Optional[str] = None


class [Feature]Response(BaseModel):
    """[Feature] response"""
    id: UUID
    name: str
    description: Optional[str]
    tenant_id: UUID
    created_at: str
    updated_at: str


# Endpoints
@router.post("/[feature-plural]", response_model=[Feature]Response, status_code=status.HTTP_201_CREATED)
async def create_[feature](
    data: [Feature]Create,
    tenant_id: UUID = Depends(get_current_tenant),
    request: Request = None
):
    """Create a new [feature]"""
    # Implementation here
    pass


@router.get("/[feature-plural]", response_model=List[[Feature]Response])
async def list_[feature-plural](
    tenant_id: UUID = Depends(get_current_tenant),
    limit: int = 50,
    offset: int = 0
):
    """List [feature-plural]"""
    # Implementation here
    pass


@router.get("/[feature-plural]/{[feature]_id}", response_model=[Feature]Response)
async def get_[feature](
    [feature]_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant)
):
    """Get [feature] by ID"""
    # Implementation here
    pass


@router.put("/[feature-plural]/{[feature]_id}", response_model=[Feature]Response)
async def update_[feature](
    [feature]_id: UUID,
    data: [Feature]Update,
    tenant_id: UUID = Depends(get_current_tenant)
):
    """Update [feature]"""
    # Implementation here
    pass


@router.delete("/[feature-plural]/{[feature]_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_[feature](
    [feature]_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant)
):
    """Delete [feature]"""
    # Implementation here
    pass
```

### 2. Register Route

Add to `src/api/route_registration.py`:

```python
from src.api import [feature_name]

app.include_router([feature_name].router, prefix="/api/v1", tags=["[feature-plural]"])
```

### 3. Create Database Migration

```bash
python scripts/migration-manager.py create add_[feature]_table
```

Edit the migration file:

```sql
-- UP MIGRATION
BEGIN;

CREATE TABLE IF NOT EXISTS [feature-plural] (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_[feature-plural]_tenant_id ON [feature-plural](tenant_id);

COMMIT;

-- DOWN MIGRATION
BEGIN;

DROP TABLE IF EXISTS [feature-plural];

COMMIT;
```

### 4. Add Tests

Create `tests/unit/test_[feature].py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_create_[feature]():
    """Test creating a [feature]"""
    # Test implementation
    pass


def test_get_[feature]():
    """Test getting a [feature]"""
    # Test implementation
    pass
```

### 5. Update Documentation

- Add endpoint to `docs/api.md`
- Update OpenAPI schema (auto-generated)
- Add examples if needed

### 6. Checklist

- [ ] Route handler created
- [ ] Route registered
- [ ] Database migration created and tested
- [ ] Tests written
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Tenant isolation verified
- [ ] Input validation added
- [ ] Security checks added
