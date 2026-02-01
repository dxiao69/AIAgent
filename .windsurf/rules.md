# Windsurf AI Rules

## Project Context

**IT Operations AI Agent** - An AI-powered tool for IT operations teams to manage device compliance using natural language. Integrates with MECM, ServiceNow, and Tachyon for enterprise device management.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI 0.100+, Python 3.11+ |
| Database | PostgreSQL 15+, SQLAlchemy 2.0 async |
| Cache/Queue | Redis 7+, Celery |
| Desktop | PySide6 (Qt 6.5+), MVVM pattern |
| LLM | LangChain, OpenAI/Azure OpenAI/QWEN |
| Auth | Azure AD OAuth, MSAL, JWT |
| Integrations | MECM (SQL), ServiceNow (REST), Tachyon (REST) |

## Directory Structure

```
services/
├── core-service/         # FastAPI - main API
├── auth-service/         # FastAPI - authentication  
├── mecm-connector/       # FastAPI - MECM queries
├── servicenow-connector/ # FastAPI - incident/change mgmt
├── tachyon-connector/    # FastAPI - real-time device ops
├── llm-service/          # FastAPI - LLM abstraction
└── action-worker/        # Celery - task execution

desktop/                  # PySide6 desktop application
tests/                    # pytest test suites
k8s/                      # Kubernetes deployment
```

## Code Style Rules

### Always Use
- Type hints on all functions
- Async/await for I/O operations
- Pydantic models for validation
- structlog for logging
- Dependency injection with FastAPI Depends()

### Naming
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Imports Order
```python
# 1. Standard library
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

# 2. Third-party
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

# 3. Local
from core_service.models import Rule
```

## Code Templates

### FastAPI Route
```python
@router.post("/", response_model=ResponseModel)
async def create_item(
    request: CreateRequest,
    service: ItemService = Depends(),
) -> ResponseModel:
    """Endpoint docstring."""
    try:
        result = await service.create(request)
        logger.info("Item created", item_id=str(result.id))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### SQLAlchemy Model
```python
class Entity(Base):
    __tablename__ = "entities"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### Pydantic Schema
```python
class ItemCreate(BaseModel):
    """Request model."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None

class ItemResponse(BaseModel):
    """Response model."""
    id: UUID
    name: str
    
    class Config:
        from_attributes = True
```

### PySide6 ViewModel
```python
class ItemViewModel(QObject):
    items_changed = Signal()
    is_loading_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._items: List[Item] = []
        self._is_loading = False
    
    @Property(list, notify=items_changed)
    def items(self) -> List[Item]:
        return self._items
    
    @Slot()
    def load_items(self):
        self._is_loading = True
        self.is_loading_changed.emit()
        # async load...
```

### Async HTTP Client
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{settings.service_url}/api/endpoint",
        json=request.model_dump(),
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()
```

## Domain-Specific Patterns

### LLM Calls - Always Filter PII
```python
# Filter before sending to LLM
filtered_text = sensitive_data_filter.filter(user_input)
response = await llm_service.generate(filtered_text)
```

### MECM Queries - Use Parameters
```python
# NEVER concatenate strings - use parameters
query = "SELECT * FROM v_R_System WHERE Name0 = ?"
result = await connection.execute(query, [device_name])
```

### Action Workflow States
```
pending → pending_approval → approved → in_progress → completed/failed
                          → rejected
```

### Error Logging Pattern
```python
logger.error(
    "Operation failed",
    error=str(e),
    entity_id=str(entity_id),
    operation="create",
)
raise HTTPException(status_code=500, detail="Internal error")
```

## Cross-Platform Desktop Notes

- Desktop app must run on **Windows 10/11** and **macOS 12+**
- Use `QSettings` for platform-appropriate config storage
- Test keyboard shortcuts on both platforms (Ctrl vs Cmd)
- macOS menu bar is separate from window

## Testing Patterns

```python
@pytest.mark.asyncio
async def test_create_rule():
    service = RuleService(mock_repo)
    result = await service.create(RuleCreate(name="Test"))
    assert result.id is not None
```

## Prohibited Practices

❌ Hardcoded credentials or secrets  
❌ Synchronous I/O in async functions  
❌ Missing type hints  
❌ Raw string SQL concatenation  
❌ Sending unfiltered PII to LLM  
❌ Database connections without pooling  
❌ Catching exceptions without logging  
❌ Missing error handling on external calls  

## Implementation Guide References

When working on specific components, refer to these guides:

| Component | Guide | Key Content |
|-----------|-------|-------------|
| Project setup | [01_Project_Setup.md](../implementationDetails/01_Project_Setup.md) | Dependencies, folder structure, environment |
| Database models | [02_Database_Schema.md](../implementationDetails/02_Database_Schema.md) | SQLAlchemy models, Alembic migrations |
| Authentication | [03_Auth_Service.md](../implementationDetails/03_Auth_Service.md) | Azure AD, MSAL, JWT tokens |
| Core API | [04_Core_Service_API.md](../implementationDetails/04_Core_Service_API.md) | FastAPI routes, Pydantic schemas |
| Rule engine | [05_Rule_Engine.md](../implementationDetails/05_Rule_Engine.md) | Condition parsing, rule execution |
| MECM connector | [06_MECM_Connector.md](../implementationDetails/06_MECM_Connector.md) | SQL queries, device repository |
| Desktop app | [07_Desktop_App.md](../implementationDetails/07_Desktop_App.md) | PySide6, MVVM, views, styling |
| LLM service | [08_LLM_Service.md](../implementationDetails/08_LLM_Service.md) | Providers, PII filtering, prompts |
| Testing | [09_Ground_Truth_Testing.md](../implementationDetails/09_Ground_Truth_Testing.md) | Test framework, LLM evaluation |
| ServiceNow | [10_ServiceNow_Connector.md](../implementationDetails/10_ServiceNow_Connector.md) | Incidents, changes, CMDB |
| Tachyon | [11_Tachyon_Connector.md](../implementationDetails/11_Tachyon_Connector.md) | Instructions, device queries |
| Action worker | [12_Action_Worker.md](../implementationDetails/12_Action_Worker.md) | Celery tasks, approval workflow |
| Deployment | [13_Deployment.md](../implementationDetails/13_Deployment.md) | Docker, K8s, CI/CD, desktop builds |

**Always read the relevant guide before implementing a feature.**
