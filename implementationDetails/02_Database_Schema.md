# 02 - Database Schema Guide

## Overview

This guide covers the PostgreSQL database schema design, SQLAlchemy models, and Alembic migrations for the IT Operations AI Agent.

---

## Prerequisites

- Project setup complete (see [01_Project_Setup.md](01_Project_Setup.md))
- PostgreSQL running (via Docker)
- Python environment activated

---

## Step 1: Database Design

### 1.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │     rules       │       │     scans       │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ azure_id        │       │ name            │       │ rule_id (FK)    │
│ email           │──────<│ created_by (FK) │>──────│ status          │
│ display_name    │       │ entity_type     │       │ started_at      │
│ role            │       │ conditions      │       │ completed_at    │
│ created_at      │       │ actions         │       │ total_found     │
│ last_login      │       │ schedule        │       │ created_by (FK) │
└─────────────────┘       │ is_active       │       └────────┬────────┘
                          │ created_at      │                │
                          └─────────────────┘                │
                                                             │
┌─────────────────┐       ┌─────────────────┐       ┌────────▼────────┐
│  applications   │       │   app_owners    │       │  scan_results   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ name            │──────<│ email           │       │ scan_id (FK)    │
│ version         │       │ display_name    │       │ entity_type     │
│ publisher       │       │ department      │       │ entity_id       │
│ app_owner_id(FK)│       │ manager_email   │       │ entity_name     │
│ install_count   │       │ notification_   │       │ match_data      │
│ cve_list        │       │   preferences   │       │ severity        │
└─────────────────┘       └─────────────────┘       │ created_at      │
                                                    └─────────────────┘
                                                    
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ action_requests │       │  action_logs    │       │   audit_logs    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ scan_id (FK)    │       │ action_id (FK)  │       │ user_id (FK)    │
│ action_type     │       │ status          │       │ action          │
│ target_entities │       │ started_at      │       │ entity_type     │
│ parameters      │       │ completed_at    │       │ entity_id       │
│ status          │       │ result          │       │ details         │
│ created_by (FK) │       │ error_message   │       │ ip_address      │
│ approved_by(FK) │       └─────────────────┘       │ created_at      │
│ approved_at     │                                 └─────────────────┘
│ created_at      │
└─────────────────┘
```

### 1.2 Table Definitions

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | System users from Azure AD | azure_id, email, role |
| `rules` | Rule definitions | name, entity_type, conditions, actions |
| `scans` | Scan execution records | rule_id, status, results count |
| `scan_results` | Individual scan matches | entity_type, entity_id, match_data |
| `applications` | Tracked applications | name, version, cve_list |
| `app_owners` | Application owners | email, department |
| `action_requests` | Pending/approved actions | action_type, status, approvals |
| `action_logs` | Action execution history | status, result, errors |
| `audit_logs` | System audit trail | user, action, details |

---

## Step 2: Create SQLAlchemy Models

### 2.1 Base Model Configuration

📝 **PROMPT: Create SQLAlchemy base model**
```
Create a SQLAlchemy 2.0 async base model for PostgreSQL with:
- UUID primary keys
- Created/updated timestamps with timezone
- Soft delete support
- JSON serialization method
- Async session management
```

**File: `shared/src/itoa_shared/database.py`**

```python
"""Database configuration and base models."""

from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from uuid import uuid4

from sqlalchemy import MetaData, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    metadata = MetaData(naming_convention=convention)
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class DatabaseManager:
    """Async database session manager."""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
```

### 2.2 User Model

**File: `services/auth-service/src/auth_service/models.py`**

```python
"""User and authentication models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from itoa_shared.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class User(Base):
    """User model for Azure AD authenticated users."""
    
    __tablename__ = "users"
    
    # Azure AD fields
    azure_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    
    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), 
        default=UserRole.VIEWER
    )
    
    # Activity tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def can_approve(self) -> bool:
        """Check if user can approve actions."""
        return self.role in (UserRole.OPERATOR, UserRole.ADMIN)
```

### 2.3 Rule Model

📝 **PROMPT: Create Rule SQLAlchemy model**
```
Create a SQLAlchemy model for Rules with:
- Name, description, entity_type (devices/applications/both)
- JSON conditions field for flexible rule definitions
- JSON actions field for configured actions
- Schedule configuration (cron expression)
- Status tracking (active/inactive)
- Foreign key to user who created it
```

**File: `services/core-service/src/core_service/models/rule.py`**

```python
"""Rule model for defining scan criteria."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from itoa_shared.database import Base


class EntityType(str, Enum):
    """Entity type for rules."""
    DEVICES = "devices"
    APPLICATIONS = "applications"
    BOTH = "both"


class Rule(Base):
    """Rule definition model."""
    
    __tablename__ = "rules"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Entity type
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        default=EntityType.DEVICES
    )
    
    # Rule configuration (JSON)
    conditions: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        comment="Rule conditions in structured format"
    )
    """
    Example conditions structure:
    {
        "logic": "AND",
        "conditions": [
            {"field": "free_disk_gb", "operator": "lt", "value": 10},
            {"field": "last_patch_date", "operator": "older_than_days", "value": 30}
        ]
    }
    """
    
    # Actions to execute when rule matches
    actions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        comment="Actions to execute for matching entities"
    )
    """
    Example actions structure:
    [
        {"type": "create_collection", "params": {"name_template": "LowDisk_{date}"}},
        {"type": "create_incident", "params": {"priority": 3, "category": "hardware"}},
        {"type": "notify_app_owner", "params": {"template": "vulnerability_alert"}}
    ]
    """
    
    # Schedule (optional)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Cron expression for scheduled execution"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Ownership
    created_by_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )
    
    # Relationships
    # created_by: Mapped["User"] = relationship("User", back_populates="rules")
    # scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="rule")
    
    # Template flag
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Rule {self.name} ({self.entity_type})>"


class RuleTemplate(Base):
    """Pre-built rule templates."""
    
    __tablename__ = "rule_templates"
    
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[EntityType] = mapped_column(SQLEnum(EntityType))
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB)
    suggested_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    
    def __repr__(self) -> str:
        return f"<RuleTemplate {self.name}>"
```

### 2.4 Scan and Results Models

**File: `services/core-service/src/core_service/models/scan.py`**

```python
"""Scan execution and results models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from itoa_shared.database import Base


class ScanStatus(str, Enum):
    """Scan execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, Enum):
    """Result severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Scan(Base):
    """Scan execution record."""
    
    __tablename__ = "scans"
    
    # Rule reference
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id"), index=True)
    rule_name: Mapped[str] = mapped_column(String(255))  # Denormalized for history
    
    # Execution status
    status: Mapped[ScanStatus] = mapped_column(
        SQLEnum(ScanStatus),
        default=ScanStatus.PENDING
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Results summary
    total_scanned: Mapped[int] = mapped_column(Integer, default=0)
    total_matched: Mapped[int] = mapped_column(Integer, default=0)
    devices_matched: Mapped[int] = mapped_column(Integer, default=0)
    applications_matched: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ownership
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    
    # AI insights (generated after scan)
    ai_insights: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, 
        nullable=True,
        comment="AI-generated insights about scan results"
    )
    
    # Relationships
    # rule: Mapped["Rule"] = relationship("Rule", back_populates="scans")
    # results: Mapped[list["ScanResult"]] = relationship("ScanResult", back_populates="scan")
    
    def __repr__(self) -> str:
        return f"<Scan {self.id[:8]} - {self.status}>"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate scan duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ScanResult(Base):
    """Individual scan result (matched entity)."""
    
    __tablename__ = "scan_results"
    
    # Scan reference
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), index=True)
    
    # Entity info
    entity_type: Mapped[str] = mapped_column(String(50), index=True)  # 'device' or 'application'
    entity_id: Mapped[str] = mapped_column(String(255), index=True)
    entity_name: Mapped[str] = mapped_column(String(255))
    
    # Match details
    match_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        comment="Data that caused the match"
    )
    """
    Example match_data:
    {
        "free_disk_gb": 5.2,
        "last_patch_date": "2025-12-01",
        "matched_conditions": ["free_disk_gb < 10", "last_patch_date > 30 days"]
    }
    """
    
    # Severity
    severity: Mapped[Severity] = mapped_column(
        SQLEnum(Severity),
        default=Severity.MEDIUM
    )
    
    # For applications - owner info
    app_owner_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("app_owners.id"), 
        nullable=True,
        index=True
    )
    
    # AI explanation (optional)
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ScanResult {self.entity_type}:{self.entity_name}>"
```

### 2.5 Application and App Owner Models

**File: `services/core-service/src/core_service/models/application.py`**

```python
"""Application and App Owner models."""

from typing import Any, Optional

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from itoa_shared.database import Base


class AppOwner(Base):
    """Application owner model."""
    
    __tablename__ = "app_owners"
    
    # Contact info
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Manager info for escalation
    manager_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notification preferences
    notification_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {
            "email": True,
            "teams": False,
            "digest_frequency": "immediate"  # immediate, daily, weekly
        }
    )
    
    # ServiceNow user sys_id (for ticket assignment)
    servicenow_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<AppOwner {self.email}>"


class Application(Base):
    """Tracked application model."""
    
    __tablename__ = "applications"
    
    # Application identity
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Unique identifier (name + publisher combo)
    app_key: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    
    # Installation stats
    install_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Owner reference
    app_owner_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("app_owners.id"),
        nullable=True,
        index=True
    )
    
    # Vulnerability tracking
    cve_list: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        comment="List of CVE IDs affecting this application"
    )
    
    # Additional metadata
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    criticality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # low, medium, high, critical
    
    # EOL info
    eol_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Application {self.name} v{self.version}>"
```

### 2.6 Action Models

**File: `services/core-service/src/core_service/models/action.py`**

```python
"""Action request and execution models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from itoa_shared.database import Base


class ActionType(str, Enum):
    """Available action types."""
    CREATE_COLLECTION = "create_collection"
    CREATE_DEPLOYMENT = "create_deployment"
    CREATE_INCIDENT = "create_incident"
    SEND_NOTIFICATION = "send_notification"
    NOTIFY_APP_OWNER = "notify_app_owner"
    RUN_TACHYON_INSTRUCTION = "run_tachyon_instruction"
    CREATE_VULNERABILITY_TICKET = "create_vulnerability_ticket"


class ActionStatus(str, Enum):
    """Action request status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionRequest(Base):
    """Action request model for approval workflow."""
    
    __tablename__ = "action_requests"
    
    # Reference to scan results
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), index=True)
    
    # Action configuration
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType))
    
    # Target entities (device IDs or application IDs)
    target_entities: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        comment="List of target entities with metadata"
    )
    """
    Example:
    [
        {"type": "device", "id": "DEV001", "name": "WS-NYC-12345"},
        {"type": "application", "id": "APP001", "name": "Chrome", "owner_email": "john@co.com"}
    ]
    """
    
    # Action parameters
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        comment="Action-specific parameters"
    )
    
    # Status tracking
    status: Mapped[ActionStatus] = mapped_column(
        SQLEnum(ActionStatus),
        default=ActionStatus.DRAFT
    )
    
    # Approval workflow
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    approved_by_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Execution tracking
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # AI suggestion flag
    is_ai_suggested: Mapped[bool] = mapped_column(default=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    def __repr__(self) -> str:
        return f"<ActionRequest {self.action_type} - {self.status}>"


class ActionLog(Base):
    """Action execution log."""
    
    __tablename__ = "action_logs"
    
    # Reference to action request
    action_request_id: Mapped[str] = mapped_column(
        ForeignKey("action_requests.id"), 
        index=True
    )
    
    # Execution details
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Result
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # External references (IDs created in external systems)
    external_ids: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        default=dict,
        comment="IDs from external systems (collection_id, incident_number, etc.)"
    )
    
    def __repr__(self) -> str:
        return f"<ActionLog {self.action_request_id[:8]} - {self.status}>"


class AuditLog(Base):
    """System audit log for compliance."""
    
    __tablename__ = "audit_logs"
    
    # Who
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user_email: Mapped[str] = mapped_column(String(255))  # Denormalized
    
    # What
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Details
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Where
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_email}>"
```

---

## Step 3: Set Up Alembic Migrations

### 3.1 Initialize Alembic

```powershell
cd services/core-service
pip install alembic
alembic init alembic
```

### 3.2 Configure Alembic

**File: `services/core-service/alembic.ini`** (modify these lines)

```ini
# Change the script location
script_location = alembic

# Set the SQLAlchemy URL (use environment variable)
sqlalchemy.url = postgresql://%(POSTGRES_USER)s:%(POSTGRES_PASSWORD)s@%(POSTGRES_HOST)s/%(POSTGRES_DB)s
```

**File: `services/core-service/alembic/env.py`**

```python
"""Alembic migration environment."""

import asyncio
from logging.config import fileConfig
import os

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models
from core_service.models.rule import Rule, RuleTemplate
from core_service.models.scan import Scan, ScanResult
from core_service.models.application import Application, AppOwner
from core_service.models.action import ActionRequest, ActionLog, AuditLog
from itoa_shared.database import Base

# Alembic Config object
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://itoa:itoa_dev_password@localhost:5432/itoa_db"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3.3 Create Initial Migration

```powershell
# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Run migration
alembic upgrade head
```

---

## Step 4: Database Initialization Script

**File: `scripts/init-db.sql`**

```sql
-- Initialize ITOA Agent Database
-- This script runs when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create enum types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('viewer', 'operator', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM ('devices', 'applications', 'both');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE scan_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'executing', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for common queries (run after tables are created by Alembic)
-- These are additional performance indexes

-- Index for searching rules by name
-- CREATE INDEX IF NOT EXISTS idx_rules_name_trgm ON rules USING gin (name gin_trgm_ops);

-- Index for scan results by entity
-- CREATE INDEX IF NOT EXISTS idx_scan_results_entity ON scan_results (entity_type, entity_id);

-- Index for audit logs by date
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs (created_at DESC);

-- Grant permissions (adjust for your security requirements)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO itoa;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO itoa;
```

---

## Step 5: Seed Data

📝 **PROMPT: Generate seed data script**
```
Create a Python script to seed the database with:
- 10 rule templates (5 for devices, 5 for applications)
- Sample app owners
- Test user accounts
```

**File: `scripts/seed_data.py`**

```python
"""Seed database with initial data."""

import asyncio
from itoa_shared.database import DatabaseManager, Base
from core_service.models.rule import RuleTemplate, EntityType

# Rule templates data
RULE_TEMPLATES = [
    # Device templates
    {
        "name": "Low Disk Space Alert",
        "description": "Find devices with less than 10GB free disk space",
        "category": "storage",
        "entity_type": EntityType.DEVICES,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "free_disk_gb", "operator": "lt", "value": 10}
            ]
        },
        "suggested_actions": [
            {"type": "create_incident", "params": {"category": "storage", "priority": 3}}
        ]
    },
    {
        "name": "Inactive Devices (30+ days)",
        "description": "Find devices not seen in over 30 days",
        "category": "inventory",
        "entity_type": EntityType.DEVICES,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "last_active_days", "operator": "gt", "value": 30}
            ]
        },
        "suggested_actions": [
            {"type": "create_collection", "params": {"name_template": "Inactive_Devices_{date}"}}
        ]
    },
    {
        "name": "Missing Critical Patches",
        "description": "Find devices missing critical security patches",
        "category": "security",
        "entity_type": EntityType.DEVICES,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "missing_critical_patches", "operator": "gt", "value": 0}
            ]
        },
        "suggested_actions": [
            {"type": "create_deployment", "params": {"type": "required"}}
        ]
    },
    {
        "name": "EOL Hardware - 6 Month Warning",
        "description": "Find hardware approaching end of life",
        "category": "lifecycle",
        "entity_type": EntityType.DEVICES,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "eol_days_remaining", "operator": "lt", "value": 180}
            ]
        },
        "suggested_actions": [
            {"type": "create_incident", "params": {"category": "hardware_refresh"}}
        ]
    },
    {
        "name": "High Memory Usage",
        "description": "Find devices with consistently high memory usage",
        "category": "performance",
        "entity_type": EntityType.DEVICES,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "avg_memory_usage_pct", "operator": "gt", "value": 90}
            ]
        },
        "suggested_actions": []
    },
    
    # Application templates
    {
        "name": "Vulnerable Applications (CVE)",
        "description": "Find applications with known vulnerabilities",
        "category": "security",
        "entity_type": EntityType.APPLICATIONS,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "cve_count", "operator": "gt", "value": 0}
            ]
        },
        "suggested_actions": [
            {"type": "notify_app_owner", "params": {"template": "vulnerability_alert"}},
            {"type": "create_vulnerability_ticket", "params": {}}
        ]
    },
    {
        "name": "EOL Software",
        "description": "Find applications past end of life date",
        "category": "lifecycle",
        "entity_type": EntityType.APPLICATIONS,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "is_eol", "operator": "eq", "value": True}
            ]
        },
        "suggested_actions": [
            {"type": "notify_app_owner", "params": {"template": "eol_notice"}}
        ]
    },
    {
        "name": "Outdated Browser Versions",
        "description": "Find outdated Chrome, Firefox, or Edge installations",
        "category": "security",
        "entity_type": EntityType.APPLICATIONS,
        "conditions": {
            "logic": "OR",
            "conditions": [
                {"field": "name", "operator": "contains", "value": "Chrome", "and": [
                    {"field": "version", "operator": "version_lt", "value": "120.0"}
                ]},
                {"field": "name", "operator": "contains", "value": "Firefox", "and": [
                    {"field": "version", "operator": "version_lt", "value": "121.0"}
                ]}
            ]
        },
        "suggested_actions": [
            {"type": "create_deployment", "params": {"type": "recommended"}}
        ]
    },
    {
        "name": "Unauthorized Software",
        "description": "Find installations of blacklisted software",
        "category": "compliance",
        "entity_type": EntityType.APPLICATIONS,
        "conditions": {
            "logic": "OR",
            "conditions": [
                {"field": "name", "operator": "in_list", "value": ["BitTorrent", "uTorrent", "Kazaa"]}
            ]
        },
        "suggested_actions": [
            {"type": "create_incident", "params": {"category": "compliance", "priority": 2}}
        ]
    },
    {
        "name": "License Compliance Check",
        "description": "Find applications exceeding license count",
        "category": "compliance",
        "entity_type": EntityType.APPLICATIONS,
        "conditions": {
            "logic": "AND",
            "conditions": [
                {"field": "install_count", "operator": "gt", "value": {"ref": "license_count"}}
            ]
        },
        "suggested_actions": [
            {"type": "notify_app_owner", "params": {"template": "license_warning"}}
        ]
    }
]


async def seed_templates(db: DatabaseManager):
    """Seed rule templates."""
    async for session in db.get_session():
        for template_data in RULE_TEMPLATES:
            template = RuleTemplate(**template_data)
            session.add(template)
        await session.commit()
        print(f"✅ Seeded {len(RULE_TEMPLATES)} rule templates")


async def main():
    """Run seeding."""
    import os
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://itoa:itoa_dev_password@localhost:5432/itoa_db")
    db = DatabaseManager(db_url)
    
    await seed_templates(db)
    print("🎉 Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Verification

### Test Database Connection

```python
# Quick test script
import asyncio
from itoa_shared.database import DatabaseManager

async def test_connection():
    db = DatabaseManager("postgresql+asyncpg://itoa:itoa_dev_password@localhost:5432/itoa_db")
    async for session in db.get_session():
        result = await session.execute("SELECT 1")
        print(f"✅ Database connected: {result.scalar()}")

asyncio.run(test_connection())
```

---

## Common Issues

### Issue: asyncpg not connecting

**Solution:** Ensure you're using `postgresql+asyncpg://` in the URL

### Issue: UUID type errors

**Solution:** Enable uuid-ossp extension: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

---

## Next Steps

→ [03_Auth_Service.md](03_Auth_Service.md) - Implement authentication service

---

**Checkpoint:** You should now have:
- [ ] All SQLAlchemy models defined
- [ ] Alembic configured for migrations
- [ ] Initial migration created and applied
- [ ] Seed data script ready
- [ ] Database connection tested
