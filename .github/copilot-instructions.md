# GitHub Copilot Instructions

## Project Overview

This is the **IT Operations AI Agent** project - an AI-powered tool for IT operations teams to create, manage, and execute device compliance rules using natural language. The system integrates with MECM, ServiceNow, and Tachyon (1E) for device management and remediation.

## Tech Stack

### Backend Services (Python 3.11+)
- **FastAPI 0.100+** - Async REST APIs with Pydantic 2.0 validation
- **SQLAlchemy 2.0** - Async ORM with asyncpg driver
- **PostgreSQL 15+** - Primary database
- **Redis 7+** - Caching and Celery broker
- **Celery** - Async task queue for action execution
- **Alembic** - Database migrations

### Desktop Application
- **PySide6 (Qt 6.5+)** - Cross-platform desktop UI
- **MVVM Pattern** - ViewModels with Qt signals/slots
- **Supports**: Windows 10/11, macOS 12+ (Intel & Apple Silicon)

### AI/LLM Integration
- **LangChain 0.1+** - LLM orchestration
- **OpenAI / Azure OpenAI / QWEN** - LLM providers
- **Sensitive data filtering** - PII masking before LLM calls

### Authentication
- **Azure AD OAuth 2.0** - Via MSAL library
- **JWT tokens** - python-jose for validation

### External Integrations
- **MECM** - SQL Server via aioodbc
- **ServiceNow** - REST API for incidents/changes
- **Tachyon (1E)** - Real-time device queries/actions

## Project Structure

```
AIAgent/
├── services/
│   ├── core-service/         # Main API (FastAPI)
│   ├── auth-service/         # Authentication
│   ├── mecm-connector/       # MECM integration
│   ├── servicenow-connector/ # ServiceNow integration
│   ├── tachyon-connector/    # Tachyon integration
│   ├── llm-service/          # LLM provider abstraction
│   └── action-worker/        # Celery worker
├── desktop/                  # PySide6 desktop app
├── tests/                    # Test suites
├── k8s/                      # Kubernetes manifests
└── implementationDetails/    # Implementation guides
```

## Coding Conventions

### Python Style
- Use **type hints** for all function parameters and returns
- Use **async/await** for all I/O operations
- Use **Pydantic models** for request/response validation
- Use **structlog** for structured logging
- Follow **PEP 8** with 100 char line limit

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Import Order
1. Standard library
2. Third-party packages
3. Local imports

### Example Code Pattern

```python
"""Module docstring describing purpose."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from core_service.models import Rule
from core_service.services import RuleService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/rules", tags=["Rules"])


class RuleCreate(BaseModel):
    """Request model for creating a rule."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    conditions: Dict[str, Any]


class RuleResponse(BaseModel):
    """Response model for rule data."""
    id: UUID
    name: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=RuleResponse)
async def create_rule(
    request: RuleCreate,
    service: RuleService = Depends(),
) -> RuleResponse:
    """Create a new compliance rule."""
    try:
        rule = await service.create(request)
        logger.info("Rule created", rule_id=str(rule.id))
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Database Models

```python
from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Rule(Base):
    __tablename__ = "rules"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### PySide6 ViewModel Pattern

```python
from PySide6.QtCore import QObject, Signal, Property, Slot


class BaseViewModel(QObject):
    """Base class for ViewModels."""
    
    is_loading_changed = Signal()
    error_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self._is_loading = False
        self._error = ""
    
    @Property(bool, notify=is_loading_changed)
    def is_loading(self) -> bool:
        return self._is_loading
    
    @is_loading.setter
    def is_loading(self, value: bool):
        if self._is_loading != value:
            self._is_loading = value
            self.is_loading_changed.emit()
```

## Key Implementation Details

### LLM Integration
- Always filter sensitive data before sending to LLM
- Use prompt templates from `llm_service/prompts.py`
- Implement retry logic with tenacity

### MECM Queries
- Use parameterized queries to prevent SQL injection
- Implement connection pooling
- Cache frequently accessed data in Redis

### Action Workflow
- All remediation actions require approval (configurable by severity)
- Actions are executed via Celery workers
- Track status: pending → approved → in_progress → completed/failed

### Error Handling
- Use custom exception classes
- Return appropriate HTTP status codes
- Log errors with context using structlog

## Testing

- Use **pytest** with pytest-asyncio for async tests
- Mock external services (MECM, ServiceNow, Tachyon)
- Implement ground truth testing for LLM outputs
- Target: >80% code coverage

## Implementation Guide References

When working on specific components, **always read the relevant guide first**:

| Component | Guide | Key Content |
|-----------|-------|-------------|
| Project setup | [01_Project_Setup.md](implementationDetails/01_Project_Setup.md) | Dependencies, folder structure, environment |
| Database models | [02_Database_Schema.md](implementationDetails/02_Database_Schema.md) | SQLAlchemy models, Alembic migrations |
| Authentication | [03_Auth_Service.md](implementationDetails/03_Auth_Service.md) | Azure AD, MSAL, JWT tokens |
| Core API | [04_Core_Service_API.md](implementationDetails/04_Core_Service_API.md) | FastAPI routes, Pydantic schemas |
| Rule engine | [05_Rule_Engine.md](implementationDetails/05_Rule_Engine.md) | Condition parsing, rule execution |
| MECM connector | [06_MECM_Connector.md](implementationDetails/06_MECM_Connector.md) | SQL queries, device repository |
| Desktop app | [07_Desktop_App.md](implementationDetails/07_Desktop_App.md) | PySide6, MVVM, views, styling |
| LLM service | [08_LLM_Service.md](implementationDetails/08_LLM_Service.md) | Providers, PII filtering, prompts |
| Testing | [09_Ground_Truth_Testing.md](implementationDetails/09_Ground_Truth_Testing.md) | Test framework, LLM evaluation |
| ServiceNow | [10_ServiceNow_Connector.md](implementationDetails/10_ServiceNow_Connector.md) | Incidents, changes, CMDB |
| Tachyon | [11_Tachyon_Connector.md](implementationDetails/11_Tachyon_Connector.md) | Instructions, device queries |
| Action worker | [12_Action_Worker.md](implementationDetails/12_Action_Worker.md) | Celery tasks, approval workflow |
| Deployment | [13_Deployment.md](implementationDetails/13_Deployment.md) | Docker, K8s, CI/CD, desktop builds |
| Non-coding tasks | [14_Non_Coding_Checklist.md](implementationDetails/14_Non_Coding_Checklist.md) | Infrastructure, security, approvals |

## Do NOT

- Hardcode credentials or secrets
- Use synchronous I/O in async contexts
- Skip type hints
- Ignore error handling
- Create database connections without pooling
- Send PII to LLM without filtering
