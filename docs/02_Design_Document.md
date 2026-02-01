# IT Operations AI Agent - System Design Document

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Project Name:** IT Operations AI Agent (ITOA Agent)  
**Author:** IT Operations Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Design](#4-data-design)
5. [Integration Design](#5-integration-design)
6. [Security Design](#6-security-design)
7. [User Interface Design](#7-user-interface-design)
8. [Deployment Design](#8-deployment-design)
9. [Error Handling & Logging](#9-error-handling--logging)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Introduction

### 1.1 Purpose

This document provides the technical design for the IT Operations AI Agent (ITOA Agent). It describes the system architecture, component design, data models, integration patterns, and deployment strategy.

### 1.2 Design Goals

| Goal | Description |
|------|-------------|
| **Modularity** | Loosely coupled components for easy maintenance |
| **Extensibility** | Easy to add new rules, actions, and integrations |
| **Safety** | Human-in-the-loop for all destructive actions |
| **Performance** | Handle 100K devices with responsive UI |
| **Accessibility** | WCAG 2.1 AA compliant interface |

### 1.3 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Desktop UI** | Python + PySide6 (Qt) | Cross-platform, WCAG support, mature ecosystem |
| **Backend API** | Python + FastAPI | Async support, automatic OpenAPI docs |
| **Database** | PostgreSQL | Robust, JSON support, enterprise-ready |
| **Cache** | Redis | Session management, job queues |
| **Message Queue** | Redis/RabbitMQ | Action execution queue |
| **Container** | Docker + Kubernetes | OpenShift deployment |
| **LLM** | LangChain | Provider-agnostic LLM abstraction |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Layer                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Desktop Application (PySide6)                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │ │
│  │  │Dashboard │ │  Rules   │ │  Scans   │ │ Actions  │ │ Reports  │     │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │ HTTPS/REST
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster (OpenShift)                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         API Gateway (Ingress)                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Backend Services                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   Auth      │  │    Core     │  │    LLM      │  │   Action    │  │   │
│  │  │  Service    │  │   Service   │  │   Service   │  │   Worker    │  │   │
│  │  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │  │  (Celery)   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Data Layer                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │ PostgreSQL  │  │    Redis    │  │  Local LLM  │                   │   │
│  │  │  Database   │  │ Cache/Queue │  │   (QWEN)    │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  MECM DB    │   │ ServiceNow  │   │ 1E Tachyon  │
            │  (SQL)      │   │    API      │   │    API      │
            └─────────────┘   └─────────────┘   └─────────────┘
```

### 2.2 Component Overview

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Desktop App** | User interface, local state | Python + PySide6 |
| **Auth Service** | Authentication, authorization | FastAPI + Azure OAuth |
| **Core Service** | Rules, scans, business logic | FastAPI + SQLAlchemy |
| **LLM Service** | AI suggestions, NL processing | FastAPI + LangChain |
| **Action Worker** | Execute approved actions | Celery + Redis |
| **PostgreSQL** | Application data | PostgreSQL 15+ |
| **Redis** | Caching, job queue | Redis 7+ |

### 2.3 Communication Patterns

```
Desktop App ──REST/JSON──► API Gateway ──► Backend Services
                                               │
                                               ▼
Backend Services ──SQL──────────────────► PostgreSQL
                 ──Redis Protocol────────► Redis
                 ──HTTPS─────────────────► External APIs
                 ──gRPC/HTTP─────────────► Local LLM
```

---

## 3. Component Design

### 3.1 Desktop Application

#### 3.1.1 Architecture (MVVM Pattern)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Desktop Application                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      View Layer (Qt)                       │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │MainWindow│ │Dialogs  │ │Widgets  │ │Charts   │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │ Data Binding                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   ViewModel Layer                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │Dashboard│ │RulesVM  │ │ScansVM  │ │ActionsVM│         │  │
│  │  │ViewModel│ │         │ │         │ │         │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │ API Calls                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │APIClient│ │AuthSvc  │ │CacheSvc │ │ConfigSvc│         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Module Structure

```
itoa_desktop/
├── main.py                    # Application entry point
├── config/
│   ├── settings.py           # Configuration management
│   └── constants.py          # Application constants
├── services/
│   ├── api_client.py         # REST API client
│   ├── auth_service.py       # Azure OAuth handling
│   ├── cache_service.py      # Local caching
│   └── config_service.py     # Settings persistence
├── viewmodels/
│   ├── base_viewmodel.py     # Base class with signals
│   ├── dashboard_vm.py       # Dashboard logic
│   ├── rules_vm.py           # Rules management
│   ├── scans_vm.py           # Scan results
│   ├── actions_vm.py         # Action management
│   └── reports_vm.py         # Report generation
├── views/
│   ├── main_window.py        # Main application window
│   ├── dashboard/
│   │   ├── dashboard_view.py
│   │   └── widgets/
│   ├── rules/
│   │   ├── rules_view.py
│   │   ├── rule_builder.py
│   │   └── rule_templates.py
│   ├── scans/
│   │   ├── scan_results_view.py
│   │   └── device_detail.py
│   ├── actions/
│   │   ├── actions_view.py
│   │   └── approval_dialog.py
│   └── common/
│       ├── accessible_widgets.py
│       └── data_table.py
├── models/
│   ├── rule.py               # Rule data model
│   ├── device.py             # Device data model
│   ├── action.py             # Action data model
│   └── user.py               # User data model
├── utils/
│   ├── validators.py         # Input validation
│   ├── formatters.py         # Data formatting
│   └── accessibility.py      # WCAG helpers
└── resources/
    ├── styles/
    │   ├── light_theme.qss
    │   └── dark_theme.qss
    ├── icons/
    └── translations/
```

#### 3.1.3 Key Classes

**API Client:**
```python
class APIClient:
    """Thread-safe REST API client with retry logic."""
    
    def __init__(self, base_url: str, auth_service: AuthService):
        self.base_url = base_url
        self.auth = auth_service
        self.session = requests.Session()
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
    
    async def get(self, endpoint: str, params: dict = None) -> dict:
        """GET request with automatic token refresh."""
        headers = {"Authorization": f"Bearer {await self.auth.get_token()}"}
        response = await self._request("GET", endpoint, headers=headers, params=params)
        return response.json()
    
    async def post(self, endpoint: str, data: dict) -> dict:
        """POST request with automatic token refresh."""
        headers = {"Authorization": f"Bearer {await self.auth.get_token()}"}
        response = await self._request("POST", endpoint, headers=headers, json=data)
        return response.json()
```

**Base ViewModel:**
```python
from PySide6.QtCore import QObject, Signal

class BaseViewModel(QObject):
    """Base ViewModel with common signals and state management."""
    
    loading_changed = Signal(bool)
    error_occurred = Signal(str)
    data_changed = Signal()
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api = api_client
        self._loading = False
        self._error = None
    
    @property
    def loading(self) -> bool:
        return self._loading
    
    @loading.setter
    def loading(self, value: bool):
        self._loading = value
        self.loading_changed.emit(value)
    
    def handle_error(self, error: Exception):
        self._error = str(error)
        self.error_occurred.emit(self._error)
        logging.error(f"ViewModel error: {error}", exc_info=True)
```

### 3.2 Backend Services

#### 3.2.1 Auth Service

**Responsibilities:**
- Azure OAuth 2.0 token validation
- User session management
- Role-based access control

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Initiate OAuth flow |
| POST | /auth/callback | OAuth callback |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Get current user info |
| POST | /auth/logout | Invalidate session |

**Module Structure:**
```
auth_service/
├── main.py
├── routers/
│   └── auth.py
├── services/
│   ├── azure_oauth.py
│   ├── token_service.py
│   └── rbac_service.py
├── models/
│   ├── user.py
│   └── token.py
└── middleware/
    └── auth_middleware.py
```

#### 3.2.2 Core Service

**Responsibilities:**
- Rule CRUD operations
- Rule execution (scanning)
- Device data aggregation
- Action request management

**API Endpoints:**

**Rules:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /rules | List all rules |
| POST | /rules | Create rule |
| GET | /rules/{id} | Get rule details |
| PUT | /rules/{id} | Update rule |
| DELETE | /rules/{id} | Delete rule |
| POST | /rules/{id}/execute | Execute rule scan |
| GET | /rules/templates | Get rule templates |

**Scans:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /scans | List scan executions |
| GET | /scans/{id} | Get scan details |
| GET | /scans/{id}/results | Get scan results (devices) |
| GET | /scans/{id}/summary | Get categorized summary |

**Devices:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /devices | Search devices |
| GET | /devices/{id} | Get device details |
| GET | /devices/{id}/history | Get device scan history |

**Actions:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /actions | List action requests |
| POST | /actions | Create action request |
| GET | /actions/{id} | Get action details |
| POST | /actions/{id}/approve | Approve action |
| POST | /actions/{id}/reject | Reject action |
| POST | /actions/{id}/cancel | Cancel action |
| GET | /actions/pending | Get pending approvals |

**Module Structure:**
```
core_service/
├── main.py
├── routers/
│   ├── rules.py
│   ├── scans.py
│   ├── devices.py
│   └── actions.py
├── services/
│   ├── rule_service.py
│   ├── scan_engine.py
│   ├── device_service.py
│   ├── action_service.py
│   └── notification_service.py
├── models/
│   ├── rule.py
│   ├── scan.py
│   ├── device.py
│   └── action.py
├── repositories/
│   ├── rule_repository.py
│   ├── scan_repository.py
│   └── action_repository.py
├── connectors/
│   ├── mecm_connector.py
│   ├── snow_connector.py
│   └── tachyon_connector.py
└── utils/
    ├── rule_parser.py
    └── query_builder.py
```

#### 3.2.3 LLM Service

**Responsibilities:**
- Natural language rule interpretation
- Remediation suggestion generation
- Issue explanation generation
- Sensitive data filtering

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /llm/interpret-rule | NL to structured rule |
| POST | /llm/suggest-remediation | Get action suggestions |
| POST | /llm/explain-issue | Explain device issue |
| GET | /llm/providers | List available providers |
| PUT | /llm/config | Update LLM configuration |

**Module Structure:**
```
llm_service/
├── main.py
├── routers/
│   └── llm.py
├── services/
│   ├── llm_orchestrator.py
│   ├── rule_interpreter.py
│   ├── suggestion_generator.py
│   └── data_filter.py
├── providers/
│   ├── base_provider.py
│   ├── openai_provider.py
│   ├── azure_openai_provider.py
│   └── qwen_provider.py
├── prompts/
│   ├── rule_interpretation.py
│   ├── remediation_suggestion.py
│   └── issue_explanation.py
└── utils/
    ├── tokenizer.py
    └── sensitive_filter.py
```

**LLM Provider Abstraction:**
```python
from abc import ABC, abstractmethod
from langchain.llms.base import BaseLLM
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_llm(self) -> BaseLLM:
        """Return configured LLM instance."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    def get_llm(self) -> BaseLLM:
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=0.3
        )
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class QWENProvider(LLMProvider):
    def __init__(self, endpoint: str, model: str = "qwen-7b"):
        self.endpoint = endpoint
        self.model = model
    
    def get_llm(self) -> BaseLLM:
        # Uses local QWEN via vLLM or similar
        return VLLMOpenAI(
            openai_api_base=self.endpoint,
            model_name=self.model
        )
```

**Sensitive Data Filter:**
```python
class SensitiveDataFilter:
    """Filter sensitive information before sending to LLM."""
    
    PATTERNS = {
        'email': (r'\b[\w.-]+@[\w.-]+\.\w+\b', 'USER_{}_EMAIL'),
        'ip_address': (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_{}_ADDR'),
        'hostname': (r'\b[A-Z]{2,4}-[A-Z]{2,4}-\d{4,6}\b', 'DEVICE_{}'),
        'serial': (r'\b[A-Z0-9]{10,20}\b', 'SERIAL_{}'),
        'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN_REDACTED'),
    }
    
    def __init__(self):
        self.mappings = {}  # Store for reverse mapping if needed
        self.counter = 0
    
    def filter(self, text: str) -> str:
        """Replace sensitive data with placeholders."""
        filtered = text
        for pattern_name, (pattern, replacement) in self.PATTERNS.items():
            matches = re.findall(pattern, filtered)
            for match in matches:
                self.counter += 1
                placeholder = replacement.format(self.counter)
                self.mappings[placeholder] = match
                filtered = filtered.replace(match, placeholder, 1)
        return filtered
    
    def restore(self, text: str) -> str:
        """Restore original values from placeholders."""
        restored = text
        for placeholder, original in self.mappings.items():
            restored = restored.replace(placeholder, original)
        return restored
```

#### 3.2.4 Action Worker

**Responsibilities:**
- Execute approved actions asynchronously
- Manage action queue
- Handle retries and failures
- Send completion notifications

**Module Structure:**
```
action_worker/
├── main.py
├── celery_app.py
├── tasks/
│   ├── base_task.py
│   ├── mecm_tasks.py
│   ├── snow_tasks.py
│   ├── tachyon_tasks.py
│   └── notification_tasks.py
├── executors/
│   ├── patch_executor.py
│   ├── incident_executor.py
│   ├── collection_executor.py
│   └── deployment_executor.py
└── utils/
    ├── retry_policy.py
    └── result_handler.py
```

**Celery Task Example:**
```python
from celery import Task
from celery.exceptions import MaxRetriesExceededError

class ActionTask(Task):
    """Base task with error handling and status updates."""
    
    autoretry_for = (ConnectionError, TimeoutError)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 3
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        action_id = kwargs.get('action_id')
        update_action_status(action_id, 'FAILED', str(exc))
        notify_failure(action_id, exc)
    
    def on_success(self, retval, task_id, args, kwargs):
        action_id = kwargs.get('action_id')
        update_action_status(action_id, 'COMPLETED', retval)
        notify_success(action_id)

@app.task(base=ActionTask, bind=True)
def execute_patch_deployment(self, action_id: str, devices: list, patch_id: str):
    """Deploy patch to specified devices."""
    try:
        update_action_status(action_id, 'EXECUTING')
        
        # Create MECM collection
        collection_id = mecm.create_collection(
            name=f"ITOA_Patch_{patch_id}_{action_id[:8]}",
            devices=devices
        )
        
        # Create deployment
        deployment_id = mecm.create_deployment(
            collection_id=collection_id,
            package_id=patch_id
        )
        
        return {
            'collection_id': collection_id,
            'deployment_id': deployment_id,
            'device_count': len(devices)
        }
    except Exception as e:
        self.retry(exc=e)
```

### 3.3 Rule Engine Design

#### 3.3.1 Rule Schema

```python
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from datetime import datetime

class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"

class Operator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    WITHIN_DAYS = "within_days"
    OLDER_THAN_DAYS = "older_than_days"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class LogicalOperator(str, Enum):
    AND = "and"
    OR = "or"

class RuleCondition(BaseModel):
    field: str
    operator: Operator
    value: any
    field_type: FieldType

class RuleConditionGroup(BaseModel):
    conditions: List[RuleCondition]
    logical_operator: LogicalOperator = LogicalOperator.AND

class RuleDefinition(BaseModel):
    id: Optional[str]
    name: str
    description: str
    category: str
    condition_groups: List[RuleConditionGroup]
    group_logical_operator: LogicalOperator = LogicalOperator.AND
    suggested_actions: List[str]
    schedule: Optional[str]  # Cron expression
    is_active: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime
```

#### 3.3.2 Available Fields

| Field Name | Source | Type | Description |
|------------|--------|------|-------------|
| `device_name` | MECM | string | Computer hostname |
| `operating_system` | MECM | string | OS name and version |
| `disk_free_space_gb` | MECM | number | Free disk space in GB |
| `disk_total_space_gb` | MECM | number | Total disk space in GB |
| `disk_free_percent` | MECM | number | Free space percentage |
| `last_active_date` | MECM | date | Last communication date |
| `last_active_days` | MECM | number | Days since last active |
| `primary_user` | MECM | string | Assigned user |
| `department` | CMDB | string | Department name |
| `location` | CMDB | string | Physical location |
| `eol_date` | SNOW | date | End of life date |
| `eos_date` | SNOW | date | End of support date |
| `eol_days_remaining` | SNOW | number | Days until EOL |
| `hardware_model` | MECM | string | Hardware model |
| `manufacturer` | MECM | string | Device manufacturer |
| `critical_patches_missing` | MECM | number | Count of missing critical patches |
| `total_patches_missing` | MECM | number | Count of all missing patches |
| `compliance_status` | MECM | string | Compliance state |
| `vulnerable_apps_count` | MECM | number | Apps with known vulnerabilities |

#### 3.3.3 Query Builder

```python
class QueryBuilder:
    """Build SQL queries from rule definitions."""
    
    FIELD_MAPPINGS = {
        'device_name': ('mecm', 'v_R_System', 'Name0'),
        'disk_free_space_gb': ('mecm', 'v_GS_LOGICAL_DISK', 'FreeSpace0 / 1024'),
        'last_active_date': ('mecm', 'v_R_System', 'LastActiveTime'),
        'eol_date': ('snow', 'u_eol_table', 'u_eol_date'),
        # ... more mappings
    }
    
    def build_query(self, rule: RuleDefinition) -> dict:
        """Generate queries for each data source."""
        mecm_conditions = []
        snow_conditions = []
        
        for group in rule.condition_groups:
            for condition in group.conditions:
                source, table, column = self.FIELD_MAPPINGS[condition.field]
                sql_condition = self._build_condition(column, condition)
                
                if source == 'mecm':
                    mecm_conditions.append(sql_condition)
                elif source == 'snow':
                    snow_conditions.append(sql_condition)
        
        return {
            'mecm_query': self._combine_conditions(mecm_conditions, rule.group_logical_operator),
            'snow_query': self._combine_conditions(snow_conditions, rule.group_logical_operator)
        }
    
    def _build_condition(self, column: str, condition: RuleCondition) -> str:
        """Convert condition to SQL WHERE clause."""
        op = condition.operator
        val = condition.value
        
        if op == Operator.EQUALS:
            return f"{column} = '{val}'"
        elif op == Operator.LESS_THAN:
            return f"{column} < {val}"
        elif op == Operator.WITHIN_DAYS:
            return f"DATEDIFF(day, GETDATE(), {column}) <= {val}"
        elif op == Operator.OLDER_THAN_DAYS:
            return f"DATEDIFF(day, {column}, GETDATE()) > {val}"
        # ... more operators
```

---

## 4. Data Design

### 4.1 Database Schema

#### 4.1.1 Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    users    │     │    rules    │     │rule_templates│
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)     │     │ id (PK)     │
│ azure_id    │◄────┤ created_by  │     │ name        │
│ email       │     │ name        │     │ category    │
│ display_name│     │ description │     │ definition  │
│ role        │     │ category    │     │ actions     │
│ created_at  │     │ definition  │     └─────────────┘
│ last_login  │     │ schedule    │
└─────────────┘     │ is_active   │
                    │ created_at  │
                    │ updated_at  │
                    └──────┬──────┘
                           │
                           │ 1:N
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│scan_results │     │rule_executions    │action_requests│
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)     │     │ id (PK)     │
│ execution_id│◄────┤ rule_id(FK) │     │ scan_id(FK) │
│ device_id   │     │ started_at  │     │ action_type │
│ device_name │     │ completed_at│     │ devices     │
│ matched_rules│    │ status      │────►│ status      │
│ risk_score  │     │ device_count│     │ created_by  │
│ device_data │     │ created_by  │     │ approved_by │
│ created_at  │     └─────────────┘     │ approved_at │
└─────────────┘                         │ executed_at │
                                        │ result      │
       ┌─────────────┐                  │ created_at  │
       │ audit_logs  │                  └─────────────┘
       ├─────────────┤
       │ id (PK)     │
       │ user_id(FK) │
       │ action      │
       │ entity_type │
       │ entity_id   │
       │ old_value   │
       │ new_value   │
       │ ip_address  │
       │ created_at  │
       └─────────────┘
```

#### 4.1.2 Table Definitions

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('operator', 'approver', 'administrator'))
);

-- Rules table
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,
    suggested_actions JSONB,
    schedule VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rule executions table
CREATE TABLE rule_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES rules(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    device_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Scan results table
CREATE TABLE scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES rule_executions(id),
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255) NOT NULL,
    matched_rules JSONB,
    risk_score INTEGER DEFAULT 0,
    device_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scan_results_execution (execution_id),
    INDEX idx_scan_results_device (device_id)
);

-- Action requests table
CREATE TABLE action_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES rule_executions(id),
    action_type VARCHAR(100) NOT NULL,
    devices JSONB NOT NULL,
    device_count INTEGER NOT NULL,
    parameters JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_action_status CHECK (status IN ('pending', 'approved', 'rejected', 'executing', 'completed', 'failed', 'cancelled'))
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_created (created_at)
);

-- Settings table
CREATE TABLE settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Rule Execution Data Flow                        │
└──────────────────────────────────────────────────────────────────────────┘

1. User triggers rule execution
   │
   ▼
2. Core Service loads rule definition
   │
   ▼
3. Query Builder generates source queries
   │
   ├──────────────────┬──────────────────┐
   ▼                  ▼                  ▼
4a. MECM Query    4b. SNOW Query    4c. Tachyon Query
   │                  │                  │
   ▼                  ▼                  ▼
5. Results aggregated and correlated by device_id
   │
   ▼
6. Rule conditions evaluated against aggregated data
   │
   ▼
7. Matching devices stored in scan_results
   │
   ▼
8. LLM Service generates suggestions (filtered data)
   │
   ▼
9. Results returned to desktop app
```

---

## 5. Integration Design

### 5.1 MECM Database Integration

**Connection Configuration:**
```python
class MECMConnector:
    """Read-only connector to MECM backup database."""
    
    def __init__(self, config: MECMConfig):
        self.engine = create_engine(
            f"mssql+pyodbc://{config.username}:{config.password}@"
            f"{config.server}/{config.database}?driver=ODBC+Driver+17+for+SQL+Server",
            pool_size=5,
            pool_recycle=3600,
            echo=False
        )
    
    def get_devices_with_low_disk(self, threshold_gb: int) -> List[dict]:
        """Query devices with disk space below threshold."""
        query = text("""
            SELECT 
                sys.ResourceID,
                sys.Name0 as DeviceName,
                disk.DeviceID0 as Drive,
                disk.Size0 / 1024 as TotalGB,
                disk.FreeSpace0 / 1024 as FreeGB,
                sys.User_Name0 as PrimaryUser,
                sys.AD_Site_Name0 as ADSite,
                sys.Operating_System_Name_and0 as OS
            FROM v_R_System sys
            INNER JOIN v_GS_LOGICAL_DISK disk ON sys.ResourceID = disk.ResourceID
            WHERE disk.DriveType0 = 3  -- Local disk
              AND disk.DeviceID0 = 'C:'
              AND disk.FreeSpace0 / 1024 < :threshold
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"threshold": threshold_gb})
            return [dict(row) for row in result]
```

**Available Queries:**
| Query | Description | Tables Used |
|-------|-------------|-------------|
| Get all devices | Basic device inventory | v_R_System |
| Disk space | Storage information | v_GS_LOGICAL_DISK |
| Installed software | Software inventory | v_GS_INSTALLED_SOFTWARE |
| Patch compliance | Update status | v_UpdateComplianceStatus |
| Collections | Device groupings | v_Collection, v_CollectionMembers |

### 5.2 ServiceNow Integration

**API Client:**
```python
class ServiceNowConnector:
    """ServiceNow REST API client."""
    
    def __init__(self, config: SNOWConfig):
        self.base_url = f"https://{config.instance}.service-now.com/api/now"
        self.auth = (config.username, config.password)
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def get_eol_records(self, days_ahead: int = 365) -> List[dict]:
        """Get devices with EOL within specified days."""
        target_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        response = self.session.get(
            f"{self.base_url}/table/u_eol_table",
            auth=self.auth,
            params={
                "sysparm_query": f"u_eol_date<=javascript:gs.dateGenerate('{target_date}')",
                "sysparm_fields": "u_device_id,u_device_name,u_eol_date,u_eos_date,u_model"
            }
        )
        response.raise_for_status()
        return response.json()["result"]
    
    def create_incident(self, incident_data: dict) -> str:
        """Create a new incident and return sys_id."""
        response = self.session.post(
            f"{self.base_url}/table/incident",
            auth=self.auth,
            json={
                "short_description": incident_data["title"],
                "description": incident_data["description"],
                "category": incident_data.get("category", "Hardware"),
                "impact": incident_data.get("impact", 3),
                "urgency": incident_data.get("urgency", 3),
                "assignment_group": incident_data.get("assignment_group"),
                "cmdb_ci": incident_data.get("ci_sys_id")
            }
        )
        response.raise_for_status()
        return response.json()["result"]["sys_id"]
```

### 5.3 1E Tachyon Integration

**Recommendation:** Use 1E Tachyon for:
- Real-time device queries (when MECM data is stale)
- Executing remediation scripts on endpoints
- Software deployment confirmation
- Disk cleanup operations

**API Client:**
```python
class TachyonConnector:
    """1E Tachyon API client."""
    
    def __init__(self, config: TachyonConfig):
        self.base_url = config.base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        })
    
    def execute_instruction(self, instruction_id: str, devices: List[str]) -> str:
        """Execute a Tachyon instruction on specified devices."""
        response = self.session.post(
            f"{self.base_url}/Consumer/Instructions",
            json={
                "InstructionDefinitionId": instruction_id,
                "Scope": {
                    "Devices": [{"Fqdn": d} for d in devices]
                }
            }
        )
        response.raise_for_status()
        return response.json()["InstructionId"]
    
    def get_instruction_results(self, instruction_id: str) -> List[dict]:
        """Get results of an instruction execution."""
        response = self.session.get(
            f"{self.base_url}/Consumer/Instructions/{instruction_id}/Responses"
        )
        response.raise_for_status()
        return response.json()["Responses"]
    
    # Pre-defined instruction IDs
    INSTRUCTIONS = {
        "disk_cleanup": "1e-tachyon-disk-cleanup-instruction-id",
        "get_disk_space": "1e-tachyon-get-diskspace-instruction-id",
        "restart_service": "1e-tachyon-restart-service-instruction-id"
    }
```

### 5.4 Notification Integration

**Email/Teams Notifications:**
```python
class NotificationService:
    """Send notifications via email and Microsoft Teams."""
    
    def __init__(self, config: NotificationConfig):
        self.smtp_config = config.smtp
        self.teams_webhook = config.teams_webhook_url
        self.graph_client = GraphClient(config.graph_credentials)
    
    async def send_user_notification(self, user_email: str, template: str, data: dict):
        """Send notification to end user."""
        template_content = self.load_template(template)
        rendered = self.render_template(template_content, data)
        
        await self.send_email(
            to=user_email,
            subject=rendered["subject"],
            body=rendered["body"]
        )
    
    async def send_team_notification(self, channel: str, message: dict):
        """Send notification to Teams channel."""
        await self.session.post(
            self.teams_webhook,
            json={
                "@type": "MessageCard",
                "summary": message["title"],
                "sections": [{
                    "activityTitle": message["title"],
                    "facts": message["facts"],
                    "text": message["body"]
                }]
            }
        )
```

---

## 6. Security Design

### 6.1 Authentication Flow

The system uses the **OAuth 2.0 Authorization Code Flow** for secure authentication. This flow is recommended for applications with a backend server because:
- Client secret stays on the server (never exposed to desktop app)
- Azure tokens are managed server-side (never touch client device)
- Centralized session management enables easy access revocation

#### 6.1.1 Authorization Code Flow Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Desktop    │     │   Backend    │     │  Microsoft   │     │   Azure AD   │
│     App      │     │  (OpenShift) │     │ Login Page   │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │ 1. Click Login     │                    │                    │
       │───────────────────►│                    │                    │
       │                    │                    │                    │
       │ 2. Return Auth URL │                    │                    │
       │◄───────────────────│                    │                    │
       │                    │                    │                    │
       │ 3. Open System Browser                  │                    │
       │─────────────────────────────────────────►                    │
       │                    │                    │                    │
       │                    │    4. User Authenticates (MFA)          │
       │                    │                    │◄───────────────────►
       │                    │                    │                    │
       │                    │ 5. Redirect with Authorization Code     │
       │                    │◄───────────────────│                    │
       │                    │                    │                    │
       │                    │ 6. Exchange Code for Access Token       │
       │                    │────────────────────────────────────────►│
       │                    │                    │                    │
       │                    │ 7. Return Access Token + Refresh Token  │
       │                    │◄────────────────────────────────────────│
       │                    │                    │                    │
       │ 8. Return Application JWT/Session Token │                    │
       │◄───────────────────│                    │                    │
       │                    │                    │                    │
```

#### 6.1.2 Flow Steps Explained

| Step | Component | Action |
|------|-----------|--------|
| **1** | Desktop App | User clicks "Login" button |
| **2** | Backend (Auth Service) | Returns Microsoft authorization URL with client_id, redirect_uri, scope |
| **3** | Desktop App | Opens system browser to Microsoft login page |
| **4** | Microsoft/Azure AD | User authenticates with credentials and MFA (if configured) |
| **5** | Microsoft | Redirects to backend callback URL (`/auth/callback`) with authorization code |
| **6** | Backend (Auth Service) | Exchanges authorization code for tokens (server-to-server, includes client_secret) |
| **7** | Azure AD | Returns access_token, refresh_token, and id_token |
| **8** | Backend (Auth Service) | Issues application-specific JWT to desktop app for subsequent API calls |

#### 6.1.3 Azure AD App Registration

```yaml
Azure AD App Registration:
  Application (client) ID: <your-client-id>
  Directory (tenant) ID: <your-tenant-id>
  
  Authentication:
    Platform: Web
    Redirect URI: https://itoa-backend.openshift.company.com/auth/callback
    
  Certificates & secrets:
    Client secret: <stored in OpenShift secrets / Azure Key Vault>
    
  Token configuration:
    - Access tokens (for API calls)
    - ID tokens (for user info)
    
  API permissions:
    - Microsoft Graph: User.Read (delegated)
    - Microsoft Graph: email (delegated)
    - Microsoft Graph: profile (delegated)
```

#### 6.1.4 Backend Implementation

```python
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import msal
import secrets

router = APIRouter(prefix="/auth", tags=["Authentication"])

# MSAL Configuration
MSAL_CONFIG = {
    "client_id": settings.AZURE_CLIENT_ID,
    "client_secret": settings.AZURE_CLIENT_SECRET,
    "authority": f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
    "redirect_uri": settings.AZURE_REDIRECT_URI,
    "scope": ["User.Read", "email", "profile"]
}

msal_app = msal.ConfidentialClientApplication(
    MSAL_CONFIG["client_id"],
    authority=MSAL_CONFIG["authority"],
    client_credential=MSAL_CONFIG["client_secret"]
)

@router.get("/login")
async def login(request: Request):
    """Step 1-2: Initiate OAuth flow, return authorization URL."""
    # Generate state token to prevent CSRF
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    
    auth_url = msal_app.get_authorization_request_url(
        scopes=MSAL_CONFIG["scope"],
        state=state,
        redirect_uri=MSAL_CONFIG["redirect_uri"]
    )
    
    return {"auth_url": auth_url}

@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    """Step 5-7: Exchange authorization code for tokens."""
    # Verify state to prevent CSRF
    if state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for tokens (server-to-server)
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=MSAL_CONFIG["scope"],
        redirect_uri=MSAL_CONFIG["redirect_uri"]
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result.get("error_description"))
    
    # Extract user info from ID token
    user_info = result.get("id_token_claims", {})
    
    # Create or update user in database
    user = await user_service.upsert_user(
        azure_id=user_info.get("oid"),
        email=user_info.get("preferred_username"),
        display_name=user_info.get("name")
    )
    
    # Store Azure tokens for later use (Graph API calls, etc.)
    await token_service.store_tokens(
        user_id=user.id,
        access_token=result.get("access_token"),
        refresh_token=result.get("refresh_token"),
        expires_at=result.get("expires_in")
    )
    
    # Generate application JWT for desktop app
    app_token = create_application_jwt(user)
    
    # Redirect to desktop app with token (via custom protocol or localhost)
    return RedirectResponse(f"itoa-agent://auth/success?token={app_token}")

@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh the application JWT using stored Azure refresh token."""
    user = await get_current_user(request)
    
    # Get stored refresh token
    stored_tokens = await token_service.get_tokens(user.id)
    
    # Use MSAL to refresh Azure tokens
    result = msal_app.acquire_token_by_refresh_token(
        refresh_token=stored_tokens.refresh_token,
        scopes=MSAL_CONFIG["scope"]
    )
    
    if "error" in result:
        raise HTTPException(status_code=401, detail="Session expired, please login again")
    
    # Update stored tokens
    await token_service.store_tokens(
        user_id=user.id,
        access_token=result.get("access_token"),
        refresh_token=result.get("refresh_token"),
        expires_at=result.get("expires_in")
    )
    
    # Issue new application JWT
    new_app_token = create_application_jwt(user)
    
    return {"token": new_app_token}
```

#### 6.1.5 Desktop App Integration

```python
import webbrowser
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QTcpServer

class AuthService:
    """Handle OAuth flow from desktop app."""
    
    def __init__(self, api_client):
        self.api = api_client
        self.callback_server = None
    
    async def login(self):
        """Initiate login flow."""
        # Step 1: Get authorization URL from backend
        response = await self.api.get("/auth/login")
        auth_url = response["auth_url"]
        
        # Step 3: Open system browser for Microsoft login
        webbrowser.open(auth_url)
        
        # Wait for callback (via custom protocol handler or local server)
        token = await self._wait_for_callback()
        
        return token
    
    async def _wait_for_callback(self):
        """Wait for OAuth callback with token."""
        # Option A: Custom protocol handler (itoa-agent://)
        # Option B: Local HTTP server on localhost
        # Implementation depends on deployment requirements
        pass
```

#### 6.1.6 Security Benefits

| Benefit | Description |
|---------|-------------|
| **Client Secret Protection** | Secret never leaves the backend server |
| **Token Security** | Azure tokens stored server-side, not on user devices |
| **Centralized Revocation** | Can invalidate all sessions from backend |
| **MFA Support** | Leverages Azure AD MFA without additional code |
| **Audit Trail** | All authentications logged server-side |
| **SSO Ready** | Users already logged into Microsoft 365 may not need to re-authenticate |

### 6.2 Authorization Matrix

```python
class Permission(Enum):
    VIEW_DASHBOARD = "view:dashboard"
    VIEW_RULES = "view:rules"
    CREATE_RULES = "create:rules"
    EDIT_RULES = "edit:rules"
    DELETE_RULES = "delete:rules"
    EXECUTE_SCANS = "execute:scans"
    VIEW_RESULTS = "view:results"
    CREATE_ACTIONS = "create:actions"
    APPROVE_ACTIONS = "approve:actions"
    VIEW_REPORTS = "view:reports"
    MANAGE_USERS = "manage:users"
    MANAGE_SETTINGS = "manage:settings"

ROLE_PERMISSIONS = {
    "operator": [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_RULES,
        Permission.EXECUTE_SCANS,
        Permission.VIEW_RESULTS,
        Permission.CREATE_ACTIONS,
        Permission.VIEW_REPORTS,
    ],
    "approver": [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_RULES,
        Permission.EXECUTE_SCANS,
        Permission.VIEW_RESULTS,
        Permission.CREATE_ACTIONS,
        Permission.APPROVE_ACTIONS,
        Permission.VIEW_REPORTS,
    ],
    "administrator": [
        # All permissions
        *Permission
    ]
}
```

### 6.3 Sensitive Data Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Classification                           │
├─────────────────────────────────────────────────────────────────┤
│  PUBLIC         │ Device count, categories, aggregated stats   │
│  INTERNAL       │ Device names, locations, departments          │
│  CONFIDENTIAL   │ User names, email addresses, IP addresses    │
│  RESTRICTED     │ Credentials, API keys, personal data          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Handling by Classification                    │
├─────────────────────────────────────────────────────────────────┤
│  LLM Processing │ PUBLIC + sanitized INTERNAL only              │
│  Audit Logs     │ INTERNAL + masked CONFIDENTIAL                │
│  UI Display     │ All (based on user role)                      │
│  API Responses  │ All (based on user permissions)               │
│  Exports        │ PUBLIC + INTERNAL (admin: CONFIDENTIAL)       │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 API Security

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate token and return current user."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user = await user_service.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_permission(permission: Permission):
    """Dependency to check user permission."""
    async def permission_checker(user: User = Depends(get_current_user)):
        if permission not in ROLE_PERMISSIONS.get(user.role, []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return permission_checker

# Usage in endpoint
@router.post("/rules")
async def create_rule(
    rule: RuleCreate,
    user: User = Depends(require_permission(Permission.CREATE_RULES))
):
    return await rule_service.create(rule, user)
```

---

## 7. User Interface Design

### 7.1 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Clarity** | Clear labels, consistent terminology |
| **Feedback** | Loading states, success/error messages |
| **Efficiency** | Keyboard shortcuts, bulk operations |
| **Safety** | Confirmation dialogs, undo where possible |
| **Accessibility** | WCAG 2.1 AA compliance |

### 7.2 Wireframes

#### 7.2.1 Dashboard

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰ IT Operations AI Agent                               John Doe ▼   ⚙  ?    │
├───────┬──────────────────────────────────────────────────────────────────────┤
│       │                                                                       │
│  📊   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│ Dash  │  │   Devices   │  │   Issues    │  │  Pending    │  │  Actions    │  │
│       │  │   Scanned   │  │   Found     │  │  Approvals  │  │   Today     │  │
│  📋   │  │   98,432    │  │    1,247    │  │      5      │  │     12      │  │
│ Rules │  │   ↑ 2.1%    │  │   ↓ 15%     │  │   ⚠ Alert   │  │   ✓ Good    │  │
│       │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│  🔍   │                                                                       │
│ Scans │  Issues by Category                  Recent Activity                  │
│       │  ┌────────────────────────────┐      ┌────────────────────────────┐  │
│  ⚡   │  │  ████████████  Low Disk    │      │ 10:32  Rule "EOL-1Y" exec  │  │
│Actions│  │  ██████       EOL Soon     │      │ 10:15  Action approved     │  │
│       │  │  ████         Patches      │      │ 09:45  New rule created    │  │
│  📈   │  │  ██           Compliance   │      │ 09:30  Scan completed      │  │
│Reports│  └────────────────────────────┘      └────────────────────────────┘  │
│       │                                                                       │
│  ⚙    │  Quick Actions                                                       │
│Settings│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │
│       │  │ + New Rule   │ │ Run All Scans│ │ View Pending │                  │
│       │  └──────────────┘ └──────────────┘ └──────────────┘                  │
└───────┴──────────────────────────────────────────────────────────────────────┘
```

#### 7.2.2 Rule Builder

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰ IT Operations AI Agent                               John Doe ▼   ⚙  ?    │
├───────┬──────────────────────────────────────────────────────────────────────┤
│       │  Rules > Create New Rule                                             │
│  📊   │  ─────────────────────────────────────────────────────────────────   │
│ Dash  │                                                                       │
│       │  ┌────────────────────────────────────────────────────────────────┐  │
│  📋   │  │ 💬 Describe your rule in plain English:                        │  │
│ Rules │  │ ┌────────────────────────────────────────────────────────────┐ │  │
│  ←    │  │ │ Find devices with less than 10GB free disk space that     │ │  │
│       │  │ │ haven't been active in 4 weeks                            │ │  │
│  🔍   │  │ └────────────────────────────────────────────────────────────┘ │  │
│ Scans │  │                                     [ 🤖 Generate Rule ]        │  │
│       │  └────────────────────────────────────────────────────────────────┘  │
│  ⚡   │                                                                       │
│Actions│  ── OR build manually ─────────────────────────────────────────────   │
│       │                                                                       │
│  📈   │  Rule Name: [ Low Disk Inactive Devices                          ]   │
│Reports│  Category:  [ Disk Space                               ▼ ]          │
│       │  Description: [ Devices needing cleanup or retirement            ]   │
│  ⚙    │                                                                       │
│Settings│ Conditions:                                                          │
│       │  ┌────────────────────────────────────────────────────────────────┐  │
│       │  │ IF  [ Disk Free Space GB  ▼]  [ <  ▼]  [ 10        ]  [AND ▼]  │  │
│       │  │ AND [ Last Active Days    ▼]  [ >  ▼]  [ 28        ]          │  │
│       │  │                                            [ + Add Condition ] │  │
│       │  └────────────────────────────────────────────────────────────────┘  │
│       │                                                                       │
│       │  Suggested Actions:                                                   │
│       │  ☑ Send User Notification    ☐ Create Incident    ☐ Run Tachyon     │
│       │                                                                       │
│       │  Schedule: [ Manual ▼ ]   [ Every Day ▼ ]   [ 08:00 AM ▼ ]          │
│       │                                                                       │
│       │                              [ Cancel ]  [ Save as Draft ]  [ Save ] │
└───────┴──────────────────────────────────────────────────────────────────────┘
```

#### 7.2.3 Scan Results with AI Suggestions

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰ IT Operations AI Agent                               John Doe ▼   ⚙  ?    │
├───────┬──────────────────────────────────────────────────────────────────────┤
│       │  Scan Results: "Low Disk Inactive Devices" - 1,247 devices found     │
│  📊   │  ─────────────────────────────────────────────────────────────────   │
│ Dash  │                                                                       │
│       │  ┌─ AI Suggestions ──────────────────────────────────────────────┐   │
│  📋   │  │ 🤖 Based on analysis of 1,247 devices:                        │   │
│ Rules │  │                                                                │   │
│       │  │ 1. Create MECM Collection "DiskCleanup_2026-01" (1,100 active) │   │
│  🔍   │  │    → Deploy disk cleanup script via Tachyon                   │   │
│ Scans │  │                                                                │   │
│  ←    │  │ 2. Send notifications to 147 inactive device users            │   │
│       │  │    → Likely unused devices, consider retirement               │   │
│  ⚡   │  │                                                                │   │
│Actions│  │ [ Apply Suggestion 1 ]  [ Apply Suggestion 2 ]  [ Dismiss ]   │   │
│       │  └────────────────────────────────────────────────────────────────┘   │
│  📈   │                                                                       │
│Reports│  Filter: [ All Categories ▼ ]  Search: [                    🔍 ]    │
│       │                                                                       │
│  ⚙    │  ☐ │ Device Name    │ User          │ Dept     │ Free GB │ Days  │  │
│Settings│ ───┼────────────────┼───────────────┼──────────┼─────────┼───────│  │
│       │  ☐ │ WS-NYC-12345   │ john.doe      │ Finance  │  5.2 GB │  45   │  │
│       │  ☐ │ WS-NYC-12346   │ jane.smith    │ Finance  │  3.1 GB │  32   │  │
│       │  ☐ │ WS-LON-78901   │ bob.wilson    │ IT       │  8.7 GB │  29   │  │
│       │  ☑ │ WS-LON-78902   │ alice.jones   │ HR       │  2.3 GB │  60   │  │
│       │                                                                       │
│       │  Selected: 1                [ Export CSV ]  [ Create Action ▼ ]      │
│       │                                                                       │
│       │  ◀ 1 2 3 ... 125 ▶    Showing 1-10 of 1,247                         │
└───────┴──────────────────────────────────────────────────────────────────────┘
```

#### 7.2.4 Action Approval

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰ IT Operations AI Agent                               John Doe ▼   ⚙  ?    │
├───────┬──────────────────────────────────────────────────────────────────────┤
│       │  Pending Approvals (5)                                               │
│  📊   │  ─────────────────────────────────────────────────────────────────   │
│ Dash  │                                                                       │
│       │  ┌────────────────────────────────────────────────────────────────┐  │
│  📋   │  │ ⚠ Action Request #AR-2026-0142                                 │  │
│ Rules │  │                                                                 │  │
│       │  │ Type: Create MECM Collection + Deployment                      │  │
│  🔍   │  │ Requested by: jane.smith@company.com                           │  │
│ Scans │  │ Requested: Jan 31, 2026 10:32 AM                               │  │
│       │  │                                                                 │  │
│  ⚡   │  │ Summary:                                                        │  │
│Actions│  │ • Collection: "Finance_DiskCleanup_2026-01"                    │  │
│  ←    │  │ • Devices: 120 (Finance Department)                            │  │
│       │  │ • Action: Deploy Disk Cleanup Script                           │  │
│  📈   │  │                                                                 │  │
│Reports│  │ Device Preview:                                                 │  │
│       │  │ ┌──────────────────────────────────────────────────────────┐   │  │
│  ⚙    │  │ │ WS-NYC-12345 (5.2 GB free) - john.doe                   │   │  │
│Settings│  │ │ WS-NYC-12346 (3.1 GB free) - jane.smith                 │   │  │
│       │  │ │ WS-NYC-12347 (4.8 GB free) - mike.brown                  │   │  │
│       │  │ │ ... and 117 more devices                                 │   │  │
│       │  │ └──────────────────────────────────────────────────────────┘   │  │
│       │  │                                                                 │  │
│       │  │ Notes from requestor:                                          │  │
│       │  │ "Routine cleanup for Finance devices with low disk space"     │  │
│       │  │                                                                 │  │
│       │  │ Approver Comments: [                                        ]  │  │
│       │  │                                                                 │  │
│       │  │          [ View All Devices ]  [ ✗ Reject ]  [ ✓ Approve ]    │  │
│       │  └────────────────────────────────────────────────────────────────┘  │
└───────┴──────────────────────────────────────────────────────────────────────┘
```

### 7.3 Accessibility Implementation

```python
class AccessibleWidget(QWidget):
    """Base class for WCAG-compliant widgets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_accessibility()
    
    def setup_accessibility(self):
        """Configure accessibility properties."""
        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Set accessible name and description
        self.setAccessibleName(self.__class__.__name__)
        
    def set_accessible_info(self, name: str, description: str = "", role: str = ""):
        """Set accessibility information for screen readers."""
        self.setAccessibleName(name)
        self.setAccessibleDescription(description)
        if role:
            # Set role hint for assistive technologies
            self.setProperty("accessibleRole", role)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Space:
            self.activate()
        else:
            super().keyPressEvent(event)
    
    def activate(self):
        """Override in subclasses for activation behavior."""
        pass

class AccessibleDataTable(QTableView):
    """WCAG-compliant data table."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Accessibility settings
        self.setAccessibleName("Data Table")
        self.setAlternatingRowColors(True)  # Visual distinction
        
        # Keyboard navigation
        self.setTabKeyNavigation(True)
        
        # High contrast selection
        palette = self.palette()
        palette.setColor(QPalette.Highlight, QColor("#0066CC"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Focus indicator
        self.setStyleSheet("""
            QTableView:focus {
                border: 2px solid #0066CC;
            }
            QTableView::item:focus {
                border: 2px solid #FF6600;
            }
        """)
```

### 7.4 Theme Support

```python
# Light theme (light_theme.qss)
LIGHT_THEME = """
QMainWindow {
    background-color: #FFFFFF;
    color: #1A1A1A;
}

QPushButton {
    background-color: #0066CC;
    color: #FFFFFF;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #0052A3;
}

QPushButton:focus {
    outline: 2px solid #FF6600;
    outline-offset: 2px;
}

/* Ensure 4.5:1 contrast ratio */
QLabel {
    color: #1A1A1A;  /* On white: 12.6:1 */
}

QLineEdit {
    border: 1px solid #767676;  /* 4.5:1 contrast */
    padding: 8px;
    border-radius: 4px;
}
"""

# Dark theme (dark_theme.qss)  
DARK_THEME = """
QMainWindow {
    background-color: #1A1A1A;
    color: #FFFFFF;
}

QPushButton {
    background-color: #3399FF;
    color: #000000;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QLabel {
    color: #FFFFFF;  /* On dark: 12.6:1 */
}
"""
```

---

## 8. Deployment Design

### 8.1 Kubernetes Architecture

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: itoa-core-service
  namespace: itoa-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: itoa-core
  template:
    metadata:
      labels:
        app: itoa-core
    spec:
      containers:
      - name: core-service
        image: registry.company.com/itoa/core-service:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: itoa-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: itoa-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: itoa-core-service
  namespace: itoa-agent
spec:
  selector:
    app: itoa-core
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### 8.2 Infrastructure Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         OpenShift Cluster                                 │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                          Ingress                                    │  │
│  │                    (Route/HAProxy)                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                               │                                           │
│         ┌─────────────────────┼─────────────────────┐                    │
│         ▼                     ▼                     ▼                    │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐            │
│  │ Auth Service│       │Core Service │       │ LLM Service │            │
│  │  (2 pods)   │       │  (2 pods)   │       │  (2 pods)   │            │
│  └─────────────┘       └─────────────┘       └─────────────┘            │
│         │                     │                     │                    │
│         └─────────────────────┼─────────────────────┘                    │
│                               ▼                                          │
│                    ┌─────────────────────┐                               │
│                    │   Action Worker     │                               │
│                    │    (3 pods)         │                               │
│                    └─────────────────────┘                               │
│                               │                                          │
│         ┌─────────────────────┼─────────────────────┐                    │
│         ▼                     ▼                     ▼                    │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐            │
│  │ PostgreSQL  │       │    Redis    │       │  Local LLM  │            │
│  │ (StatefulSet)│      │ (StatefulSet)│      │   (QWEN)    │            │
│  └─────────────┘       └─────────────┘       └─────────────┘            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │  MECM DB    │      │ ServiceNow  │      │ 1E Tachyon  │
   │  (On-prem)  │      │  (Cloud)    │      │  (On-prem)  │
   └─────────────┘      └─────────────┘      └─────────────┘
```

### 8.3 CI/CD Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - security
  - deploy

variables:
  DOCKER_REGISTRY: registry.company.com/itoa

test:
  stage: test
  script:
    - pip install -r requirements-dev.txt
    - pytest --cov=src tests/
    - pylint src/
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'

build:
  stage: build
  script:
    - docker build -t $DOCKER_REGISTRY/core-service:$CI_COMMIT_SHA .
    - docker push $DOCKER_REGISTRY/core-service:$CI_COMMIT_SHA

security_scan:
  stage: security
  script:
    - trivy image $DOCKER_REGISTRY/core-service:$CI_COMMIT_SHA
    - bandit -r src/

deploy_staging:
  stage: deploy
  environment: staging
  script:
    - kubectl set image deployment/itoa-core-service 
        core-service=$DOCKER_REGISTRY/core-service:$CI_COMMIT_SHA
        -n itoa-staging
  only:
    - develop

deploy_production:
  stage: deploy
  environment: production
  script:
    - kubectl set image deployment/itoa-core-service 
        core-service=$DOCKER_REGISTRY/core-service:$CI_COMMIT_SHA
        -n itoa-production
  when: manual
  only:
    - main
```

---

## 9. Error Handling & Logging

### 9.1 Error Categories

| Category | Handling | User Message |
|----------|----------|--------------|
| **Authentication** | Redirect to login | "Session expired. Please log in again." |
| **Authorization** | Show error | "You don't have permission for this action." |
| **Validation** | Highlight field | "Please correct the highlighted fields." |
| **Network** | Retry with backoff | "Connection issue. Retrying..." |
| **External API** | Queue for retry | "External service unavailable. Action queued." |
| **Data** | Log and alert | "Data processing error. Support notified." |

### 9.2 Logging Strategy

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info(
    "rule_executed",
    rule_id=rule.id,
    rule_name=rule.name,
    devices_found=len(results),
    duration_ms=duration,
    user_id=current_user.id
)
```

### 9.3 Monitoring & Alerting

```yaml
# Prometheus alerts
groups:
- name: itoa-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: ActionWorkerDown
    expr: up{job="action-worker"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Action worker is down"
      
  - alert: PendingActionsBacklog
    expr: action_requests_pending > 100
    for: 30m
    labels:
      severity: warning
    annotations:
      summary: "Large backlog of pending actions"
```

---

## 10. Testing Strategy

### 10.1 Test Pyramid

```
                    ┌───────────────┐
                   /   E2E Tests    \        5%
                  /   (Selenium)     \
                 /─────────────────────\
                /   Integration Tests   \    20%
               /    (API, Database)      \
              /───────────────────────────\
             /       Unit Tests            \   75%
            /   (Pytest, Mock external)     \
           /─────────────────────────────────\
```

### 10.2 Test Categories

| Category | Tools | Coverage Target |
|----------|-------|-----------------|
| Unit Tests | pytest, unittest.mock | 80% |
| Integration Tests | pytest, testcontainers | Key flows |
| API Tests | pytest, httpx | All endpoints |
| UI Tests | pytest-qt | Critical paths |
| E2E Tests | Selenium, pytest | Happy paths |
| Security Tests | bandit, safety | All code |
| Accessibility Tests | axe-core, manual | WCAG AA |

### 10.3 Example Tests

```python
# Unit test for rule engine
class TestRuleEngine:
    def test_evaluate_disk_space_condition(self):
        condition = RuleCondition(
            field="disk_free_space_gb",
            operator=Operator.LESS_THAN,
            value=10,
            field_type=FieldType.NUMBER
        )
        
        device_data = {"disk_free_space_gb": 5}
        
        result = RuleEngine.evaluate_condition(condition, device_data)
        
        assert result is True
    
    def test_evaluate_date_condition(self):
        condition = RuleCondition(
            field="last_active_date",
            operator=Operator.OLDER_THAN_DAYS,
            value=28,
            field_type=FieldType.DATE
        )
        
        device_data = {
            "last_active_date": datetime.now() - timedelta(days=30)
        }
        
        result = RuleEngine.evaluate_condition(condition, device_data)
        
        assert result is True

# Integration test for API
class TestRulesAPI:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_create_rule(self, client, auth_headers):
        rule_data = {
            "name": "Test Rule",
            "category": "Disk Space",
            "condition_groups": [{
                "conditions": [{
                    "field": "disk_free_space_gb",
                    "operator": "lt",
                    "value": 10,
                    "field_type": "number"
                }]
            }]
        }
        
        response = await client.post(
            "/api/rules",
            json=rule_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["name"] == "Test Rule"
```

---

## Appendix A: API Reference

Full OpenAPI specification available at `/api/docs` when service is running.

## Appendix B: Configuration Reference

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `AZURE_CLIENT_ID` | Azure AD app client ID | Required |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Required |
| `LLM_PROVIDER` | openai, azure_openai, qwen | openai |
| `LLM_API_KEY` | API key for LLM provider | Required* |
| `MECM_SERVER` | MECM database server | Required |
| `SNOW_INSTANCE` | ServiceNow instance name | Required |
| `LOG_LEVEL` | Logging level | INFO |

## Appendix C: Glossary

See Requirements Document Appendix B.

---

**Document Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Architect | | | |
| Security Architect | | | |
| Development Lead | | | |
| QA Lead | | | |

---

*End of Design Document*
