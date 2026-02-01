# 04 - Core Service API Implementation Guide

## Overview

This guide covers implementing the main FastAPI backend service that provides REST APIs for all core functionality: rules, scans, devices, applications, and actions.

---

## Prerequisites

- Database schema implemented (see [02_Database_Schema.md](02_Database_Schema.md))
- Authentication service complete (see [03_Auth_Service.md](03_Auth_Service.md))
- Docker environment running

---

## Step 1: FastAPI Application Setup

📝 **PROMPT: Create FastAPI application with middleware**
```
Create a FastAPI application with:
- CORS middleware for desktop app
- Request logging middleware with structlog
- Error handling middleware
- Health check endpoint
- API versioning (v1)
- OpenAPI documentation
```

**File: `services/core-service/src/core_service/main.py`**

```python
"""FastAPI main application."""

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from core_service.config import get_settings
from core_service.database import init_db, close_db
from core_service.routes import rules, scans, devices, applications, actions, dashboard


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("Starting Core Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Core Service...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="IT Operations AI Agent - Core Service",
        description="Backend API for device and application management",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS for desktop app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable):
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
            )
            raise
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": type(exc).__name__,
            },
        )
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "core-service"}
    
    # Include routers
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(rules.router, prefix="/api/v1")
    app.include_router(scans.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(applications.router, prefix="/api/v1")
    app.include_router(actions.router, prefix="/api/v1")
    
    return app


app = create_app()
```

---

## Step 2: Database Session Management

**File: `services/core-service/src/core_service/database.py`**

```python
"""Database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core_service.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool if settings.testing else None,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database connection."""
    async with engine.begin() as conn:
        # Test connection
        await conn.execute("SELECT 1")


async def close_db():
    """Close database connections."""
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Step 3: Pydantic Schemas

📝 **PROMPT: Create Pydantic models for API request/response validation**
```
Create Pydantic models for:
- Rule CRUD operations
- Scan operations
- Device queries
- Application queries
- Action requests
Include proper validation, examples, and JSON schema customization.
```

**File: `services/core-service/src/core_service/schemas/rules.py`**

```python
"""Rule schemas for API validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ConditionSchema(BaseModel):
    """Single condition in a rule."""
    field: str = Field(..., description="Field to evaluate")
    operator: str = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "free_disk_gb",
                "operator": "lt",
                "value": 10
            }
        }
    }


class ConditionGroupSchema(BaseModel):
    """Group of conditions with logic operator."""
    logic: str = Field(..., pattern="^(AND|OR)$")
    conditions: List["ConditionSchema | ConditionGroupSchema"]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "logic": "AND",
                "conditions": [
                    {"field": "operating_system", "operator": "contains", "value": "Windows 10"},
                    {"field": "free_disk_gb", "operator": "lt", "value": 10}
                ]
            }
        }
    }


# Forward reference for recursive type
ConditionGroupSchema.model_rebuild()


class RuleCreate(BaseModel):
    """Schema for creating a rule."""
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    entity_type: str = Field(..., pattern="^(devices|applications|both)$")
    conditions: ConditionGroupSchema
    is_template: bool = False
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Low Disk Space - Windows 10",
                "description": "Find Windows 10 devices with less than 10GB free",
                "entity_type": "devices",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {"field": "operating_system", "operator": "contains", "value": "Windows 10"},
                        {"field": "free_disk_gb", "operator": "lt", "value": 10}
                    ]
                },
                "severity": "high"
            }
        }
    }


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    conditions: Optional[ConditionGroupSchema] = None
    is_active: Optional[bool] = None
    severity: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    tags: Optional[List[str]] = None


class RuleResponse(BaseModel):
    """Schema for rule response."""
    id: UUID
    name: str
    description: Optional[str]
    entity_type: str
    conditions: Dict[str, Any]
    is_active: bool
    is_template: bool
    category: Optional[str]
    tags: List[str]
    severity: str
    created_by_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    last_scan_at: Optional[datetime]
    total_scans: int
    
    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    """Paginated list of rules."""
    items: List[RuleResponse]
    total: int
    page: int
    page_size: int
    pages: int
```

**File: `services/core-service/src/core_service/schemas/scans.py`**

```python
"""Scan schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    """Request to create a new scan."""
    rule_id: UUID = Field(..., description="Rule to execute")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule for later")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rule_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }


class ScanResultItem(BaseModel):
    """Single result from a scan."""
    entity_id: str
    entity_name: str
    entity_type: str
    severity: str
    matched_conditions: List[str]
    details: Dict[str, Any]
    
    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    """Scan execution response."""
    id: UUID
    rule_id: UUID
    rule_name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_scanned: int
    total_matched: int
    error_message: Optional[str]
    created_by_id: Optional[UUID]
    
    model_config = {"from_attributes": True}


class ScanDetailResponse(ScanResponse):
    """Scan with results."""
    results: List[ScanResultItem]
    severity_breakdown: Dict[str, int]
    duration_seconds: Optional[float]


class ScanListResponse(BaseModel):
    """Paginated scan list."""
    items: List[ScanResponse]
    total: int
    page: int
    page_size: int
```

**File: `services/core-service/src/core_service/schemas/devices.py`**

```python
"""Device schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):
    """Device information."""
    id: str = Field(..., description="MECM Resource ID")
    name: str = Field(..., description="Device name/hostname")
    operating_system: str
    os_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    last_active: Optional[datetime] = None
    last_hardware_scan: Optional[datetime] = None
    free_disk_gb: Optional[float] = None
    total_disk_gb: Optional[float] = None
    memory_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    missing_critical_patches: int = 0
    missing_patches_total: int = 0
    primary_user: Optional[str] = None
    ou_path: Optional[str] = None
    collections: List[str] = Field(default_factory=list)
    is_active: bool = True
    
    model_config = {"from_attributes": True}


class DeviceQueryParams(BaseModel):
    """Query parameters for device search."""
    search: Optional[str] = None
    operating_system: Optional[str] = None
    manufacturer: Optional[str] = None
    min_disk_free: Optional[float] = None
    max_disk_free: Optional[float] = None
    inactive_days: Optional[int] = None
    has_missing_patches: Optional[bool] = None
    collection: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)
    sort_by: str = "name"
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")


class DeviceListResponse(BaseModel):
    """Paginated device list."""
    items: List[DeviceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DeviceDetailResponse(DeviceResponse):
    """Device with additional details."""
    installed_software: List[Dict[str, Any]] = []
    patch_history: List[Dict[str, Any]] = []
    collection_memberships: List[Dict[str, Any]] = []
    recent_issues: List[Dict[str, Any]] = []
```

---

## Step 4: Rules API Routes

📝 **PROMPT: Create CRUD routes for rules management**
```
Create FastAPI routes for:
- GET /rules - List rules with filtering and pagination
- GET /rules/{id} - Get single rule
- POST /rules - Create rule
- PUT /rules/{id} - Update rule
- DELETE /rules/{id} - Soft delete rule
- POST /rules/{id}/clone - Clone a rule
- GET /rules/templates - Get rule templates
Include proper authentication and authorization.
```

**File: `services/core-service/src/core_service/routes/rules.py`**

```python
"""Rules API routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.database import get_db
from core_service.models import Rule, User
from core_service.schemas.rules import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleListResponse,
)
from core_service.auth import get_current_user, require_role


router = APIRouter(prefix="/rules", tags=["Rules"])


@router.get("", response_model=RuleListResponse)
async def list_rules(
    search: Optional[str] = Query(None, description="Search in name/description"),
    entity_type: Optional[str] = Query(None, pattern="^(devices|applications|both)$"),
    is_active: Optional[bool] = Query(None),
    is_template: bool = Query(False),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List rules with filtering and pagination.
    
    Accessible by: All authenticated users
    """
    # Build query
    query = select(Rule).where(Rule.deleted_at.is_(None))
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Rule.name.ilike(search_filter)) |
            (Rule.description.ilike(search_filter))
        )
    
    if entity_type:
        query = query.where(Rule.entity_type == entity_type)
    
    if is_active is not None:
        query = query.where(Rule.is_active == is_active)
    
    query = query.where(Rule.is_template == is_template)
    
    if category:
        query = query.where(Rule.category == category)
    
    if severity:
        query = query.where(Rule.severity == severity)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply sorting
    sort_column = getattr(Rule, sort_by, Rule.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return RuleListResponse(
        items=[RuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/templates", response_model=List[RuleResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List available rule templates.
    """
    query = (
        select(Rule)
        .where(Rule.is_template == True)
        .where(Rule.deleted_at.is_(None))
    )
    
    if category:
        query = query.where(Rule.category == category)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [RuleResponse.model_validate(t) for t in templates]


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific rule by ID.
    """
    query = select(Rule).where(Rule.id == rule_id).where(Rule.deleted_at.is_(None))
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    return RuleResponse.model_validate(rule)


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Create a new rule.
    
    Requires: Operator or Admin role
    """
    # Create rule
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        entity_type=rule_data.entity_type,
        conditions=rule_data.conditions.model_dump(),
        is_template=rule_data.is_template,
        category=rule_data.category,
        tags=rule_data.tags,
        severity=rule_data.severity,
        created_by_id=current_user.id,
    )
    
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    
    return RuleResponse.model_validate(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Update an existing rule.
    
    Requires: Operator or Admin role
    """
    query = select(Rule).where(Rule.id == rule_id).where(Rule.deleted_at.is_(None))
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    # Update fields
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "conditions" and value:
            setattr(rule, field, value.model_dump() if hasattr(value, 'model_dump') else value)
        else:
            setattr(rule, field, value)
    
    await db.flush()
    await db.refresh(rule)
    
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Soft delete a rule.
    
    Requires: Admin role
    """
    from datetime import datetime
    
    query = select(Rule).where(Rule.id == rule_id).where(Rule.deleted_at.is_(None))
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    rule.deleted_at = datetime.utcnow()
    await db.flush()


@router.post("/{rule_id}/clone", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def clone_rule(
    rule_id: UUID,
    new_name: Optional[str] = Query(None, min_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Clone an existing rule or template.
    
    Requires: Operator or Admin role
    """
    query = select(Rule).where(Rule.id == rule_id).where(Rule.deleted_at.is_(None))
    result = await db.execute(query)
    source_rule = result.scalar_one_or_none()
    
    if not source_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    # Create clone
    clone = Rule(
        name=new_name or f"{source_rule.name} (Copy)",
        description=source_rule.description,
        entity_type=source_rule.entity_type,
        conditions=source_rule.conditions,
        is_template=False,  # Clones are never templates
        category=source_rule.category,
        tags=source_rule.tags.copy(),
        severity=source_rule.severity,
        created_by_id=current_user.id,
    )
    
    db.add(clone)
    await db.flush()
    await db.refresh(clone)
    
    return RuleResponse.model_validate(clone)
```

---

## Step 5: Scans API Routes

**File: `services/core-service/src/core_service/routes/scans.py`**

```python
"""Scans API routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.database import get_db
from core_service.models import Rule, Scan, ScanResult, ScanStatus, User
from core_service.schemas.scans import (
    ScanCreate,
    ScanResponse,
    ScanDetailResponse,
    ScanListResponse,
)
from core_service.auth import get_current_user, require_role
from core_service.tasks import execute_scan_task


router = APIRouter(prefix="/scans", tags=["Scans"])


@router.get("", response_model=ScanListResponse)
async def list_scans(
    rule_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|failed)$"),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List scans with filtering.
    """
    query = select(Scan)
    
    if rule_id:
        query = query.where(Scan.rule_id == rule_id)
    
    if status:
        query = query.where(Scan.status == ScanStatus(status))
    
    if created_after:
        query = query.where(Scan.created_at >= created_after)
    
    if created_before:
        query = query.where(Scan.created_at <= created_before)
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Pagination and sort
    query = query.order_by(Scan.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    scans = result.scalars().all()
    
    # Get rule names
    rule_ids = {s.rule_id for s in scans}
    rules_query = select(Rule).where(Rule.id.in_(rule_ids))
    rules_result = await db.execute(rules_query)
    rules_map = {r.id: r.name for r in rules_result.scalars().all()}
    
    items = []
    for scan in scans:
        scan_data = ScanResponse.model_validate(scan)
        scan_data.rule_name = rules_map.get(scan.rule_id, "Unknown")
        items.append(scan_data)
    
    return ScanListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: UUID,
    include_results: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get scan details with results.
    """
    query = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(query)
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    # Get rule name
    rule_query = select(Rule.name).where(Rule.id == scan.rule_id)
    rule_result = await db.execute(rule_query)
    rule_name = rule_result.scalar() or "Unknown"
    
    # Get results
    results = []
    severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    if include_results:
        results_query = select(ScanResult).where(ScanResult.scan_id == scan_id)
        results_result = await db.execute(results_query)
        
        for sr in results_result.scalars().all():
            results.append({
                "entity_id": sr.entity_id,
                "entity_name": sr.entity_name,
                "entity_type": sr.entity_type,
                "severity": sr.severity,
                "matched_conditions": sr.matched_conditions,
                "details": sr.details,
            })
            severity_breakdown[sr.severity] = severity_breakdown.get(sr.severity, 0) + 1
    
    # Calculate duration
    duration = None
    if scan.started_at and scan.completed_at:
        duration = (scan.completed_at - scan.started_at).total_seconds()
    
    return ScanDetailResponse(
        id=scan.id,
        rule_id=scan.rule_id,
        rule_name=rule_name,
        status=scan.status.value,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        total_scanned=scan.total_scanned,
        total_matched=scan.total_matched,
        error_message=scan.error_message,
        created_by_id=scan.created_by_id,
        results=results,
        severity_breakdown=severity_breakdown,
        duration_seconds=duration,
    )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Create and execute a new scan.
    
    Requires: Operator or Admin role
    """
    # Verify rule exists
    rule_query = select(Rule).where(Rule.id == scan_data.rule_id).where(Rule.deleted_at.is_(None))
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {scan_data.rule_id} not found"
        )
    
    # Create scan record
    scan = Scan(
        rule_id=scan_data.rule_id,
        status=ScanStatus.PENDING,
        created_by_id=current_user.id,
    )
    
    db.add(scan)
    await db.flush()
    await db.refresh(scan)
    
    # Execute in background
    if scan_data.scheduled_at:
        # TODO: Schedule for later (use Celery beat)
        pass
    else:
        background_tasks.add_task(execute_scan_task, str(scan.id))
    
    return ScanResponse(
        id=scan.id,
        rule_id=scan.rule_id,
        rule_name=rule.name,
        status=scan.status.value,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        total_scanned=scan.total_scanned,
        total_matched=scan.total_matched,
        error_message=scan.error_message,
        created_by_id=scan.created_by_id,
    )


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Cancel a running or pending scan.
    """
    query = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(query)
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found"
        )
    
    if scan.status not in (ScanStatus.PENDING, ScanStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel scan in {scan.status.value} status"
        )
    
    scan.status = ScanStatus.FAILED
    scan.completed_at = datetime.utcnow()
    scan.error_message = "Cancelled by user"
    
    await db.flush()
    
    # Get rule name
    rule_query = select(Rule.name).where(Rule.id == scan.rule_id)
    rule_result = await db.execute(rule_query)
    rule_name = rule_result.scalar() or "Unknown"
    
    return ScanResponse(
        id=scan.id,
        rule_id=scan.rule_id,
        rule_name=rule_name,
        status=scan.status.value,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        total_scanned=scan.total_scanned,
        total_matched=scan.total_matched,
        error_message=scan.error_message,
        created_by_id=scan.created_by_id,
    )
```

---

## Step 6: Dashboard API Routes

**File: `services/core-service/src/core_service/routes/dashboard.py`**

```python
"""Dashboard API routes."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.database import get_db
from core_service.models import Rule, Scan, ScanResult, ScanStatus, ActionRequest, User
from core_service.auth import get_current_user


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get dashboard summary statistics.
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Active rules count
    rules_query = select(func.count(Rule.id)).where(
        Rule.is_active == True,
        Rule.deleted_at.is_(None),
    )
    rules_result = await db.execute(rules_query)
    active_rules = rules_result.scalar() or 0
    
    # Scans in last 24h
    scans_24h_query = select(func.count(Scan.id)).where(
        Scan.created_at >= last_24h
    )
    scans_24h_result = await db.execute(scans_24h_query)
    scans_24h = scans_24h_result.scalar() or 0
    
    # Issues found (results from last 7 days)
    issues_query = select(func.count(ScanResult.id)).where(
        ScanResult.created_at >= last_7d
    )
    issues_result = await db.execute(issues_query)
    total_issues = issues_result.scalar() or 0
    
    # Critical issues
    critical_query = select(func.count(ScanResult.id)).where(
        ScanResult.severity == "critical",
        ScanResult.created_at >= last_7d,
    )
    critical_result = await db.execute(critical_query)
    critical_issues = critical_result.scalar() or 0
    
    # Pending actions
    actions_query = select(func.count(ActionRequest.id)).where(
        ActionRequest.status == "pending"
    )
    actions_result = await db.execute(actions_query)
    pending_actions = actions_result.scalar() or 0
    
    return {
        "active_rules": active_rules,
        "scans_24h": scans_24h,
        "total_issues_7d": total_issues,
        "critical_issues_7d": critical_issues,
        "pending_actions": pending_actions,
        "last_updated": now.isoformat(),
    }


@router.get("/severity-trends")
async def get_severity_trends(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get severity trends over time.
    """
    from sqlalchemy import cast, Date
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Group by date and severity
    query = (
        select(
            cast(ScanResult.created_at, Date).label("date"),
            ScanResult.severity,
            func.count(ScanResult.id).label("count"),
        )
        .where(ScanResult.created_at >= start_date)
        .group_by(cast(ScanResult.created_at, Date), ScanResult.severity)
        .order_by(cast(ScanResult.created_at, Date))
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Transform to list of date records
    trends = {}
    for row in rows:
        date_str = row.date.isoformat()
        if date_str not in trends:
            trends[date_str] = {"date": date_str, "critical": 0, "high": 0, "medium": 0, "low": 0}
        trends[date_str][row.severity] = row.count
    
    return list(trends.values())


@router.get("/recent-scans")
async def get_recent_scans(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get most recent scans.
    """
    query = (
        select(Scan, Rule.name)
        .join(Rule, Scan.rule_id == Rule.id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    scans = result.all()
    
    return [
        {
            "id": str(scan.id),
            "rule_name": rule_name,
            "status": scan.status.value,
            "total_matched": scan.total_matched,
            "created_at": scan.created_at.isoformat(),
            "duration": (
                (scan.completed_at - scan.started_at).total_seconds()
                if scan.started_at and scan.completed_at
                else None
            ),
        }
        for scan, rule_name in scans
    ]


@router.get("/top-issues")
async def get_top_issues(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get entities with most issues.
    """
    last_7d = datetime.utcnow() - timedelta(days=7)
    
    query = (
        select(
            ScanResult.entity_name,
            ScanResult.entity_type,
            func.count(ScanResult.id).label("issue_count"),
            func.max(ScanResult.severity).label("max_severity"),
        )
        .where(ScanResult.created_at >= last_7d)
        .group_by(ScanResult.entity_name, ScanResult.entity_type)
        .order_by(func.count(ScanResult.id).desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "entity_name": row.entity_name,
            "entity_type": row.entity_type,
            "issue_count": row.issue_count,
            "max_severity": row.max_severity,
        }
        for row in rows
    ]
```

---

## Step 7: Devices and Applications Routes

**File: `services/core-service/src/core_service/routes/devices.py`**

```python
"""Devices API routes - proxies to MECM connector."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import httpx

from core_service.config import get_settings
from core_service.models import User
from core_service.auth import get_current_user


router = APIRouter(prefix="/devices", tags=["Devices"])
settings = get_settings()


@router.get("")
async def list_devices(
    search: Optional[str] = Query(None),
    operating_system: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    min_disk_free: Optional[float] = Query(None),
    inactive_days: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """
    List devices from MECM.
    """
    params = {
        "search": search,
        "operating_system": operating_system,
        "manufacturer": manufacturer,
        "min_disk_free": min_disk_free,
        "inactive_days": inactive_days,
        "page": page,
        "page_size": page_size,
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.mecm_connector_url}/api/devices",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"MECM connector unavailable: {str(e)}"
            )


@router.get("/{device_id}")
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get device details from MECM.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.mecm_connector_url}/api/devices/{device_id}",
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Device {device_id} not found"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text
            )


@router.get("/{device_id}/software")
async def get_device_software(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get software installed on a device.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mecm_connector_url}/api/devices/{device_id}/software",
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


@router.get("/{device_id}/patches")
async def get_device_patches(
    device_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get patch compliance status for a device.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mecm_connector_url}/api/devices/{device_id}/patches",
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
```

**File: `services/core-service/src/core_service/routes/applications.py`**

```python
"""Applications API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from core_service.config import get_settings
from core_service.models import User
from core_service.auth import get_current_user


router = APIRouter(prefix="/applications", tags=["Applications"])
settings = get_settings()


@router.get("")
async def list_applications(
    search: Optional[str] = Query(None),
    publisher: Optional[str] = Query(None),
    min_install_count: Optional[int] = Query(None),
    has_vulnerabilities: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """
    List applications from MECM software inventory.
    """
    params = {
        "search": search,
        "publisher": publisher,
        "min_install_count": min_install_count,
        "has_vulnerabilities": has_vulnerabilities,
        "page": page,
        "page_size": page_size,
    }
    params = {k: v for k, v in params.items() if v is not None}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.mecm_connector_url}/api/applications",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"MECM connector unavailable: {str(e)}"
            )


@router.get("/{app_id}")
async def get_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get application details.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mecm_connector_url}/api/applications/{app_id}",
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


@router.get("/{app_id}/installations")
async def get_app_installations(
    app_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """
    Get devices where application is installed.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mecm_connector_url}/api/applications/{app_id}/installations",
            params={"page": page, "page_size": page_size},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
```

---

## Step 8: Actions API Routes

**File: `services/core-service/src/core_service/routes/actions.py`**

```python
"""Actions API routes."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.database import get_db
from core_service.models import ActionRequest, ActionLog, User, ActionStatus, ActionType
from core_service.auth import get_current_user, require_role


router = APIRouter(prefix="/actions", tags=["Actions"])


class ActionCreateRequest(BaseModel):
    """Request to create an action."""
    action_type: str = Field(..., description="Type of action")
    target_ids: List[str] = Field(..., min_length=1)
    target_type: str = Field(..., pattern="^(device|application|collection)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., min_length=10, max_length=500)
    scan_id: Optional[UUID] = None


class ActionResponse(BaseModel):
    """Action response."""
    id: UUID
    action_type: str
    status: str
    target_count: int
    reason: str
    created_at: datetime
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by_id: UUID
    approved_by_id: Optional[UUID]
    
    model_config = {"from_attributes": True}


@router.get("")
async def list_actions(
    status: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List action requests.
    """
    query = select(ActionRequest)
    
    if status:
        query = query.where(ActionRequest.status == ActionStatus(status))
    
    if action_type:
        query = query.where(ActionRequest.action_type == ActionType(action_type))
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    query = query.order_by(ActionRequest.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    return {
        "items": [ActionResponse.model_validate(a) for a in actions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    action_data: ActionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["operator", "admin"])),
):
    """
    Create a new action request.
    
    Requires: Operator or Admin role
    """
    # Create action
    action = ActionRequest(
        action_type=ActionType(action_data.action_type),
        status=ActionStatus.PENDING,
        target_ids=action_data.target_ids,
        target_type=action_data.target_type,
        parameters=action_data.parameters,
        reason=action_data.reason,
        scan_id=action_data.scan_id,
        created_by_id=current_user.id,
    )
    
    db.add(action)
    await db.flush()
    await db.refresh(action)
    
    return ActionResponse.model_validate(action)


@router.post("/{action_id}/approve", response_model=ActionResponse)
async def approve_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Approve a pending action.
    
    Requires: Admin role
    """
    query = select(ActionRequest).where(ActionRequest.id == action_id)
    result = await db.execute(query)
    action = result.scalar_one_or_none()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.status != ActionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve action in {action.status.value} status"
        )
    
    action.status = ActionStatus.APPROVED
    action.approved_at = datetime.utcnow()
    action.approved_by_id = current_user.id
    
    await db.flush()
    
    # TODO: Queue action for execution
    
    return ActionResponse.model_validate(action)


@router.post("/{action_id}/reject", response_model=ActionResponse)
async def reject_action(
    action_id: UUID,
    reason: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    Reject a pending action.
    
    Requires: Admin role
    """
    query = select(ActionRequest).where(ActionRequest.id == action_id)
    result = await db.execute(query)
    action = result.scalar_one_or_none()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.status != ActionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject action in {action.status.value} status"
        )
    
    action.status = ActionStatus.REJECTED
    action.completed_at = datetime.utcnow()
    action.error_message = f"Rejected by admin: {reason}"
    
    await db.flush()
    
    return ActionResponse.model_validate(action)


@router.get("/{action_id}/logs")
async def get_action_logs(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get execution logs for an action.
    """
    query = (
        select(ActionLog)
        .where(ActionLog.action_request_id == action_id)
        .order_by(ActionLog.created_at)
    )
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "level": log.level,
            "message": log.message,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
```

---

## Verification

### Test the APIs

```powershell
# Start the service
cd services/core-service
uvicorn core_service.main:app --reload --port 8001

# Test health endpoint
curl http://localhost:8001/health

# Test dashboard (requires auth)
curl http://localhost:8001/api/v1/dashboard/summary -H "Authorization: Bearer <token>"

# Test rules list
curl http://localhost:8001/api/v1/rules -H "Authorization: Bearer <token>"

# Create a rule
curl -X POST http://localhost:8001/api/v1/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Low Disk Space",
    "entity_type": "devices",
    "conditions": {
      "logic": "AND",
      "conditions": [
        {"field": "free_disk_gb", "operator": "lt", "value": 10}
      ]
    }
  }'
```

### Access API Documentation

Open `http://localhost:8001/api/docs` for Swagger UI.

---

## Common Issues

### Issue: CORS errors from desktop app

**Solution:** Ensure `localhost` and `127.0.0.1` are in CORS origins:

```python
cors_origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
```

### Issue: Database connection timeouts

**Solution:** Use connection pooling and set appropriate timeouts:

```python
engine = create_async_engine(
    url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
```

---

## Next Steps

→ [06_MECM_Connector.md](06_MECM_Connector.md) - Implement MECM data source

---

**Checkpoint:** You should now have:
- [ ] FastAPI application running with middleware
- [ ] Database session management working
- [ ] Rules CRUD endpoints functional
- [ ] Scans endpoints functional
- [ ] Dashboard endpoints returning data
- [ ] Devices/Applications proxying to MECM connector
- [ ] Actions workflow started
- [ ] API documentation accessible
