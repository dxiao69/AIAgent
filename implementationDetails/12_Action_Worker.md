# 12 - Action Worker Implementation Guide

## Overview

This guide covers implementing the Celery-based action worker for executing remediation actions with approval workflows. The action worker processes approved actions from a queue and coordinates with external systems.

---

## Prerequisites

- Core service API complete (see [04_Core_Service_API.md](04_Core_Service_API.md))
- ServiceNow connector complete (see [10_ServiceNow_Connector.md](10_ServiceNow_Connector.md))
- Tachyon connector complete (see [11_Tachyon_Connector.md](11_Tachyon_Connector.md))
- Redis running for Celery broker

---

## Step 1: Configuration

📝 **PROMPT: Create action worker configuration**
```
Create configuration for the Celery action worker:
- Redis broker URL and result backend
- Retry policies and timeouts
- Approval workflow settings
- Service endpoints for connectors
```

**File: `services/action-worker/src/action_worker/config.py`**

```python
"""Action worker configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Action worker settings."""
    
    # Service settings
    service_name: str = "action-worker"
    debug: bool = False
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_timezone: str = "UTC"
    
    # Task settings
    task_default_retry_delay: int = 60  # seconds
    task_max_retries: int = 3
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300  # 55 minutes
    
    # Approval workflow
    require_approval: bool = True
    auto_approve_low_severity: bool = False
    approval_timeout_hours: int = 72
    
    # Service endpoints
    core_service_url: str = "http://localhost:8001"
    servicenow_connector_url: str = "http://localhost:8004"
    tachyon_connector_url: str = "http://localhost:8005"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/itops_agent"
    
    # Redis for caching
    redis_url: str = "redis://localhost:6379/1"
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "WORKER_",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Step 2: Celery App Configuration

📝 **PROMPT: Create Celery application**
```
Create a Celery application with:
- Task routing for different action types
- Error handling and retry policies
- Task monitoring hooks
- Priority queues
```

**File: `services/action-worker/src/action_worker/celery_app.py`**

```python
"""Celery application configuration."""

from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    worker_ready,
)

import structlog

from action_worker.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create Celery app
app = Celery(
    "action_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
app.conf.update(
    # Serialization
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    
    # Task settings
    task_default_retry_delay=settings.task_default_retry_delay,
    task_annotations={
        "*": {
            "max_retries": settings.task_max_retries,
            "time_limit": settings.task_time_limit,
            "soft_time_limit": settings.task_soft_time_limit,
        },
    },
    
    # Queue settings
    task_queues={
        "high_priority": {
            "exchange": "high_priority",
            "routing_key": "high",
        },
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "low_priority": {
            "exchange": "low_priority",
            "routing_key": "low",
        },
    },
    task_default_queue="default",
    
    # Task routing
    task_routes={
        "action_worker.tasks.execute_action": {"queue": "default"},
        "action_worker.tasks.create_incident": {"queue": "default"},
        "action_worker.tasks.execute_tachyon_action": {"queue": "high_priority"},
        "action_worker.tasks.cleanup_completed_actions": {"queue": "low_priority"},
    },
    
    # Result settings
    result_expires=86400,  # 24 hours
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# Auto-discover tasks
app.autodiscover_tasks(["action_worker"])


# Signal handlers
@worker_ready.connect
def on_worker_ready(**kwargs):
    """Called when worker is ready."""
    logger.info("Action worker ready")


@task_prerun.connect
def on_task_prerun(task_id, task, args, kwargs, **extras):
    """Called before task execution."""
    logger.info(
        "Task starting",
        task_id=task_id,
        task_name=task.name,
    )


@task_postrun.connect
def on_task_postrun(task_id, task, args, kwargs, retval, state, **extras):
    """Called after task execution."""
    logger.info(
        "Task completed",
        task_id=task_id,
        task_name=task.name,
        state=state,
    )


@task_failure.connect
def on_task_failure(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """Called when task fails."""
    logger.error(
        "Task failed",
        task_id=task_id,
        exception=str(exception),
    )
```

---

## Step 3: Action Models

📝 **PROMPT: Create action data models**
```
Create data models for actions:
- Action entity with status tracking
- Action results with device outcomes
- Approval workflow states
```

**File: `services/action-worker/src/action_worker/models.py`**

```python
"""Action worker data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ActionStatus(str, Enum):
    """Action execution status."""
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Types of remediation actions."""
    CREATE_INCIDENT = "create_incident"
    CREATE_CHANGE = "create_change"
    RESTART_SERVICE = "restart_service"
    CLEAR_TEMP_FILES = "clear_temp_files"
    DEPLOY_PATCH = "deploy_patch"
    COLLECT_DATA = "collect_data"
    CUSTOM = "custom"


class ActionSeverity(str, Enum):
    """Action severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionRequest(BaseModel):
    """Request to create an action."""
    action_type: ActionType
    severity: ActionSeverity = ActionSeverity.MEDIUM
    title: str
    description: str
    target_devices: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    scan_id: Optional[str] = None
    rule_id: Optional[str] = None
    created_by: Optional[str] = None


class Action(BaseModel):
    """Action entity."""
    id: UUID
    action_type: ActionType
    severity: ActionSeverity
    title: str
    description: str
    status: ActionStatus
    target_devices: List[str]
    parameters: Dict[str, Any]
    scan_id: Optional[str] = None
    rule_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DeviceActionResult(BaseModel):
    """Result of action on a single device."""
    device: str
    success: bool
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None


class ActionResult(BaseModel):
    """Complete action result."""
    action_id: UUID
    status: ActionStatus
    device_results: List[DeviceActionResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime


class ApprovalRequest(BaseModel):
    """Request to approve/reject an action."""
    action_id: UUID
    approved: bool
    approver: str
    comment: Optional[str] = None
```

---

## Step 4: Action Repository

📝 **PROMPT: Create action repository**
```
Create a repository for action persistence:
- Store actions in PostgreSQL
- Track status changes
- Query actions by status and type
```

**File: `services/action-worker/src/action_worker/repository.py`**

```python
"""Action repository for persistence."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String, Text, DateTime, Enum as SQLEnum

import structlog

from action_worker.config import get_settings
from action_worker.models import Action, ActionStatus, ActionType, ActionSeverity

logger = structlog.get_logger()
settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy base class."""
    pass


class ActionModel(Base):
    """Action database model."""
    
    __tablename__ = "actions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    action_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    target_devices: Mapped[List[str]] = mapped_column(ARRAY(String))
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={})
    scan_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# Database engine
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class ActionRepository:
    """Repository for action persistence."""
    
    async def create(self, request: Dict[str, Any]) -> Action:
        """Create a new action."""
        action_model = ActionModel(
            id=uuid4(),
            action_type=request["action_type"],
            severity=request.get("severity", "medium"),
            title=request["title"],
            description=request["description"],
            status=ActionStatus.PENDING.value,
            target_devices=request.get("target_devices", []),
            parameters=request.get("parameters", {}),
            scan_id=request.get("scan_id"),
            rule_id=request.get("rule_id"),
            created_by=request.get("created_by"),
        )
        
        async with async_session() as session:
            session.add(action_model)
            await session.commit()
            await session.refresh(action_model)
            
            logger.info("Action created", action_id=str(action_model.id))
            
            return self._to_domain(action_model)
    
    async def get(self, action_id: UUID) -> Optional[Action]:
        """Get action by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(ActionModel).where(ActionModel.id == action_id)
            )
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None
    
    async def update_status(
        self,
        action_id: UUID,
        status: ActionStatus,
        **kwargs,
    ) -> Optional[Action]:
        """Update action status."""
        async with async_session() as session:
            updates = {
                "status": status.value,
                "updated_at": datetime.utcnow(),
                **kwargs,
            }
            
            await session.execute(
                update(ActionModel)
                .where(ActionModel.id == action_id)
                .values(**updates)
            )
            await session.commit()
            
            return await self.get(action_id)
    
    async def set_approved(
        self,
        action_id: UUID,
        approved_by: str,
        approved: bool,
    ) -> Optional[Action]:
        """Set action approval status."""
        status = ActionStatus.APPROVED if approved else ActionStatus.REJECTED
        
        return await self.update_status(
            action_id,
            status,
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
        )
    
    async def set_started(self, action_id: UUID) -> Optional[Action]:
        """Mark action as started."""
        return await self.update_status(
            action_id,
            ActionStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
    
    async def set_completed(
        self,
        action_id: UUID,
        result: Dict[str, Any],
    ) -> Optional[Action]:
        """Mark action as completed."""
        return await self.update_status(
            action_id,
            ActionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            result=result,
        )
    
    async def set_failed(
        self,
        action_id: UUID,
        error_message: str,
    ) -> Optional[Action]:
        """Mark action as failed."""
        return await self.update_status(
            action_id,
            ActionStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=error_message,
        )
    
    async def list_by_status(
        self,
        status: ActionStatus,
        limit: int = 100,
    ) -> List[Action]:
        """List actions by status."""
        async with async_session() as session:
            result = await session.execute(
                select(ActionModel)
                .where(ActionModel.status == status.value)
                .order_by(ActionModel.created_at.desc())
                .limit(limit)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]
    
    async def list_pending_approval(self, limit: int = 100) -> List[Action]:
        """List actions pending approval."""
        return await self.list_by_status(ActionStatus.PENDING_APPROVAL, limit)
    
    async def list_recent(self, limit: int = 50) -> List[Action]:
        """List recent actions."""
        async with async_session() as session:
            result = await session.execute(
                select(ActionModel)
                .order_by(ActionModel.created_at.desc())
                .limit(limit)
            )
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]
    
    def _to_domain(self, model: ActionModel) -> Action:
        """Convert model to domain object."""
        return Action(
            id=model.id,
            action_type=ActionType(model.action_type),
            severity=ActionSeverity(model.severity),
            title=model.title,
            description=model.description,
            status=ActionStatus(model.status),
            target_devices=model.target_devices,
            parameters=model.parameters,
            scan_id=model.scan_id,
            rule_id=model.rule_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            approved_by=model.approved_by,
            approved_at=model.approved_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            result=model.result,
            error_message=model.error_message,
        )
```

---

## Step 5: Celery Tasks

📝 **PROMPT: Create Celery tasks for action execution**
```
Create Celery tasks that:
- Execute different action types
- Handle retries and failures
- Report results to core service
- Coordinate with external connectors
```

**File: `services/action-worker/src/action_worker/tasks.py`**

```python
"""Celery tasks for action execution."""

import asyncio
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

import httpx
import structlog
from celery import shared_task

from action_worker.celery_app import app
from action_worker.config import get_settings
from action_worker.repository import ActionRepository
from action_worker.models import ActionStatus, ActionType

logger = structlog.get_logger()
settings = get_settings()


def run_async(coro):
    """Run async code in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(bind=True, name="action_worker.tasks.execute_action")
def execute_action(self, action_id: str):
    """
    Main task to execute an action.
    
    Args:
        action_id: ID of the action to execute
    """
    return run_async(_execute_action_async(self, action_id))


async def _execute_action_async(task, action_id: str):
    """Async implementation of action execution."""
    repo = ActionRepository()
    
    action = await repo.get(UUID(action_id))
    if not action:
        logger.error("Action not found", action_id=action_id)
        return {"success": False, "error": "Action not found"}
    
    # Check if action is approved
    if action.status != ActionStatus.APPROVED:
        logger.warning(
            "Action not approved",
            action_id=action_id,
            status=action.status,
        )
        return {"success": False, "error": "Action not approved"}
    
    # Mark as in progress
    await repo.set_started(UUID(action_id))
    
    try:
        # Route to appropriate handler
        result = await _route_action(action)
        
        # Mark as completed
        await repo.set_completed(UUID(action_id), result)
        
        logger.info(
            "Action completed",
            action_id=action_id,
            action_type=action.action_type,
        )
        
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.exception("Action execution failed", action_id=action_id)
        
        # Mark as failed
        await repo.set_failed(UUID(action_id), str(e))
        
        # Retry if possible
        if task.request.retries < settings.task_max_retries:
            raise task.retry(exc=e)
        
        return {"success": False, "error": str(e)}


async def _route_action(action) -> Dict[str, Any]:
    """Route action to appropriate handler."""
    handlers = {
        ActionType.CREATE_INCIDENT: _handle_create_incident,
        ActionType.CREATE_CHANGE: _handle_create_change,
        ActionType.RESTART_SERVICE: _handle_tachyon_action,
        ActionType.CLEAR_TEMP_FILES: _handle_tachyon_action,
        ActionType.COLLECT_DATA: _handle_tachyon_action,
        ActionType.CUSTOM: _handle_custom_action,
    }
    
    handler = handlers.get(action.action_type, _handle_custom_action)
    return await handler(action)


async def _handle_create_incident(action) -> Dict[str, Any]:
    """Handle create incident action."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.servicenow_connector_url}/api/incidents",
            json={
                "short_description": action.title,
                "description": action.description,
                "impact": _severity_to_impact(action.severity),
                "urgency": _severity_to_urgency(action.severity),
            },
        )
        response.raise_for_status()
        incident = response.json()
        
        return {
            "incident_number": incident.get("number"),
            "incident_sys_id": incident.get("sys_id"),
            "created_at": datetime.utcnow().isoformat(),
        }


async def _handle_create_change(action) -> Dict[str, Any]:
    """Handle create change request action."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.servicenow_connector_url}/api/changes",
            json={
                "short_description": action.title,
                "description": action.description,
                "type": action.parameters.get("change_type", "normal"),
            },
        )
        response.raise_for_status()
        change = response.json()
        
        return {
            "change_number": change.get("number"),
            "change_sys_id": change.get("sys_id"),
            "created_at": datetime.utcnow().isoformat(),
        }


async def _handle_tachyon_action(action) -> Dict[str, Any]:
    """Handle Tachyon-based action."""
    action_map = {
        ActionType.RESTART_SERVICE: "restart-service",
        ActionType.CLEAR_TEMP_FILES: "clear-temp-files",
        ActionType.COLLECT_DATA: "custom",
    }
    
    endpoint = action_map.get(action.action_type, "custom")
    
    async with httpx.AsyncClient() as client:
        if action.action_type == ActionType.RESTART_SERVICE:
            response = await client.post(
                f"{settings.tachyon_connector_url}/api/actions/{endpoint}",
                json={
                    "devices": action.target_devices,
                    "service_name": action.parameters.get("service_name"),
                },
            )
        elif action.action_type == ActionType.CLEAR_TEMP_FILES:
            response = await client.post(
                f"{settings.tachyon_connector_url}/api/actions/{endpoint}",
                json={
                    "devices": action.target_devices,
                },
            )
        else:
            response = await client.post(
                f"{settings.tachyon_connector_url}/api/actions/{endpoint}",
                params={
                    "instruction_name": action.parameters.get("instruction_name"),
                    "devices": action.target_devices,
                },
                json=action.parameters.get("instruction_parameters", {}),
            )
        
        response.raise_for_status()
        return response.json()


async def _handle_custom_action(action) -> Dict[str, Any]:
    """Handle custom action."""
    logger.info(
        "Executing custom action",
        action_id=str(action.id),
        parameters=action.parameters,
    )
    
    # Custom action logic here
    return {
        "status": "completed",
        "message": f"Custom action {action.action_type} executed",
        "parameters": action.parameters,
    }


def _severity_to_impact(severity) -> int:
    """Convert severity to ServiceNow impact."""
    mapping = {
        "critical": 1,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    return mapping.get(severity.value, 2)


def _severity_to_urgency(severity) -> int:
    """Convert severity to ServiceNow urgency."""
    mapping = {
        "critical": 1,
        "high": 2,
        "medium": 2,
        "low": 3,
    }
    return mapping.get(severity.value, 2)


@app.task(name="action_worker.tasks.process_approval")
def process_approval(action_id: str, approved: bool, approver: str):
    """Process action approval."""
    return run_async(_process_approval_async(action_id, approved, approver))


async def _process_approval_async(action_id: str, approved: bool, approver: str):
    """Async implementation of approval processing."""
    repo = ActionRepository()
    
    action = await repo.set_approved(UUID(action_id), approver, approved)
    
    if not action:
        return {"success": False, "error": "Action not found"}
    
    if approved:
        # Queue the action for execution
        execute_action.delay(action_id)
        logger.info("Action approved and queued", action_id=action_id)
    else:
        logger.info("Action rejected", action_id=action_id, approver=approver)
    
    return {
        "success": True,
        "action_id": action_id,
        "status": action.status.value,
    }


@app.task(name="action_worker.tasks.cleanup_completed_actions")
def cleanup_completed_actions():
    """Cleanup old completed actions."""
    return run_async(_cleanup_completed_async())


async def _cleanup_completed_async():
    """Async implementation of cleanup."""
    # Implementation would archive or delete old completed actions
    logger.info("Running action cleanup")
    return {"cleaned": 0}


# Periodic task for expiring stale approvals
@app.task(name="action_worker.tasks.expire_pending_approvals")
def expire_pending_approvals():
    """Expire actions pending approval for too long."""
    return run_async(_expire_approvals_async())


async def _expire_approvals_async():
    """Async implementation of approval expiration."""
    repo = ActionRepository()
    pending = await repo.list_pending_approval()
    
    expired_count = 0
    cutoff = datetime.utcnow()
    
    for action in pending:
        hours_pending = (cutoff - action.created_at).total_seconds() / 3600
        
        if hours_pending > settings.approval_timeout_hours:
            await repo.update_status(action.id, ActionStatus.CANCELLED)
            expired_count += 1
            logger.info("Action approval expired", action_id=str(action.id))
    
    return {"expired": expired_count}
```

---

## Step 6: API Service

📝 **PROMPT: Create FastAPI service for action management**
```
Create a FastAPI service that:
- Provides endpoints for creating actions
- Handles approval workflow
- Lists and queries actions
- Integrates with Celery tasks
```

**File: `services/action-worker/src/action_worker/api.py`**

```python
"""FastAPI service for action management."""

from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from action_worker.config import get_settings
from action_worker.repository import ActionRepository
from action_worker.models import (
    Action,
    ActionRequest,
    ActionStatus,
    ActionType,
    ApprovalRequest,
)
from action_worker.tasks import execute_action, process_approval


app = FastAPI(
    title="Action Worker API",
    description="API for managing remediation actions",
    version="1.0.0",
)

settings = get_settings()


class CreateActionResponse(BaseModel):
    """Response for action creation."""
    id: UUID
    status: ActionStatus
    requires_approval: bool


class ActionListResponse(BaseModel):
    """Response for action listing."""
    items: List[Action]
    count: int


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "action-worker"}


@app.post("/actions", response_model=CreateActionResponse)
async def create_action(request: ActionRequest):
    """Create a new action."""
    repo = ActionRepository()
    
    action = await repo.create(request.model_dump())
    
    # Determine if approval is required
    requires_approval = _requires_approval(request)
    
    if requires_approval:
        # Set to pending approval
        await repo.update_status(action.id, ActionStatus.PENDING_APPROVAL)
    else:
        # Auto-approve and queue
        await repo.update_status(action.id, ActionStatus.APPROVED)
        execute_action.delay(str(action.id))
    
    return CreateActionResponse(
        id=action.id,
        status=ActionStatus.PENDING_APPROVAL if requires_approval else ActionStatus.APPROVED,
        requires_approval=requires_approval,
    )


@app.post("/actions/{action_id}/approve")
async def approve_action(action_id: UUID, request: ApprovalRequest):
    """Approve or reject an action."""
    repo = ActionRepository()
    
    action = await repo.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.status != ActionStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Action is not pending approval (status: {action.status})",
        )
    
    # Process approval
    process_approval.delay(str(action_id), request.approved, request.approver)
    
    return {
        "action_id": str(action_id),
        "approved": request.approved,
        "message": "Approval processed",
    }


@app.get("/actions/{action_id}", response_model=Action)
async def get_action(action_id: UUID):
    """Get action by ID."""
    repo = ActionRepository()
    
    action = await repo.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    return action


@app.get("/actions", response_model=ActionListResponse)
async def list_actions(
    status: Optional[ActionStatus] = Query(None),
    action_type: Optional[ActionType] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List actions with optional filtering."""
    repo = ActionRepository()
    
    if status:
        actions = await repo.list_by_status(status, limit)
    else:
        actions = await repo.list_recent(limit)
    
    if action_type:
        actions = [a for a in actions if a.action_type == action_type]
    
    return ActionListResponse(items=actions, count=len(actions))


@app.get("/actions/pending-approval", response_model=ActionListResponse)
async def list_pending_approval(limit: int = Query(50, ge=1, le=200)):
    """List actions pending approval."""
    repo = ActionRepository()
    
    actions = await repo.list_pending_approval(limit)
    
    return ActionListResponse(items=actions, count=len(actions))


@app.post("/actions/{action_id}/cancel")
async def cancel_action(action_id: UUID):
    """Cancel an action."""
    repo = ActionRepository()
    
    action = await repo.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    if action.status in [ActionStatus.COMPLETED, ActionStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed or failed action",
        )
    
    await repo.update_status(action_id, ActionStatus.CANCELLED)
    
    return {"action_id": str(action_id), "status": "cancelled"}


def _requires_approval(request: ActionRequest) -> bool:
    """Determine if action requires approval."""
    if not settings.require_approval:
        return False
    
    if settings.auto_approve_low_severity and request.severity.value == "low":
        return False
    
    # Always require approval for certain action types
    high_risk_types = [ActionType.DEPLOY_PATCH, ActionType.CUSTOM]
    if request.action_type in high_risk_types:
        return True
    
    return True
```

---

## Step 7: Worker Entry Point

**File: `services/action-worker/src/action_worker/__main__.py`**

```python
"""Worker entry point."""

import sys

if __name__ == "__main__":
    # Start Celery worker or API based on argument
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        from action_worker.api import app
        
        uvicorn.run(app, host="0.0.0.0", port=8006)
    else:
        from action_worker.celery_app import app
        
        app.worker_main(["worker", "--loglevel=info"])
```

---

## Step 8: Celery Beat Schedule

**File: `services/action-worker/src/action_worker/beat.py`**

```python
"""Celery Beat schedule configuration."""

from celery.schedules import crontab

from action_worker.celery_app import app


# Configure periodic tasks
app.conf.beat_schedule = {
    "expire-pending-approvals": {
        "task": "action_worker.tasks.expire_pending_approvals",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
    },
    "cleanup-completed-actions": {
        "task": "action_worker.tasks.cleanup_completed_actions",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}
```

---

## Verification

### Start Worker Components

```powershell
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:7

# Terminal 2: Start Celery worker
cd services/action-worker
python -m celery -A action_worker.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat (for scheduled tasks)
python -m celery -A action_worker.celery_app beat --loglevel=info

# Terminal 4: Start API
uvicorn action_worker.api:app --reload --port 8006
```

### Test Action Flow

```powershell
# Create an action
$body = @{
    action_type = "create_incident"
    severity = "medium"
    title = "Test action"
    description = "Test description"
    target_devices = @("DESKTOP-001")
} | ConvertTo-Json

curl -X POST http://localhost:8006/actions `
  -H "Content-Type: application/json" `
  -d $body

# List pending approvals
curl http://localhost:8006/actions/pending-approval

# Approve action
$approval = @{
    action_id = "<action-id>"
    approved = $true
    approver = "admin@company.com"
} | ConvertTo-Json

curl -X POST http://localhost:8006/actions/<action-id>/approve `
  -H "Content-Type: application/json" `
  -d $approval
```

---

## Common Issues

### Issue: Tasks not being picked up

**Solution:** Verify Redis is running and celery broker URL is correct

### Issue: Task execution timeout

**Solution:** Increase `task_time_limit` in settings or break into smaller tasks

### Issue: Approval workflow stuck

**Solution:** Check task queue and ensure beat scheduler is running

---

## Next Steps

→ [13_Deployment.md](13_Deployment.md) - Deploy the complete system

---

**Checkpoint:** You should now have:
- [ ] Celery worker processing tasks
- [ ] Actions created and queued
- [ ] Approval workflow functioning
- [ ] ServiceNow/Tachyon integration working
- [ ] Periodic tasks scheduled
