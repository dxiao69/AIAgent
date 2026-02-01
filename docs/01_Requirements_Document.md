# IT Operations AI Agent - Software Requirements Specification (SRS)

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Project Name:** IT Operations AI Agent (ITOA Agent)  
**Author:** IT Operations Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Testing Requirements](#5-testing-requirements)
6. [Data Requirements](#6-data-requirements)
7. [User Interface Requirements](#7-user-interface-requirements)
8. [Security Requirements](#8-security-requirements)
9. [Compliance Requirements](#9-compliance-requirements)
10. [Appendices](#10-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document defines the software requirements for the IT Operations AI Agent (ITOA Agent), an intelligent automation system designed to identify IT infrastructure issues, provide AI-powered remediation suggestions, and execute approved actions across enterprise systems.

### 1.2 Scope

The ITOA Agent will:
- Allow operations staff to define rules for identifying problematic devices and applications
- Automatically scan and identify devices and applications matching defined criteria
- Leverage LLM (Large Language Models) to suggest remediation actions
- Execute approved remediation actions across multiple IT systems
- Provide summarized views for bulk operations
- Enable app owners to address vulnerabilities in their applications

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| MECM | Microsoft Endpoint Configuration Manager |
| SNOW | ServiceNow |
| EOL | End of Life |
| EOS | End of Support |
| LLM | Large Language Model |
| CMDB | Configuration Management Database |
| 1E Tachyon | Real-time endpoint management platform |
| WCAG | Web Content Accessibility Guidelines |
| CVE | Common Vulnerabilities and Exposures |
| App Owner | Person/team responsible for an application |

### 1.4 Target Users

- **Primary Users:** IT Operations Team (< 5 concurrent users)
- **Approvers:** Designated personnel with approval role
- **Administrators:** System configuration and rule management

---

## 2. Overall Description

### 2.1 Product Perspective

The ITOA Agent is a standalone desktop application that integrates with existing IT infrastructure:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ITOA Agent                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Rule Engine │  │  LLM Engine │  │  Action Executor        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                  │                      │
         ▼                  ▼                      ▼
┌─────────────┐    ┌──────────────┐    ┌────────────────────────┐
│  MECM DB    │    │ OpenAI/QWEN  │    │  ServiceNow API        │
│  (Backup)   │    │    LLM       │    │  1E Tachyon API        │
└─────────────┘    └──────────────┘    └────────────────────────┘
```

### 2.2 Product Features Summary

| Feature ID | Feature Name | Priority |
|------------|--------------|----------|
| F-001 | Rule Definition & Management | High |
| F-002 | Device Identification & Scanning | High |
| F-002A | Application Identification & Scanning | High |
| F-003 | LLM-Powered Suggestions | High |
| F-004 | Action Execution with Approval | High |
| F-005 | Bulk Operation Summarization | Medium |
| F-006 | Natural Language Rule Creation | Medium |
| F-007 | Audit & Reporting | Medium |

### 2.3 User Classes and Characteristics

| User Class | Description | Permissions |
|------------|-------------|-------------|
| Operator | Day-to-day operations, runs scans, reviews suggestions | View, Execute (pending approval) |
| Approver | Reviews and approves/rejects proposed actions | View, Approve, Reject |
| Administrator | Configures system, manages rules, users | Full access |

### 2.4 Operating Environment

- **Platform:** Kubernetes (OpenShift)
- **Client:** Python Desktop Application
- **Database:** PostgreSQL (application data), MECM SQL Server (read-only)
- **Authentication:** Azure OAuth 2.0
- **Scale:** 100,000 managed devices

### 2.5 Constraints

- MECM database is a backup copy (not real-time)
- Sensitive data must be filtered before LLM processing
- All destructive actions require human approval
- WCAG 2.1 AA compliance required

---

## 3. Functional Requirements

### 3.1 Rule Definition & Management (F-001)

#### FR-001.1: Create Rule
**Description:** Users shall be able to create rules to identify target devices or applications.

**Acceptance Criteria:**
- User can define rule name and description
- User can select Entity Type: Devices, Applications, or Both
- User can specify conditions using a visual builder OR natural language
- User can set rule schedule (manual, daily, weekly)
- User can assign rule category (Disk Space, EOL, Vulnerability, Compliance, Software Update)
- System validates rule syntax before saving

**Entity Types:**
| Entity Type | Description | Use Case |
|-------------|-------------|----------|
| Devices | Target computer/workstation assets | Hardware issues, disk space, inactivity |
| Applications | Target installed software | Version updates, vulnerabilities, EOL software |
| Both | Combined device and application criteria | Devices running specific vulnerable software |

**Rule Condition Components:**
| Component | Type | Example |
|-----------|------|---------|
| Entity Type | Dropdown | Devices, Applications, Both |
| Field | Dropdown | Disk Free Space, Last Active Date, EOL Date, App Version, CVE Count |
| Operator | Dropdown | <, >, =, <=, >=, contains, within |
| Value | Input | 10 GB, 4 weeks, 1 year |
| Logical Operator | Dropdown | AND, OR |

#### FR-001.2: Natural Language Rule Creation
**Description:** Users shall be able to describe rules in natural language, and LLM will convert to structured rule.

**Acceptance Criteria:**
- User can type: "Find devices with less than 10GB disk space that haven't been active in 4 weeks"
- LLM interprets and generates structured rule
- User reviews and confirms generated rule
- System shows confidence score for interpretation

#### FR-001.3: Edit Rule
**Description:** Users shall be able to modify existing rules.

**Acceptance Criteria:**
- All rule properties can be edited
- Edit history is maintained
- Active rules can be disabled without deletion

#### FR-001.4: Delete Rule
**Description:** Users shall be able to delete rules with confirmation.

**Acceptance Criteria:**
- Soft delete (archive) by default
- Hard delete requires administrator role
- Associated historical data is retained

#### FR-001.5: Rule Templates
**Description:** System shall provide pre-built rule templates for common scenarios.

**Pre-built Templates:**
| Template Name | Entity Type | Condition | Default Action |
|---------------|-------------|-----------|----------------|
| Low Disk Space Alert | Devices | Disk Free < 10GB | Send Notification |
| Inactive Device | Devices | Last Active > 4 weeks | Send Notification |
| EOL Hardware (1 Year) | Devices | EOL Date within 365 days | Notify Hardware Team |
| EOL Hardware (6 Months) | Devices | EOL Date within 180 days | Create Incident |
| Missing Critical Patches | Devices | Critical Patches Missing > 0 | Create Patch Deployment |
| Vulnerable Applications | Applications | CVE Count > 0 | Notify App Owner |
| Outdated Java | Applications | App Name = "Java" AND Version < 17 | Notify App Owner |
| EOL Software | Applications | App EOL Date < Today | Create Incident |
| Unsupported Browser | Applications | App Name contains "Chrome" AND Version < 120 | Send Notification |
| Adobe Reader Update | Applications | App Name = "Adobe Reader" AND Version < 2024 | Notify App Owner |

---

### 3.2 Device Identification & Scanning (F-002)

#### FR-002.1: Execute Rule Scan
**Description:** Users shall be able to execute rules to identify matching devices.

**Acceptance Criteria:**
- Manual execution on-demand
- Scheduled execution (configurable)
- Progress indicator during scan
- Scan can be cancelled
- Results cached for review

#### FR-002.2: View Scan Results
**Description:** Users shall be able to view devices identified by rule execution.

**Acceptance Criteria:**
- List view with sortable columns
- Filter by rule, category, severity
- Search by device name, user, location
- Export to CSV/Excel
- Pagination for large result sets

**Result Fields:**
| Field | Source | Description |
|-------|--------|-------------|
| Device Name | MECM | Computer hostname |
| Primary User | MECM | Assigned user |
| Department | CMDB | Organizational unit |
| Location | CMDB | Physical location |
| Triggered Rules | Agent | Rules that matched |
| Risk Score | Agent | Calculated priority |
| Last Scan Date | Agent | When device was evaluated |

#### FR-002.3: Device Detail View
**Description:** Users shall be able to view detailed information for any identified device.

**Acceptance Criteria:**
- Hardware specifications (from MECM)
- Installed software list (from MECM)
- Compliance status (from MECM)
- CMDB record link
- EOL/EOS dates (from ServiceNow)
- Historical scan results
- Previous actions taken

#### FR-002.4: Bulk Categorization
**Description:** System shall automatically group identified devices by common attributes.

**Grouping Options:**
- By Department
- By Location
- By Issue Type
- By Hardware Model
- By Operating System
- By Application

---

### 3.2A Application Identification & Scanning (F-002A)

#### FR-002A.1: Execute Application Rule Scan
**Description:** Users shall be able to execute rules to identify applications matching criteria.

**Acceptance Criteria:**
- Manual execution on-demand
- Scheduled execution (configurable)
- Progress indicator during scan
- Scan can be cancelled
- Results grouped by application or by device
- Results cached for review

#### FR-002A.2: View Application Scan Results
**Description:** Users shall be able to view applications identified by rule execution.

**Acceptance Criteria:**
- Tabbed view: Applications view / Devices view
- Applications view shows unique apps with installation count
- Devices view shows devices with the flagged applications
- Filter by app name, vendor, version, severity
- Group by App Owner
- Export to CSV/Excel
- Pagination for large result sets

**Application Result Fields:**
| Field | Source | Description |
|-------|--------|-------------|
| Application Name | MECM | Software display name |
| Version | MECM | Installed version |
| Vendor | MECM | Software publisher |
| Installation Count | MECM | Number of devices with this app |
| App Owner | CMDB | Responsible person/team |
| CVE Count | Vulnerability DB | Known vulnerabilities |
| EOL Date | Vendor/CMDB | End of life date |
| Risk Score | Agent | Calculated priority |
| Latest Version | Vendor | Current available version |

#### FR-002A.3: Application Detail View
**Description:** Users shall be able to view detailed information for any identified application.

**Acceptance Criteria:**
- Application metadata (name, vendor, version)
- CVE/vulnerability list (if applicable)
- All devices with this application installed
- App Owner contact information
- Upgrade path recommendations
- Historical scan results
- Previous actions taken

#### FR-002A.4: App Owner Grouping
**Description:** System shall group applications by App Owner for notification purposes.

**Acceptance Criteria:**
- Automatically identify App Owner from CMDB
- Group all flagged applications by owner
- Calculate total device impact per owner
- Generate summary for bulk notification
- Support manual App Owner assignment

**Example Output:**
```
App Owner: Sarah Wilson (sarah.wilson@company.com)
Applications Requiring Attention:
  - Java 8 (EOL) - 245 devices
  - Adobe Reader 2020 (Outdated) - 156 devices  
  - Chrome 118 (Security Update) - 89 devices
Total Impact: 490 devices (some overlap)
```

#### FR-002A.5: Application Vulnerability Tracking
**Description:** System shall track known vulnerabilities for identified applications.

**Acceptance Criteria:**
- Integration with vulnerability database (CVE)
- Display CVE ID, severity, description
- Link to remediation guidance
- Track vulnerability age
- Priority based on CVSS score

**Vulnerability Fields:**
| Field | Description |
|-------|-------------|
| CVE ID | Common Vulnerabilities and Exposures identifier |
| CVSS Score | Severity score (0-10) |
| Severity | Critical, High, Medium, Low |
| Published Date | When vulnerability was disclosed |
| Affected Versions | Version range with vulnerability |
| Remediation | Upgrade path or workaround |

---

### 3.3 LLM-Powered Suggestions (F-003)

#### FR-003.1: Generate Remediation Suggestions
**Description:** System shall use LLM to generate contextual remediation suggestions.

**Acceptance Criteria:**
- LLM analyzes device context and rule violations
- Generates ranked list of suggested actions
- Provides reasoning for each suggestion
- Estimates impact and effort
- Supports both external (OpenAI) and local (QWEN) LLMs

#### FR-003.2: Configurable LLM Provider
**Description:** Administrators shall be able to configure LLM provider.

**Configuration Options:**
| Setting | Options | Description |
|---------|---------|-------------|
| Provider | OpenAI, Azure OpenAI, Local QWEN | LLM service to use |
| Model | gpt-4, gpt-3.5-turbo, qwen-7b, etc. | Specific model |
| API Endpoint | URL | For external providers |
| API Key | Secret | Authentication (encrypted) |
| Temperature | 0.0 - 1.0 | Response creativity |
| Max Tokens | Integer | Response length limit |

#### FR-003.3: Sensitive Data Filtering
**Description:** System shall filter sensitive data before sending to LLM.

**Filtered Data Types:**
- User personal information (names replaced with pseudonyms)
- IP addresses (masked)
- Specific hostnames (generalized)
- Credentials (never included)
- Serial numbers (masked)

**Filtering Rules:**
```
Original: "User John.Smith@company.com on device WS-NYC-12345"
Filtered: "User USER_001 on device WORKSTATION_001"
```

#### FR-003.4: Explain Device Issues
**Description:** LLM shall provide plain-language explanations of why devices were flagged.

**Acceptance Criteria:**
- Clear, non-technical explanation
- Impact assessment
- Priority recommendation
- Similar past incidents (if available)

---

### 3.4 Action Execution with Approval (F-004)

#### FR-004.1: Available Actions
**Description:** System shall support the following remediation actions.

| Action ID | Action Name | Target System | Description |
|-----------|-------------|---------------|-------------|
| A-001 | Install Patch | MECM/1E Tachyon | Deploy patches to devices |
| A-002 | Create Incident | ServiceNow | Create incident ticket |
| A-003 | Send User Notification | Email/Teams | Notify end user |
| A-004 | Send Owner Notification | Email/Teams | Notify application owner |
| A-005 | Create Collection | MECM | Create device collection |
| A-006 | Create Deployment | MECM | Create software deployment |
| A-007 | Run Tachyon Instruction | 1E Tachyon | Execute real-time action |

#### FR-004.2: Action Request Creation
**Description:** Users shall be able to create action requests for identified devices.

**Acceptance Criteria:**
- Select single or multiple devices
- Choose action type
- Add notes/justification
- Set priority level
- Submit for approval

#### FR-004.3: Approval Workflow
**Description:** All actions shall require approval before execution.

**Workflow States:**
```
[Draft] → [Pending Approval] → [Approved] → [Executing] → [Completed]
                            ↘ [Rejected] → [Archived]
                            ↘ [Approved] → [Failed] → [Retry/Archive]
```

**Approval Requirements:**
- Single approver required (from approver role)
- Approver cannot be requestor (for non-admin)
- Approval expires after 7 days (configurable)
- Approver must provide comments for rejection

#### FR-004.4: Bulk Action Support
**Description:** Users shall be able to apply actions to multiple devices.

**Acceptance Criteria:**
- Select multiple devices from scan results
- Apply same action to all selected
- System groups devices intelligently
- Single approval for bulk action
- Individual device status tracking

#### FR-004.5: Action Execution
**Description:** Approved actions shall be executed automatically.

**Acceptance Criteria:**
- Execution starts within 5 minutes of approval
- Real-time progress tracking
- Error handling with retry option
- Notification on completion/failure
- Full audit trail

#### FR-004.6: Action Testing (Sandbox Mode)
**Description:** Users shall be able to test actions in a sandbox environment before using them in production.

**Acceptance Criteria:**
- Every action must be testable before production use
- Test mode executes against sandbox/test environment
- Test results clearly show what WOULD happen without actual execution
- Dry-run mode available for all action types
- Test execution logs captured for review
- Validation errors clearly reported
- Actions cannot be used in production rules until successfully tested

**Test Modes by Action Type:**
| Action Type | Test Mode Behavior |
|-------------|-------------------|
| Send Notification | Sends to test email/requestor only |
| Create MECM Collection | Shows preview, no actual creation |
| Create Deployment | Validates parameters, shows target preview |
| ServiceNow Incident | Creates in test instance or preview mode |
| 1E Tachyon Action | Validates instruction, shows target devices |

**Test Validation Checklist:**
- [ ] API connectivity verified
- [ ] Authentication successful
- [ ] Parameters validated
- [ ] Target system accessible
- [ ] Sample execution successful
- [ ] Rollback capability confirmed (if applicable)

#### FR-004.7: Action Definition Management
**Description:** Administrators shall be able to define and manage available actions.

**Action Definition Properties:**
| Property | Description |
|----------|-------------|
| Action ID | Unique identifier |
| Name | Display name |
| Description | What the action does |
| Category | Notification, MECM, ServiceNow, Tachyon, Reporting |
| Risk Level | Low, Medium, High, Critical |
| Approval Required | Yes/No, Single/Dual |
| Max Batch Size | Maximum devices per execution |
| Parameters | Required and optional inputs |
| API Endpoint | Target system API details |
| Test Endpoint | Sandbox/test API details |
| Validation Rules | Parameter validation logic |
| Rollback Support | Whether action can be reversed |
| Test Status | Not Tested, Test Passed, Test Failed |

---

### 3.5 Bulk Operation Summarization (F-005)

#### FR-005.1: Intelligent Grouping
**Description:** System shall suggest intelligent grouping for bulk operations.

**Example Scenario:**
```
Input: 500 devices with low disk space
Output: 
  - Group 1: Finance Department (120 devices) → Create MECM Collection "Finance_DiskCleanup_2026-01"
  - Group 2: Engineering Department (200 devices) → Create MECM Collection "Eng_DiskCleanup_2026-01"
  - Group 3: Remote Workers (180 devices) → Send individual notifications
```

#### FR-005.2: Collection Creation
**Description:** System shall create MECM collections for grouped devices.

**Acceptance Criteria:**
- Auto-generate collection name (editable)
- Add all target devices to collection
- Support limiting collection (for phased rollout)
- Preview collection before creation

#### FR-005.3: Deployment Creation
**Description:** System shall create MECM deployments targeting collections.

**Acceptance Criteria:**
- Select deployment package/application
- Configure deployment schedule
- Set maintenance window compliance
- Preview deployment before creation
- Link to approval workflow

---

### 3.6 Audit & Reporting (F-007)

#### FR-007.1: Audit Log
**Description:** System shall maintain comprehensive audit logs.

**Logged Events:**
| Event Type | Data Captured |
|------------|---------------|
| Login | User, timestamp, IP address |
| Rule Change | User, before/after values, timestamp |
| Scan Execution | User, rule, device count, duration |
| Action Request | User, action type, devices, timestamp |
| Approval/Rejection | Approver, comments, timestamp |
| Action Execution | Status, errors, duration |

#### FR-007.2: Reports
**Description:** System shall provide standard reports.

**Available Reports:**
| Report | Description | Schedule |
|--------|-------------|----------|
| Daily Summary | Actions taken, pending approvals | Daily |
| Weekly Compliance | Devices by compliance status | Weekly |
| Monthly Trends | Issue trends over time | Monthly |
| Audit Report | All user actions | On-demand |
| EOL Forecast | Upcoming EOL devices | Monthly |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Requirement | Target |
|-------------|--------|
| Rule execution (100K devices) | < 5 minutes |
| UI response time | < 2 seconds |
| LLM suggestion generation | < 30 seconds |
| Concurrent users | 5 |
| Data refresh frequency | Daily (MECM backup) |

### 4.2 Scalability

| Requirement | Target |
|-------------|--------|
| Maximum devices | 100,000 |
| Maximum rules | 500 |
| Maximum concurrent scans | 3 |
| Historical data retention | 2 years |

### 4.3 Availability

| Requirement | Target |
|-------------|--------|
| Uptime | 99.5% (business hours) |
| Planned maintenance window | Weekends |
| Recovery Time Objective (RTO) | 4 hours |
| Recovery Point Objective (RPO) | 24 hours |

### 4.4 Reliability

| Requirement | Target |
|-------------|--------|
| Action success rate | > 95% |
| Data accuracy | > 99% |
| LLM suggestion relevance | > 80% (user feedback) |

---

## 5. Testing Requirements

### 5.1 Ground Truth Testing for AI/LLM Components

The ITOA Agent uses LLM and AI components that require rigorous validation to ensure accuracy, safety, and reliability. Ground truth testing provides a systematic approach to validate AI behavior against known correct outputs.

#### TR-001: Manual Test Case Management
**Description:** System shall support manual creation and management of ground truth test cases.

**Acceptance Criteria:**
- Support JSON-formatted test case definitions
- Test cases include: ID, category, input, expected output, evaluation mode
- Support multiple test categories (NL parsing, action recommendations, risk classification, summarization)
- Version control for test cases
- Minimum 100 test cases before production deployment

**Test Case Schema:**
```json
{
  "test_id": "NL-001",
  "category": "nl_parsing",
  "input": "Natural language input",
  "expected_output": { "structured output" },
  "acceptable_variations": ["alternative outputs"],
  "evaluation_mode": "exact|semantic|partial",
  "metadata": {
    "author": "string",
    "difficulty": "easy|medium|hard",
    "tags": ["array"]
  }
}
```

#### TR-002: LLM-Assisted Evaluation
**Description:** System shall leverage LLM to evaluate semantic equivalence between actual and expected outputs.

**Acceptance Criteria:**
- Use GPT-4 or equivalent for semantic evaluation
- Structured evaluation prompts with consistent scoring
- Support multiple evaluation modes:
  - **Exact:** Character-by-character match
  - **Semantic:** Meaning equivalence (LLM-judged)
  - **Partial:** Key fields must match, others flexible
  - **Range:** Numeric values within acceptable tolerance
- Generate confidence scores (0-100)
- Flag low-confidence results for human review

**Evaluation Metrics:**
| Metric | Target | Description |
|--------|--------|-------------|
| NL Parsing Accuracy | > 90% | Correct intent and parameter extraction |
| Action Recommendation Relevance | > 85% | Appropriate actions suggested |
| Risk Classification Accuracy | > 95% | Correct risk level assignment |
| Summarization Quality | > 80% | Semantic equivalence score |

#### TR-003: Test Categories
**Description:** System shall support testing across all AI/LLM-powered features.

**Test Categories:**

| Category | Description | Min Test Cases |
|----------|-------------|----------------|
| NL Parsing | Natural language rule interpretation | 40 |
| Action Recommendations | AI-suggested remediation actions | 30 |
| Risk Classification | Action risk level assessment | 25 |
| Summarization | Report and result summarization | 20 |

**Example Test Cases:**

**NL Parsing Example:**
```
Input: "Find devices with less than 10GB free disk space that haven't been active in 30 days"
Expected Output:
  conditions:
    - field: "disk_free_space_gb", operator: "<", value: 10
    - logical: "AND"
    - field: "last_active_days", operator: ">", value: 30
```

**Action Recommendation Example:**
```
Input: { rule: "EOL Devices", device_count: 150, issue: "end_of_life" }
Expected Actions: ["notify_hardware_team", "create_servicenow_ticket", "add_to_mecm_collection"]
```

#### TR-004: DevOps Pipeline Integration
**Description:** Ground truth tests shall be integrated into CI/CD pipeline.

**Acceptance Criteria:**
- Tests run automatically on every code change
- Pipeline fails if accuracy drops below thresholds
- Support for baseline comparison (detect regressions)
- Parallel execution for faster feedback
- Test results stored for trend analysis

**Pipeline Stages:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Code Push  │───▶│  Unit Tests  │───▶│ Ground Truth│───▶│   Deploy     │
└─────────────┘    └──────────────┘    │   Tests     │    │  (if pass)   │
                                       └─────────────┘    └──────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │  Generate   │
                                       │   Report    │
                                       └─────────────┘
```

**Quality Gates:**
| Gate | Condition | Action |
|------|-----------|--------|
| Minimum Accuracy | All categories > threshold | Block deploy if failed |
| Regression Check | No category drops > 5% | Warning + Review |
| Coverage | All test categories executed | Block deploy if incomplete |

#### TR-005: Test Reporting
**Description:** System shall generate comprehensive test reports.

**Acceptance Criteria:**
- Summary dashboard with pass/fail rates per category
- Detailed results with actual vs expected comparison
- Trend analysis over time
- Export to JSON, HTML, and PDF formats
- Integration with Azure DevOps test reporting

**Report Contents:**
| Section | Details |
|---------|---------|
| Summary | Overall pass rate, execution time, timestamp |
| By Category | Breakdown by test category with individual scores |
| Failed Tests | List of failures with diff analysis |
| Regressions | Tests that passed previously but now fail |
| Trends | Historical accuracy over last 30 days |

### 5.2 Unit and Integration Testing

| Test Type | Coverage Target | Tools |
|-----------|-----------------|-------|
| Unit Tests | > 80% | pytest |
| Integration Tests | All API endpoints | pytest + requests |
| UI Tests | Critical workflows | pytest-qt |

### 5.3 Performance Testing

| Test Type | Target | Tools |
|-----------|--------|-------|
| Load Testing | 100K device scan < 5min | locust |
| Stress Testing | 5 concurrent users | locust |
| LLM Response Time | < 30 seconds | Custom benchmark |

### 5.4 Security Testing

| Test Type | Frequency | Tools |
|-----------|-----------|-------|
| SAST | Every commit | SonarQube |
| Dependency Scan | Weekly | Snyk |
| Penetration Testing | Quarterly | Manual |

**Referenced Documents:**
- [Ground Truth Testing Plan](testing/Ground_Truth_Testing_Plan.md)
- [Ground Truth Requirements](testing/Ground_Truth_Requirements.md)

---

## 6. Data Requirements

### 6.1 Data Sources

#### 6.1.1 MECM Database (Read-Only)

| Table/View | Data Elements | Refresh |
|------------|---------------|---------|
| v_R_System | Device name, OS, Last Active | Daily |
| v_GS_LOGICAL_DISK | Disk space, Drive letter | Daily |
| v_GS_INSTALLED_SOFTWARE | Software inventory (name, version, vendor) | Daily |
| v_GS_ADD_REMOVE_PROGRAMS | Add/Remove Programs data | Daily |
| v_UpdateComplianceStatus | Patch compliance | Daily |
| v_Collection | Collections | Daily |

**Application-Specific Fields from v_GS_INSTALLED_SOFTWARE:**
| Field | Description |
|-------|-------------|
| ProductName0 | Application display name |
| ProductVersion0 | Installed version |
| Publisher0 | Software vendor |
| InstallDate0 | Installation date |
| ResourceID | Link to device |

#### 6.1.2 ServiceNow API

| Endpoint | Data Elements | Usage |
|----------|---------------|-------|
| /api/now/table/cmdb_ci_computer | CMDB records | Read |
| /api/now/table/cmdb_ci_appl | Application CMDB records | Read |
| /api/now/table/cmdb_rel_ci | CI relationships (App Owner) | Read |
| /api/now/table/u_eol_table | EOL dates (devices & software) | Read |
| /api/now/table/incident | Incidents | Read/Write |

#### 6.1.3 1E Tachyon API

| Endpoint | Usage |
|----------|-------|
| /Consumer/Instructions | Execute instructions |
| /Consumer/Responses | Get results |
| /Inventory/Devices | Device lookup |

#### 6.1.4 Vulnerability Data Sources (Optional)

| Source | Data Elements | Usage |
|--------|---------------|-------|
| NVD (NIST) | CVE data, CVSS scores | Read |
| Vendor Advisories | Security bulletins | Read |
| Internal Vuln DB | Custom vulnerability tracking | Read/Write |

### 6.2 Data Storage

**Application Database (PostgreSQL):**

| Table | Purpose |
|-------|---------|
| rules | Rule definitions (with entity_type field) |
| rule_executions | Scan history |
| scan_results_devices | Identified devices |
| scan_results_applications | Identified applications |
| applications | Application catalog |
| app_owners | Application owner mappings |
| vulnerabilities | CVE/vulnerability tracking |
| action_requests | Pending/completed actions |
| approvals | Approval records |
| audit_log | All user actions |
| users | User profiles |
| settings | System configuration |

### 6.3 Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Scan results | 90 days |
| Action history | 2 years |
| Audit logs | 7 years |
| Rule history | Indefinite |

---

## 7. User Interface Requirements

### 7.1 General UI Requirements

- **Technology:** Python desktop application (PyQt6/PySide6 recommended)
- **Accessibility:** WCAG 2.1 AA compliant
- **Theme:** Support light and dark modes
- **Resolution:** Minimum 1920x1080

### 7.2 Main Navigation

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Logo] IT Operations AI Agent          [User] ▼  [Settings] [Help] │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │Dashboard│ │  Rules  │ │  Scan   │ │ Actions │ │ Reports │        │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                        [Main Content Area]                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Key Screens

#### 6.3.1 Dashboard
- Summary cards (devices scanned, issues found, pending approvals)
- Recent activity feed
- Quick action buttons
- Alert notifications

#### 6.3.2 Rules Management
- Rule list with status indicators
- Rule builder (visual + natural language)
- Template gallery
- Rule execution history

#### 6.3.3 Scan Results
- Device grid with filtering/sorting
- Bulk selection toolbar
- Category summary sidebar
- Export options

#### 6.3.4 Action Management
- Pending approvals queue
- Action history
- Execution status
- Approval dialog

#### 6.3.5 Reports
- Report selector
- Date range picker
- Export options (PDF, Excel, CSV)
- Visualization charts

### 7.4 Accessibility Requirements (WCAG 2.1 AA)

| Requirement | Implementation |
|-------------|----------------|
| Keyboard Navigation | All functions accessible via keyboard |
| Screen Reader | Proper ARIA labels and roles |
| Color Contrast | Minimum 4.5:1 ratio |
| Text Scaling | Support 200% zoom |
| Focus Indicators | Visible focus states |
| Error Identification | Clear error messages with suggestions |

### 7.5 User Experience (UX) Requirements

The following UX requirements are designed to reduce cognitive load and improve user efficiency.

#### 6.5.1 Navigation & Orientation

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-001 | Breadcrumb navigation on all pages | High |
| UX-002 | Collapsible sidebar with keyboard shortcut (Ctrl+B) | Medium |
| UX-003 | Consistent header layout with user context | High |
| UX-004 | Page titles reflecting current location | High |

**Breadcrumb Pattern:**
```
Home > [Section] > [Subsection] > [Current Page]
Examples:
- Home > Rules
- Home > Settings > Action Definitions
- Home > Rules > Rule Builder > Step 2: Set Conditions
```

#### 6.5.2 Progressive Disclosure & Wizard Patterns

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-005 | Multi-step wizard for complex tasks (rule creation, action configuration) | High |
| UX-006 | Visual progress indicator showing current step and remaining steps | High |
| UX-007 | Step validation before proceeding to next step | High |
| UX-008 | Allow backward navigation without losing data | High |

**Rule Builder Wizard Steps:**
1. **Define Rule** - Name, description, entity type
2. **Set Conditions** - Natural language or manual builder
3. **Choose Actions** - Select remediation actions
4. **Test & Activate** - Preview results and enable

#### 6.5.3 Contextual Help & Guidance

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-009 | Contextual help tips on complex screens | Medium |
| UX-010 | Dismissible info banners for new users | Medium |
| UX-011 | Placeholder text with examples in input fields | Medium |
| UX-012 | Tooltips on icons and abbreviated labels | Medium |

#### 6.5.4 Empty States

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-013 | Friendly empty state messages when no data exists | Medium |
| UX-014 | Clear call-to-action in empty states | Medium |
| UX-015 | Quick links to documentation or examples | Low |

**Empty State Components:**
- Illustrative icon or graphic
- Title explaining the empty state
- Description with guidance
- Primary action button (e.g., "Create Your First Rule")
- Secondary action (e.g., "View Examples")

#### 6.5.5 Confirmation & Feedback

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-016 | Confirmation modal for destructive actions | High |
| UX-017 | Success confirmation after significant actions | High |
| UX-018 | Auto-save indicator for forms with drafts | Medium |
| UX-019 | Clear loading states during async operations | High |

**Confirmation Modal Pattern:**
```
┌─────────────────────────────────────────┐
│           ⚠️ [Warning Icon]             │
│                                         │
│     [Action Title - e.g., "Reject       │
│      this action request?"]             │
│                                         │
│     [Consequence description]           │
│                                         │
│     [Required input if needed]          │
│                                         │
│     [Cancel]        [Confirm Action]    │
└─────────────────────────────────────────┘
```

#### 6.5.6 Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| Ctrl+B | Toggle sidebar | Global |
| Ctrl+N | Create new rule | Rules page |
| Ctrl+S | Save current form | Form views |
| Ctrl+Enter | Submit form | Form views |
| Escape | Close modal/cancel action | Modals |

#### 6.5.7 Quick Actions

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-020 | Quick action cards on dashboard | High |
| UX-021 | One-click access to common tasks | High |
| UX-022 | Badge indicators for pending items | High |

**Dashboard Quick Actions:**
- Create New Rule
- Run All Active Rules
- View Pending Approvals (with count badge)
- Generate Report

#### 6.5.8 Information Hierarchy

| Requirement ID | Requirement | Priority |
|---------------|-------------|----------|
| UX-023 | Summary cards before detailed tables | High |
| UX-024 | Collapsible sections for advanced options | Medium |
| UX-025 | Pagination with configurable page sizes | High |
| UX-026 | Column visibility toggles for dense tables | Medium |

---

## 8. Security Requirements

### 8.1 Authentication

| Requirement | Implementation |
|-------------|----------------|
| Provider | Azure OAuth 2.0 |
| MFA | Required (Azure AD enforced) |
| Session Timeout | 30 minutes inactivity |
| Token Refresh | Automatic |

### 8.2 Authorization

**Role-Based Access Control (RBAC):**

| Permission | Operator | Approver | Administrator |
|------------|----------|----------|---------------|
| View Dashboard | ✓ | ✓ | ✓ |
| Manage Rules | View | View | Full |
| Execute Scans | ✓ | ✓ | ✓ |
| Request Actions | ✓ | ✓ | ✓ |
| Approve Actions | ✗ | ✓ | ✓ |
| System Settings | ✗ | ✗ | ✓ |
| User Management | ✗ | ✗ | ✓ |

### 8.3 Data Security

| Requirement | Implementation |
|-------------|----------------|
| Data at Rest | AES-256 encryption |
| Data in Transit | TLS 1.3 |
| API Keys | Encrypted storage (Azure Key Vault) |
| PII Handling | Masked in logs, filtered for LLM |
| Database Access | Connection pooling, parameterized queries |

### 8.4 LLM Security

| Requirement | Implementation |
|-------------|----------------|
| Data Filtering | Remove PII before LLM calls |
| Local LLM Option | QWEN for sensitive environments |
| Prompt Injection Prevention | Input sanitization |
| Response Validation | Check for harmful content |
| Audit | Log all LLM interactions |

### 8.5 Action Safety

| Requirement | Implementation |
|-------------|----------------|
| Mandatory Approval | All actions require approval |
| Separation of Duties | Requestor cannot self-approve |
| Rollback Capability | Where possible (MECM deployments) |
| Dry Run Mode | Preview action without execution |
| Rate Limiting | Max 1000 devices per action |

---

## 9. Compliance Requirements

### 9.1 Accessibility Compliance

- WCAG 2.1 Level AA compliance
- Regular accessibility audits
- Documented accessibility features

### 9.2 Audit Compliance

- Complete audit trail for all actions
- Tamper-proof logs
- 7-year retention for audit data
- Export capability for auditors

### 9.3 Data Protection

- PII minimization
- Data masking in non-production
- Right to access (data export)
- Secure deletion procedures

---

## 10. Appendices

### Appendix A: Rule Examples

#### Example 1: Low Disk Space with Inactive Device
```yaml
name: "Low Disk Space - Inactive Devices"
description: "Devices with low disk space that haven't checked in recently"
conditions:
  - field: "disk_free_space_gb"
    operator: "<"
    value: 10
  - logical: "AND"
  - field: "last_active_days"
    operator: ">"
    value: 28
actions:
  - type: "send_notification"
    target: "primary_user"
    template: "low_disk_inactive"
schedule: "daily"
```

#### Example 2: EOL Hardware Planning
```yaml
name: "EOL Hardware - 1 Year Warning"
description: "Hardware reaching end of life within 1 year"
conditions:
  - field: "eol_date"
    operator: "within_days"
    value: 365
actions:
  - type: "send_notification"
    target: "hardware_team"
    template: "eol_planning"
schedule: "weekly"
```

### Appendix B: Glossary

| Term | Definition |
|------|------------|
| Collection | MECM grouping of devices for targeting |
| Deployment | MECM software/patch distribution |
| Instruction | 1E Tachyon real-time command |
| Incident | ServiceNow trouble ticket |

### Appendix C: Referenced Documents

- Microsoft Endpoint Configuration Manager Documentation
- ServiceNow API Reference
- 1E Tachyon Platform Guide
- Azure OAuth 2.0 Documentation
- WCAG 2.1 Guidelines

---

**Document Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Security Officer | | | |
| Operations Manager | | | |

---

*End of Requirements Document*
