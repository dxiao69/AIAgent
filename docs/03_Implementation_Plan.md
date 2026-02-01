# IT Operations AI Agent - Implementation Plan

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Project Name:** IT Operations AI Agent (ITOA Agent)  
**Estimated Duration:** 12-14 Weeks

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Phase Overview](#2-phase-overview)
3. [Detailed Phase Breakdown](#3-detailed-phase-breakdown)
4. [Resource Requirements](#4-resource-requirements)
5. [Risk Management](#5-risk-management)
6. [Dependencies](#6-dependencies)
7. [Milestones & Deliverables](#7-milestones--deliverables)
8. [Success Criteria](#8-success-criteria)

---

## 1. Executive Summary

### 1.1 Project Goals

Deliver a fully functional IT Operations AI Agent that enables operations staff to:
- Define rules for identifying problematic devices AND applications
- Automatically scan 100,000+ devices and applications against defined rules
- Track vulnerabilities (CVE) and coordinate with application owners
- Receive AI-powered remediation suggestions
- Execute approved actions across MECM, ServiceNow, and 1E Tachyon
- Validate AI/LLM accuracy through ground truth testing

### 1.2 Timeline Overview

```
Week:  1   2   3   4   5   6   7   8   9  10  11  12  13  14
       ├───┴───┤                                              Phase 1: Foundation
               ├───┴───┴───┤                                  Phase 2: Core Backend
                       ├───┴───┴───┤                          Phase 3: Desktop App
                               ├───┴───┴───┤                  Phase 4: LLM Integration
                                       ├───┴───┴───┴───┤      Phase 5: Actions
                                                   ├───┴───┤  Phase 6: Polish
```

### 1.3 Key Deliverables

| Phase | Deliverable | Target Week |
|-------|-------------|-------------|
| 1 | Infrastructure + Auth Service | Week 2 |
| 2 | Core Service + Rule Engine + App Scanning | Week 5 |
| 3 | Desktop App MVP | Week 7 |
| 4 | LLM Service + AI Features + Ground Truth Tests | Week 9 |
| 5 | Full Action Execution + App Owner Workflow | Week 12 |
| 6 | Production-Ready Release | Week 14 |

---

## 2. Phase Overview

### 2.1 Phase Summary

| Phase | Name | Duration | Focus |
|-------|------|----------|-------|
| **1** | Foundation | 2 weeks | Infrastructure, Auth, Project Setup |
| **2** | Core Backend | 3 weeks | Rule Engine, MECM Integration, Device & App Scanning |
| **3** | Desktop App MVP | 2 weeks | UI Framework, Core Screens |
| **4** | LLM Integration | 2 weeks | AI Suggestions, NL Processing, Ground Truth Testing |
| **5** | Actions & Integrations | 3 weeks | ServiceNow, Tachyon, App Owner Workflow, Approval |
| **6** | Polish & Compliance | 2 weeks | Accessibility, Testing, Documentation |

### 2.2 Build Order & Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          IMPLEMENTATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1                    Phase 2                    Phase 3
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ PostgreSQL   │────┐     │ MECM         │────┐     │ Desktop      │
│ Schema       │    │     │ Connector    │    │     │ Framework    │
└──────────────┘    │     └──────────────┘    │     └──────────────┘
                    │                          │            │
┌──────────────┐    │     ┌──────────────┐    │     ┌──────────────┐
│ Redis        │────┼────►│ Rule Engine  │────┼────►│ Rules UI     │
│ Setup        │    │     │              │    │     │              │
└──────────────┘    │     └──────────────┘    │     └──────────────┘
                    │                          │            │
┌──────────────┐    │     ┌──────────────┐    │     ┌──────────────┐
│ Auth Service │────┘     │ Scan Engine  │────┘     │ Scan Results │
│ (Azure OAuth)│          │              │          │ UI           │
└──────────────┘          └──────────────┘          └──────────────┘
       │                         │                         │
       └─────────────────────────┴─────────────────────────┘
                                 │
                                 ▼
Phase 4                    Phase 5                    Phase 6
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ LLM Service  │────┐     │ ServiceNow   │────┐     │ WCAG         │
│ Abstraction  │    │     │ Connector    │    │     │ Compliance   │
└──────────────┘    │     └──────────────┘    │     └──────────────┘
                    │                          │            │
┌──────────────┐    │     ┌──────────────┐    │     ┌──────────────┐
│ Data Filter  │────┼────►│ Tachyon      │────┼────►│ Performance  │
│              │    │     │ Connector    │    │     │ Testing      │
└──────────────┘    │     └──────────────┘    │     └──────────────┘
                    │                          │            │
┌──────────────┐    │     ┌──────────────┐    │     ┌──────────────┐
│ NL Rule      │────┘     │ Action Worker│────┘     │ E2E Testing  │
│ Creation     │          │ (Celery)     │          │              │
└──────────────┘          └──────────────┘          └──────────────┘
```

---

## 3. Detailed Phase Breakdown

### 3.1 Phase 1: Foundation (Week 1-2)

**Objective:** Establish project infrastructure, development environment, and authentication.

#### Week 1: Project Setup & Infrastructure

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **1.1.1** | Create project repository structure | Backend | 0.5 |
| **1.1.2** | Set up Python monorepo with shared packages | Backend | 0.5 |
| **1.1.3** | Configure development environment (Docker Compose) | DevOps | 1 |
| **1.1.4** | Create PostgreSQL database schema | Backend | 1 |
| **1.1.5** | Set up Redis for caching and queues | Backend | 0.5 |
| **1.1.6** | Configure CI/CD pipeline (GitLab/GitHub Actions) | DevOps | 1 |
| **1.1.7** | Set up code quality tools (pylint, black, mypy) | Backend | 0.5 |

**Project Structure to Create:**
```
itoa-agent/
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── .gitlab-ci.yml
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── test.txt
├── services/
│   ├── auth-service/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   ├── core-service/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   ├── llm-service/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   └── action-worker/
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── src/
├── desktop/
│   ├── pyproject.toml
│   └── src/
│       └── itoa_desktop/
├── shared/
│   ├── pyproject.toml
│   └── src/
│       └── itoa_shared/
├── k8s/
│   ├── base/
│   ├── staging/
│   └── production/
├── scripts/
│   ├── setup-dev.sh
│   └── run-tests.sh
└── docs/
    ├── 01_Requirements_Document.md
    ├── 02_Design_Document.md
    └── 03_Implementation_Plan.md
```

#### Week 2: Auth Service

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **1.2.1** | Implement Azure OAuth 2.0 integration | Backend | 2 |
| **1.2.2** | Create JWT token generation/validation | Backend | 1 |
| **1.2.3** | Implement RBAC middleware | Backend | 1 |
| **1.2.4** | Create user management endpoints | Backend | 0.5 |
| **1.2.5** | Write unit tests for auth service | Backend | 0.5 |

**Auth Service API Endpoints:**
```
POST /auth/login          - Initiate OAuth flow
POST /auth/callback       - OAuth callback handler
POST /auth/refresh        - Refresh access token
GET  /auth/me             - Get current user info
POST /auth/logout         - Invalidate session
GET  /auth/users          - List users (admin only)
PUT  /auth/users/{id}/role - Update user role (admin only)
```

**Deliverables:**
- [ ] Working development environment (Docker Compose)
- [ ] PostgreSQL schema deployed
- [ ] Redis configured
- [ ] Auth Service with Azure OAuth integration
- [ ] CI/CD pipeline running tests

---

### 3.2 Phase 2: Core Backend (Week 3-5)

**Objective:** Build the core business logic including rule engine, MECM integration, and scan execution.

#### Week 3: MECM Connector & Data Models

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **2.1.1** | Create MECM database connector (read-only) | Backend | 1.5 |
| **2.1.2** | Implement device inventory queries | Backend | 1 |
| **2.1.3** | Implement disk space queries | Backend | 0.5 |
| **2.1.4** | Implement patch compliance queries | Backend | 0.5 |
| **2.1.5** | Implement software/application inventory queries | Backend | 1 |
| **2.1.6** | Create data aggregation layer | Backend | 1 |
| **2.1.7** | Write integration tests with test database | QA | 0.5 |

**MECM Queries to Implement:**
| Query | MECM Tables | Output |
|-------|-------------|--------|
| Device Inventory | v_R_System | Name, OS, User, Site, Last Active |
| Disk Space | v_GS_LOGICAL_DISK | Drive, Total GB, Free GB |
| Software Inventory | v_GS_INSTALLED_SOFTWARE | Name, Version, Publisher |
| Application Summary | v_GS_INSTALLED_SOFTWARE | Unique apps, install count, versions |
| Patch Compliance | v_UpdateComplianceStatus | Missing patches count |
| Collections | v_Collection, v_CollectionMembers | Collection members |
| Add/Remove Programs | v_GS_ADD_REMOVE_PROGRAMS | Installed programs |

#### Week 4: Rule Engine

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **2.2.1** | Create Rule data models (Pydantic) | Backend | 1 |
| **2.2.2** | Implement rule CRUD operations | Backend | 1 |
| **2.2.3** | Build QueryBuilder for rule → SQL conversion | Backend | 1.5 |
| **2.2.4** | Implement rule condition evaluator | Backend | 1 |
| **2.2.5** | Create rule template system | Backend | 0.5 |

**Rule Engine Components:**
```python
# Core classes to implement
class RuleDefinition(BaseModel):
    """Rule configuration with conditions and actions."""
    entity_type: EntityType  # devices, applications, or both
    
class RuleCondition(BaseModel):
    """Single condition: field, operator, value."""
    
class QueryBuilder:
    """Converts rule conditions to SQL queries for devices or applications."""
    
class RuleEvaluator:
    """Evaluates device/application data against rule conditions."""
    
class RuleTemplateManager:
    """Pre-built rule templates for devices and applications."""

class EntityType(Enum):
    DEVICES = "devices"
    APPLICATIONS = "applications"
    BOTH = "both"
```

**Pre-built Templates:**

*Device Templates:*
1. Low Disk Space Alert (< 10GB)
2. Inactive Device (> 4 weeks)
3. EOL Hardware - 1 Year Warning
4. EOL Hardware - 6 Month Critical
5. Missing Critical Patches

*Application Templates:*
6. Vulnerable Applications (CVE detected)
7. EOL Software - Upgrade Required
8. Outdated Browser Versions
9. Unauthorized Software Detection
10. License Compliance Check

#### Week 5: Scan Engine & Results

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **2.3.1** | Implement scan execution engine | Backend | 1.5 |
| **2.3.2** | Create scan results storage | Backend | 1 |
| **2.3.3** | Implement device categorization/grouping | Backend | 1 |
| **2.3.4** | Add scan scheduling (cron jobs) | Backend | 0.5 |
| **2.3.5** | Performance optimization for 100K devices | Backend | 1 |

**Core Service API Endpoints:**
```
# Rules
GET    /api/rules                    - List rules
POST   /api/rules                    - Create rule
GET    /api/rules/{id}               - Get rule details
PUT    /api/rules/{id}               - Update rule
DELETE /api/rules/{id}               - Delete rule
POST   /api/rules/{id}/execute       - Execute rule scan
GET    /api/rules/templates          - Get rule templates

# Scans
GET    /api/scans                    - List scan executions
GET    /api/scans/{id}               - Get scan details
GET    /api/scans/{id}/results       - Get scan results
GET    /api/scans/{id}/summary       - Get categorized summary
POST   /api/scans/{id}/cancel        - Cancel running scan

# Devices
GET    /api/devices                  - Search devices
GET    /api/devices/{id}             - Get device details
GET    /api/devices/{id}/history     - Get device history

# Applications
GET    /api/applications             - Search applications
GET    /api/applications/{id}        - Get application details
GET    /api/applications/{id}/devices - Devices with this app
GET    /api/applications/{id}/vulnerabilities - CVEs for this app

# App Owners
GET    /api/app-owners               - List app owners
GET    /api/app-owners/{id}/applications - Apps owned by this owner
POST   /api/app-owners/{id}/notify   - Send notification to owner
```

**Deliverables:**
- [ ] MECM connector with all required queries (devices + applications)
- [ ] Rule CRUD API with validation and entity_type support
- [ ] QueryBuilder converting rules to SQL (devices and applications)
- [ ] Scan execution engine handling 100K devices and applications
- [ ] Scan results with categorization (by device, by application, by app owner)
- [ ] 10 pre-built rule templates (5 device, 5 application)

---

### 3.3 Phase 3: Desktop App MVP (Week 5-7)

**Objective:** Create functional desktop application with core screens.

> **Note:** Phase 3 overlaps with end of Phase 2 (Week 5) as UI work can begin once API contracts are defined.

#### Week 5-6: Application Framework

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **3.1.1** | Set up PySide6 project structure | Frontend | 1 |
| **3.1.2** | Implement MVVM architecture base classes | Frontend | 1 |
| **3.1.3** | Create API client with retry logic | Frontend | 1 |
| **3.1.4** | Implement Azure OAuth browser flow | Frontend | 1.5 |
| **3.1.5** | Build main window with navigation | Frontend | 1 |
| **3.1.6** | Create reusable accessible widgets | Frontend | 1.5 |
| **3.1.7** | Implement light/dark theme support | Frontend | 1 |
| **3.1.8** | Set up local configuration storage | Frontend | 0.5 |

**Desktop Module Structure:**
```
itoa_desktop/
├── main.py
├── app.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── services/
│   ├── __init__.py
│   ├── api_client.py
│   ├── auth_service.py
│   ├── cache_service.py
│   └── config_service.py
├── viewmodels/
│   ├── __init__.py
│   ├── base_viewmodel.py
│   ├── dashboard_vm.py
│   ├── rules_vm.py
│   ├── scans_vm.py
│   └── actions_vm.py
├── views/
│   ├── __init__.py
│   ├── main_window.py
│   ├── login_dialog.py
│   ├── dashboard/
│   ├── rules/
│   ├── scans/
│   └── common/
│       ├── accessible_widgets.py
│       ├── data_table.py
│       └── loading_spinner.py
├── models/
│   ├── __init__.py
│   ├── rule.py
│   ├── device.py
│   └── action.py
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   └── formatters.py
└── resources/
    ├── styles/
    ├── icons/
    └── translations/
```

#### Week 6-7: Core Screens

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **3.2.1** | Build Dashboard view with summary cards | Frontend | 1.5 |
| **3.2.2** | Create Rules list view with CRUD | Frontend | 2 |
| **3.2.3** | Build visual Rule Builder dialog | Frontend | 2 |
| **3.2.4** | Create Scan Results view with data table | Frontend | 2 |
| **3.2.5** | Build Device Detail dialog | Frontend | 1 |
| **3.2.6** | Implement filtering and search | Frontend | 1 |
| **3.2.7** | Add CSV/Excel export functionality | Frontend | 0.5 |

**Screen Specifications:**

| Screen | Key Features |
|--------|--------------|
| **Dashboard** | Summary cards, recent activity, quick actions |
| **Rules List** | Table view, status indicators, execute button |
| **Rule Builder** | Condition builder, template selection, schedule config |
| **Scan Results** | Sortable table, filters, bulk selection, export |
| **Device Detail** | Hardware info, software list, scan history |

**Deliverables:**
- [ ] Desktop app with Azure OAuth login
- [ ] Dashboard with live metrics
- [ ] Rules management (CRUD + templates)
- [ ] Visual rule builder
- [ ] Scan results view with filtering
- [ ] Device detail dialog
- [ ] Light/dark theme support

---

### 3.4 Phase 4: LLM Integration (Week 7-9)

**Objective:** Add AI-powered features including suggestions and natural language processing.

#### Week 7-8: LLM Service

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **4.1.1** | Create LLM provider abstraction (LangChain) | Backend | 1 |
| **4.1.2** | Implement OpenAI provider | Backend | 1 |
| **4.1.3** | Implement Azure OpenAI provider | Backend | 0.5 |
| **4.1.4** | Implement local QWEN provider | Backend | 1.5 |
| **4.1.5** | Build SensitiveDataFilter | Backend | 1.5 |
| **4.1.6** | Create prompt templates | Backend | 1 |
| **4.1.7** | Implement response validation | Backend | 0.5 |
| **4.1.8** | Add LLM configuration endpoints | Backend | 0.5 |

**LLM Providers:**
```python
# Provider abstraction
class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self) -> BaseLLM: ...
    @abstractmethod
    def is_available(self) -> bool: ...

# Implementations
class OpenAIProvider(LLMProvider): ...
class AzureOpenAIProvider(LLMProvider): ...
class QWENProvider(LLMProvider): ...
```

**Sensitive Data Filter Rules:**
| Pattern | Replacement | Example |
|---------|-------------|---------|
| Email addresses | USER_{n}_EMAIL | john@co.com → USER_1_EMAIL |
| IP addresses | IP_{n}_ADDR | 192.168.1.1 → IP_1_ADDR |
| Hostnames | DEVICE_{n} | WS-NYC-12345 → DEVICE_1 |
| Serial numbers | SERIAL_{n} | ABC123XYZ → SERIAL_1 |

#### Week 8-9: AI Features & Ground Truth Testing

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **4.2.1** | Implement NL rule interpretation | Backend | 2 |
| **4.2.2** | Build remediation suggestion generator | Backend | 2 |
| **4.2.3** | Create issue explanation generator | Backend | 1 |
| **4.2.4** | Integrate AI features into Desktop app | Frontend | 2 |
| **4.2.5** | Add AI suggestion UI panel | Frontend | 1 |
| **4.2.6** | Test with various prompts and edge cases | QA | 1 |
| **4.2.7** | Create ground truth test framework | Backend | 1 |
| **4.2.8** | Build manual test case library (100+ cases) | QA | 2 |
| **4.2.9** | Implement LLM-assisted evaluation | Backend | 1 |
| **4.2.10** | Integrate ground truth tests into CI/CD | DevOps | 0.5 |

**Ground Truth Test Categories:**
| Category | Min Cases | Accuracy Target |
|----------|-----------|----------------|
| NL Parsing | 40 | > 90% |
| Action Recommendations | 30 | > 85% |
| Risk Classification | 25 | > 95% |
| Summarization | 20 | > 80% |

**LLM Service API Endpoints:**
```
POST /api/llm/interpret-rule       - NL to structured rule
POST /api/llm/suggest-remediation  - Get action suggestions
POST /api/llm/explain-issue        - Explain device issue
GET  /api/llm/providers            - List available providers
PUT  /api/llm/config               - Update LLM configuration
```

**Prompt Templates:**
1. **Rule Interpretation:** Convert natural language to RuleDefinition JSON
2. **Remediation Suggestion:** Analyze devices and suggest grouped actions
3. **Issue Explanation:** Plain-language explanation of why device was flagged

**Deliverables:**
- [ ] LLM Service with provider switching
- [ ] OpenAI and QWEN providers working
- [ ] Sensitive data filtering (no PII to LLM)
- [ ] Natural language rule creation in UI
- [ ] AI suggestions panel in scan results
- [ ] Issue explanations in device details
- [ ] Ground truth test framework with 100+ test cases
- [ ] LLM-assisted semantic evaluation
- [ ] Ground truth tests integrated into CI/CD pipeline
- [ ] Baseline accuracy metrics established

---

### 3.5 Phase 5: Actions & Integrations (Week 9-12)

**Objective:** Complete external integrations and action execution workflow.

#### Week 9-10: External Connectors

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **5.1.1** | Implement ServiceNow CMDB connector | Backend | 1.5 |
| **5.1.2** | Implement ServiceNow incident creation | Backend | 1 |
| **5.1.3** | Implement ServiceNow EOL table queries | Backend | 1 |
| **5.1.4** | Implement ServiceNow App Owner lookup | Backend | 0.5 |
| **5.1.5** | Implement 1E Tachyon connector | Backend | 1.5 |
| **5.1.6** | Create Tachyon instruction execution | Backend | 1.5 |
| **5.1.7** | Implement vulnerability database connector (NVD/CVE) | Backend | 1 |
| **5.1.8** | Build notification service (Email/Teams) | Backend | 1.5 |
| **5.1.9** | Integration tests with external systems | QA | 2 |

**Vulnerability Database Integration:**
| Source | Data | Usage |
|--------|------|-------|
| NVD (NIST) | CVE data, CVSS scores | Application vulnerability lookup |
| Vendor Advisories | Security bulletins | EOL and patch information |
| Internal Vuln DB | Custom tracking | Organization-specific vulnerabilities |

**ServiceNow Integration:**
| Endpoint | Purpose |
|----------|---------|
| GET /table/cmdb_ci_computer | CMDB records |
| GET /table/u_eol_table | EOL dates |
| POST /table/incident | Create incidents |
| GET /table/sys_user_group | Assignment groups |

**1E Tachyon Integration:**
| Endpoint | Purpose |
|----------|---------|
| POST /Consumer/Instructions | Execute instruction |
| GET /Consumer/Responses | Get results |
| GET /Inventory/Devices | Device lookup |

**Pre-configured Tachyon Instructions:**
- Disk cleanup script
- Get real-time disk space
- Restart service
- Check patch status

#### Week 10-11: Action Worker

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **5.2.1** | Set up Celery worker with Redis | Backend | 1 |
| **5.2.2** | Implement base ActionTask class | Backend | 1 |
| **5.2.3** | Create MECM collection task | Backend | 1 |
| **5.2.4** | Create MECM deployment task | Backend | 1 |
| **5.2.5** | Create ServiceNow incident task | Backend | 1 |
| **5.2.6** | Create notification task | Backend | 1 |
| **5.2.7** | Create Tachyon instruction task | Backend | 1 |
| **5.2.8** | Implement retry and failure handling | Backend | 1 |

**Action Types:**
| Action | Target System | Task Class |
|--------|---------------|------------|
| Create Collection | MECM | CreateCollectionTask |
| Create Deployment | MECM | CreateDeploymentTask |
| Create Incident | ServiceNow | CreateIncidentTask |
| Send Notification | Email/Teams | SendNotificationTask |
| Notify App Owner | Email/Teams | AppOwnerNotificationTask |
| Bulk App Owner Report | Email | BulkAppOwnerReportTask |
| Run Tachyon Instruction | 1E Tachyon | TachyonInstructionTask |
| Create Vulnerability Ticket | ServiceNow | VulnerabilityTicketTask |

#### Week 11-12: Approval Workflow

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **5.3.1** | Create action request data model | Backend | 0.5 |
| **5.3.2** | Implement action request endpoints | Backend | 1.5 |
| **5.3.3** | Build approval workflow state machine | Backend | 1.5 |
| **5.3.4** | Implement approval notification | Backend | 1 |
| **5.3.5** | Create Actions UI view | Frontend | 2 |
| **5.3.6** | Build approval dialog with device preview | Frontend | 1.5 |
| **5.3.7** | Add action status tracking | Frontend | 1 |
| **5.3.8** | Implement bulk action creation | Frontend | 1 |

**Approval Workflow States:**
```
┌─────────┐     ┌─────────────────┐     ┌──────────┐
│  Draft  │────►│ Pending Approval│────►│ Approved │
└─────────┘     └─────────────────┘     └────┬─────┘
                        │                    │
                        ▼                    ▼
                ┌──────────┐          ┌───────────┐
                │ Rejected │          │ Executing │
                └──────────┘          └─────┬─────┘
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                       ┌───────────┐ ┌───────────┐ ┌───────────┐
                       │ Completed │ │  Failed   │ │ Cancelled │
                       └───────────┘ └───────────┘ └───────────┘
```

**Actions API Endpoints:**
```
GET    /api/actions              - List action requests
POST   /api/actions              - Create action request
GET    /api/actions/{id}         - Get action details
POST   /api/actions/{id}/approve - Approve action
POST   /api/actions/{id}/reject  - Reject action
POST   /api/actions/{id}/cancel  - Cancel action
GET    /api/actions/pending      - Get pending approvals
```

**Deliverables:**
- [ ] ServiceNow connector (CMDB, incidents, EOL, App Owners)
- [ ] 1E Tachyon connector with instruction execution
- [ ] Vulnerability database connector (NVD/CVE)
- [ ] Notification service (Email + Teams)
- [ ] App Owner notification workflow
- [ ] Celery action worker with all task types (including App Owner tasks)
- [ ] Complete approval workflow
- [ ] Actions UI with approval dialog
- [ ] Bulk action support
- [ ] Vulnerability ticket creation

---

### 3.6 Phase 6: Polish & Compliance (Week 12-14)

**Objective:** Ensure production readiness with accessibility compliance, testing, and documentation.

#### Week 12-13: Accessibility & UI Polish

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **6.1.1** | WCAG 2.1 AA audit of all screens | QA | 2 |
| **6.1.2** | Implement keyboard navigation | Frontend | 1.5 |
| **6.1.3** | Add screen reader support (ARIA) | Frontend | 1.5 |
| **6.1.4** | Verify color contrast ratios | Frontend | 0.5 |
| **6.1.5** | Add focus indicators | Frontend | 0.5 |
| **6.1.6** | Implement 200% zoom support | Frontend | 0.5 |
| **6.1.7** | Create Reports module | Frontend/Backend | 2 |
| **6.1.8** | Build bulk operations UI | Frontend | 1.5 |

**WCAG 2.1 AA Checklist:**
- [ ] All functionality keyboard accessible
- [ ] Focus visible on all interactive elements
- [ ] Color contrast ≥ 4.5:1 (text), ≥ 3:1 (UI)
- [ ] Text resizable to 200%
- [ ] Screen reader compatibility
- [ ] Error messages clearly identified
- [ ] Form labels properly associated

**Reports to Implement:**
| Report | Schedule | Content |
|--------|----------|---------|
| Daily Summary | Daily 8 AM | Actions taken, pending approvals |
| Weekly Compliance | Monday | Device compliance by category |
| Monthly Trends | 1st of month | Issue trends, resolution rates |
| Audit Report | On-demand | User actions, approvals, changes |
| EOL Forecast | Monthly | Upcoming EOL devices |

#### Week 13-14: Testing & Documentation

| Task | Description | Owner | Days |
|------|-------------|-------|------|
| **6.2.1** | Performance testing (100K devices + applications) | QA | 2 |
| **6.2.2** | Load testing (5 concurrent users) | QA | 1 |
| **6.2.3** | Security testing (OWASP) | Security | 2 |
| **6.2.4** | End-to-end test suite | QA | 2 |
| **6.2.5** | Ground truth regression testing (all categories) | QA | 1 |
| **6.2.6** | Create user documentation | Tech Writer | 2 |
| **6.2.7** | Create admin guide | Tech Writer | 1 |
| **6.2.8** | Production deployment preparation | DevOps | 2 |
| **6.2.9** | Final bug fixes and polish | All | 2 |

**Ground Truth Quality Gates (Pre-Release):**
| Category | Minimum Accuracy | Status |
|----------|------------------|--------|
| NL Parsing | 90% | ⬜ Pending |
| Action Recommendations | 85% | ⬜ Pending |
| Risk Classification | 95% | ⬜ Pending |
| Summarization | 80% | ⬜ Pending |

**Performance Targets:**
| Metric | Target | Test Scenario |
|--------|--------|---------------|
| Rule execution | < 5 min | 100K devices, complex rule |
| UI response | < 2 sec | Any user action |
| LLM suggestion | < 30 sec | 500 devices context |
| Scan results load | < 3 sec | 10K results with pagination |
| Action execution | < 2 min | 500 device collection |

**Documentation Deliverables:**
- User Guide (Operations staff)
- Administrator Guide (System configuration)
- API Reference (Developer documentation)
- Deployment Guide (Infrastructure team)
- Troubleshooting Guide

**Deliverables:**
- [ ] WCAG 2.1 AA compliance verified
- [ ] All reports functional
- [ ] Bulk operations UI complete
- [ ] Performance targets met
- [ ] Security audit passed
- [ ] E2E test suite (>80% coverage)
- [ ] User documentation complete
- [ ] Production deployment ready

---

## 4. Resource Requirements

### 4.1 Team Structure

| Role | Count | Responsibilities |
|------|-------|------------------|
| **Backend Developer** | 2 | Services, connectors, APIs |
| **Frontend Developer** | 1 | Desktop app, UI/UX |
| **DevOps Engineer** | 0.5 | Infrastructure, CI/CD, deployment |
| **QA Engineer** | 1 | Testing, accessibility audit |
| **Tech Writer** | 0.5 | Documentation (Phase 6) |
| **Project Manager** | 0.5 | Coordination, stakeholder management |

### 4.2 Infrastructure Requirements

| Resource | Specification | Purpose |
|----------|---------------|---------|
| **Development** | | |
| Dev Workstations | 16GB RAM, SSD | Development |
| Dev Kubernetes | 3 nodes, 4 CPU each | Local testing |
| **Staging** | | |
| OpenShift Staging | 3 nodes, 8 CPU, 16GB | Integration testing |
| PostgreSQL | 2 vCPU, 8GB RAM | Staging database |
| Redis | 2 vCPU, 4GB RAM | Staging cache |
| **Production** | | |
| OpenShift Production | 5 nodes, 8 CPU, 32GB | Production workloads |
| PostgreSQL HA | 4 vCPU, 16GB RAM (x2) | Production database |
| Redis Cluster | 2 vCPU, 8GB RAM (x3) | Production cache |

### 4.3 External Services

| Service | Purpose | Access Required |
|---------|---------|-----------------|
| MECM Database | Device & application data | Read-only SQL access |
| ServiceNow | CMDB, incidents, App Owners | API credentials |
| 1E Tachyon | Real-time actions | API token |
| Azure AD | Authentication | App registration |
| OpenAI API | LLM (optional) | API key |
| NVD (NIST) | CVE/Vulnerability data | API key (free) |
| GPT-4 API | Ground truth evaluation | API key (for semantic eval) |

---

## 5. Risk Management

### 5.1 Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R1 | MECM database schema changes | Medium | High | Document expected schema, add version checks |
| R2 | External API rate limits | Medium | Medium | Implement request queuing, caching |
| R3 | LLM response quality inconsistent | Medium | Medium | Validate responses, fallback to templates |
| R4 | Performance issues at scale | Low | High | Early load testing, query optimization |
| R5 | Azure AD integration complexity | Medium | Medium | Use MSAL library, early testing |
| R6 | WCAG compliance gaps | Low | Medium | Accessibility audit early, use Qt accessibility |
| R7 | Team availability | Low | Medium | Cross-training, documentation |
| R8 | Scope creep | Medium | Medium | Strict change control, phase-gated delivery |

### 5.2 Contingency Plans

| Risk | Contingency |
|------|-------------|
| R1 | Abstract database layer, support schema versioning |
| R2 | Implement exponential backoff, request prioritization |
| R3 | Human review option, quality feedback loop |
| R4 | Horizontal scaling, database indexing, query profiling |
| R5 | Fallback to service principal auth |
| R6 | Dedicated accessibility sprint if needed |

---

## 6. Dependencies

### 6.1 External Dependencies

| Dependency | Required By | Status |
|------------|-------------|--------|
| Azure AD App Registration | Phase 1 (Week 2) | ⬜ Pending |
| MECM Database Access | Phase 2 (Week 3) | ⬜ Pending |
| ServiceNow API Credentials | Phase 5 (Week 9) | ⬜ Pending |
| 1E Tachyon API Access | Phase 5 (Week 9) | ⬜ Pending |
| OpenShift Staging Cluster | Phase 2 (Week 4) | ⬜ Pending |
| OpenAI API Key (optional) | Phase 4 (Week 7) | ⬜ Pending |
| NVD API Access | Phase 5 (Week 9) | ⬜ Pending |
| Ground Truth Test Data (100+ cases) | Phase 4 (Week 8) | ⬜ Pending |

### 6.2 Internal Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3
   │           │           │
   │           └─────┬─────┘
   │                 ▼
   │           Phase 4 ──► Phase 5 ──► Phase 6
   │              │           │
   └──────────────┴───────────┘
         (Auth required for all)
```

---

## 7. Milestones & Deliverables

### 7.1 Milestone Schedule

| Milestone | Target Date | Deliverables |
|-----------|-------------|--------------|
| **M1: Foundation Complete** | Week 2 | Infrastructure, Auth Service |
| **M2: Core Backend Ready** | Week 5 | Rule Engine, MECM Integration, Scanning |
| **M3: Desktop MVP** | Week 7 | Desktop App with Core Screens |
| **M4: AI Features Live** | Week 9 | LLM Service, NL Rules, Suggestions |
| **M5: Full Integration** | Week 12 | All Connectors, Action Execution |
| **M6: Production Ready** | Week 14 | Tested, Documented, Deployed |

### 7.2 Demo Schedule

| Demo | Week | Audience | Content |
|------|------|----------|---------|
| **Demo 1** | 2 | Dev Team | Auth flow, infrastructure |
| **Demo 2** | 5 | Stakeholders | Rule creation, scan execution |
| **Demo 3** | 7 | Users | Desktop app walkthrough |
| **Demo 4** | 9 | Stakeholders | AI features demonstration |
| **Demo 5** | 12 | Users | Full workflow with actions |
| **Demo 6** | 14 | All | Production readiness review |

---

## 8. Success Criteria

### 8.1 Acceptance Criteria

| Criteria | Metric | Target |
|----------|--------|--------|
| **Functionality** | Features complete | 100% of High priority |
| **Performance** | Rule execution time | < 5 minutes (100K devices) |
| **Performance** | UI response time | < 2 seconds |
| **Reliability** | Action success rate | > 95% |
| **Security** | Vulnerability scan | No critical/high issues |
| **Accessibility** | WCAG compliance | AA level |
| **Quality** | Test coverage | > 80% |
| **Quality** | Bug escape rate | < 5% to production |
| **AI Accuracy** | NL Parsing | > 90% |
| **AI Accuracy** | Action Recommendations | > 85% |
| **AI Accuracy** | Risk Classification | > 95% |
| **AI Accuracy** | Summarization | > 80% |

### 8.2 Definition of Done

**Feature Level:**
- [ ] Code complete and reviewed
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Accessibility verified
- [ ] Security review passed

**Phase Level:**
- [ ] All features in phase complete
- [ ] Demo delivered to stakeholders
- [ ] No critical bugs open
- [ ] Performance targets met
- [ ] Deployed to staging environment

**Release Level:**
- [ ] All phases complete
- [ ] User acceptance testing passed
- [ ] Production deployment successful
- [ ] User documentation delivered
- [ ] Operations team trained

---

## Appendix A: Sprint Breakdown

### Sprint 1 (Week 1-2): Foundation
- US-001: Project setup and repository structure
- US-002: Development environment configuration
- US-003: PostgreSQL schema creation
- US-004: Auth Service with Azure OAuth

### Sprint 2 (Week 3-4): Core Backend I
- US-005: MECM database connector
- US-006: Device inventory queries
- US-007: Rule data models
- US-008: Rule CRUD operations

### Sprint 3 (Week 5-6): Core Backend II + Desktop Start
- US-009: QueryBuilder implementation (devices + applications)
- US-010: Scan execution engine (devices + applications)
- US-011: Desktop app framework
- US-012: API client and auth integration

### Sprint 4 (Week 7-8): Desktop + LLM Start
- US-013: Dashboard view
- US-014: Rules management UI (with entity type support)
- US-015: Scan results view (devices + applications tabs)
- US-016: LLM provider abstraction
- US-017: Ground truth test framework setup

### Sprint 5 (Week 9-10): LLM + Integrations
- US-018: NL rule interpretation
- US-019: Remediation suggestions
- US-020: Ground truth test cases (100+ cases)
- US-021: ServiceNow connector (including App Owner lookup)
- US-022: 1E Tachyon connector
- US-023: Vulnerability database connector

### Sprint 6 (Week 11-12): Actions
- US-024: Celery action worker
- US-025: Approval workflow
- US-026: Actions UI
- US-027: Notification service (including App Owner notifications)
- US-028: Vulnerability ticket creation

### Sprint 7 (Week 13-14): Polish
- US-029: WCAG compliance
- US-030: Reports module
- US-031: Performance testing
- US-032: Ground truth regression testing
- US-033: Documentation

---

## Appendix B: Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Desktop Framework | PySide6 (Qt) | Best accessibility support, native look |
| API Framework | FastAPI | Async support, automatic OpenAPI docs |
| Database | PostgreSQL | JSON support, reliability, enterprise-ready |
| LLM Abstraction | LangChain | Provider-agnostic, active community |
| Task Queue | Celery + Redis | Mature, reliable, good monitoring |
| Container | Docker + K8s | OpenShift requirement, scalability |
| Testing Framework | pytest | Flexible, good fixtures, CI integration |
| Ground Truth Eval | GPT-4 | Semantic evaluation capability |
| Vulnerability Data | NVD/NIST | Free, comprehensive CVE database |

---

## Appendix C: Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 31, 2026 | IT Ops Team | Initial version || 1.1 | Jan 31, 2026 | IT Ops Team | Added Application Management, Ground Truth Testing, Vulnerability DB |

---

## Appendix D: Referenced Documents

| Document | Location | Description |
|----------|----------|-------------|
| Requirements Document | [01_Requirements_Document.md](01_Requirements_Document.md) | Full functional and non-functional requirements |
| Design Document | [02_Design_Document.md](02_Design_Document.md) | Architecture and technical design |
| Ground Truth Testing Plan | [testing/Ground_Truth_Testing_Plan.md](testing/Ground_Truth_Testing_Plan.md) | Detailed AI validation approach |
| Ground Truth Requirements | [testing/Ground_Truth_Requirements.md](testing/Ground_Truth_Requirements.md) | Testing requirements (GTR-001 to GTR-005) |
| Executive Summary | [Executive_Summary.md](Executive_Summary.md) | High-level product overview |
---

*End of Implementation Plan*
