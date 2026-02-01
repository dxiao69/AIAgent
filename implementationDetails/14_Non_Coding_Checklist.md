# 14 - Non-Coding Tasks Checklist

## Overview

This checklist covers all non-coding activities required to successfully deploy the IT Operations AI Agent. Complete these tasks in parallel with development to avoid deployment blockers.

---

## Phase 1: Infrastructure & Access Setup (Weeks 1-2)

### Azure AD Configuration
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Create Azure AD app registration | IT Admin | | |
| [ ] Configure redirect URIs for desktop app | IT Admin | | `http://localhost:8400/callback` |
| [ ] Add API permissions (User.Read, profile, email) | IT Admin | | |
| [ ] Generate client secret | IT Admin | | Store securely, expires in 24 months |
| [ ] Document Tenant ID | IT Admin | | |
| [ ] Document Client ID | IT Admin | | |
| [ ] Add test users to app | IT Admin | | |
| [ ] Configure token lifetime policies | IT Admin | | Recommended: 1 hour access token |

**Deliverable:** Azure AD credentials document (store in secure vault)

### MECM Access
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Request read-only access to MECM SQL database | DBA | | |
| [ ] Identify MECM SQL Server hostname | MECM Admin | | |
| [ ] Identify database name (typically CM_XXX) | MECM Admin | | |
| [ ] Create service account for API access | IT Admin | | |
| [ ] Test SQL connectivity from app server | DevOps | | |
| [ ] Document available views/tables | MECM Admin | | v_R_System, v_GS_DISK, etc. |
| [ ] Verify query performance on large datasets | DBA | | Test with 10k+ devices |

**Deliverable:** MECM connection string and service account credentials

### ServiceNow Setup
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Request ServiceNow instance access | ServiceNow Admin | | |
| [ ] Create integration user account | ServiceNow Admin | | |
| [ ] Assign roles: `itil`, `rest_api_explorer` | ServiceNow Admin | | |
| [ ] Create custom fields on incident table | ServiceNow Admin | | See below |
| [ ] Configure assignment groups | ServiceNow Admin | | |
| [ ] Test API connectivity | DevOps | | |
| [ ] Document instance URL | ServiceNow Admin | | |
| [ ] Set up OAuth (if using OAuth auth) | ServiceNow Admin | | Optional |

**Custom Fields to Create:**
```
Field Name: u_scan_id
Type: String (36)
Table: incident

Field Name: u_rule_name  
Type: String (255)
Table: incident

Field Name: u_device_count
Type: Integer
Table: incident

Field Name: u_source_system
Type: String (50)
Default: "ITOpsAIAgent"
Table: incident
```

**Deliverable:** ServiceNow credentials and instance configuration

### Tachyon (1E) Setup
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Request Tachyon API access | 1E Admin | | |
| [ ] Generate X.509 client certificate | 1E Admin | | |
| [ ] Register certificate with Tachyon | 1E Admin | | |
| [ ] Document platform URL | 1E Admin | | |
| [ ] Identify available instructions | 1E Admin | | List allowed instructions |
| [ ] Create consumer registration | 1E Admin | | Consumer name: "ITOpsAIAgent" |
| [ ] Test certificate authentication | DevOps | | |
| [ ] Document coverage tags available | 1E Admin | | For device targeting |

**Deliverable:** Tachyon certificates and platform configuration

### LLM API Setup
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Decide LLM provider (OpenAI/Azure/QWEN) | Architect | | |
| [ ] Create API account | IT Admin | | |
| [ ] Generate API keys | IT Admin | | |
| [ ] Set up billing alerts | Finance | | |
| [ ] Configure rate limits | IT Admin | | |
| [ ] Document model names to use | Architect | | gpt-4, gpt-3.5-turbo |
| [ ] Estimate monthly token usage | Architect | | |
| [ ] Get budget approval | Manager | | |

**Deliverable:** LLM API keys and usage limits

### Database & Cache Infrastructure
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Provision PostgreSQL 15+ instance | DBA | | |
| [ ] Create database: `itops_agent` | DBA | | |
| [ ] Create service account with full access | DBA | | |
| [ ] Configure connection pooling | DBA | | PgBouncer recommended |
| [ ] Set up automated backups | DBA | | Daily, 30-day retention |
| [ ] Provision Redis instance | DevOps | | |
| [ ] Configure Redis persistence | DevOps | | AOF recommended |
| [ ] Document connection strings | DevOps | | |
| [ ] Test connectivity from app network | DevOps | | |

**Deliverable:** Database and Redis connection strings

### Desktop App Cross-Platform Support
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Test PySide6 app on Windows 10/11 | QA | | |
| [ ] Test PySide6 app on macOS (Intel) | QA | | macOS 12+ |
| [ ] Test PySide6 app on macOS (Apple Silicon) | QA | | M1/M2/M3 chips |
| [ ] Set up Windows code signing certificate | DevOps | | For MSI installer |
| [ ] Set up Apple Developer account | DevOps | | For notarization |
| [ ] Create macOS .app bundle | DevOps | | PyInstaller |
| [ ] Create macOS DMG installer | DevOps | | |
| [ ] Notarize macOS app with Apple | DevOps | | Required for Gatekeeper |
| [ ] Test auto-update on both platforms | QA | | |
| [ ] Document platform-specific requirements | Tech Writer | | |

**Platform Requirements:**
```
Windows:
- Windows 10 (1809+) or Windows 11
- 64-bit only
- .NET Framework 4.7.2+ (for some Qt features)

macOS:
- macOS 12 Monterey or later
- Intel x64 or Apple Silicon (Universal Binary)
- Rosetta 2 for Intel apps on Apple Silicon (fallback)
```

**Deliverable:** Tested installers for both platforms

### Container Registry & Kubernetes
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Set up container registry | DevOps | | ACR/ECR/Docker Hub |
| [ ] Create registry credentials | DevOps | | |
| [ ] Provision Kubernetes cluster | DevOps | | |
| [ ] Configure kubectl access | DevOps | | |
| [ ] Set up namespaces (staging, production) | DevOps | | |
| [ ] Configure ingress controller | DevOps | | nginx-ingress |
| [ ] Set up cert-manager for TLS | DevOps | | |
| [ ] Document cluster endpoints | DevOps | | |

**Deliverable:** Registry and Kubernetes access configured

---

## Phase 2: Security & Compliance (Weeks 2-4)

### Security Review
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Complete security questionnaire for LLM usage | Security | | |
| [ ] Document data flow diagrams | Architect | | |
| [ ] Identify PII in MECM data | Security | | |
| [ ] Define PII masking rules | Security | | See filter patterns |
| [ ] Review network security requirements | Security | | |
| [ ] Document encryption requirements | Security | | TLS 1.2+ required |
| [ ] Get approval for external API calls | Security | | OpenAI, ServiceNow |
| [ ] Penetration test plan | Security | | Schedule for Week 10 |

**PII Patterns to Filter:**
```
- Email addresses: *@*.com, *@*.org
- IP addresses: Internal ranges
- Usernames: Domain\User format
- Computer names: Hostname patterns
- Employee IDs: If in MECM data
```

**Deliverable:** Security approval document

### RBAC & Permissions
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Define user roles | Product Owner | | |
| [ ] Map roles to permissions | Product Owner | | See matrix below |
| [ ] Define Azure AD groups | IT Admin | | |
| [ ] Document approval authority levels | Manager | | |
| [ ] Create escalation matrix | Manager | | |

**Role Permission Matrix:**

| Permission | Viewer | Operator | Admin | Super Admin |
|------------|--------|----------|-------|-------------|
| View dashboard | ✓ | ✓ | ✓ | ✓ |
| View rules | ✓ | ✓ | ✓ | ✓ |
| Execute scans | | ✓ | ✓ | ✓ |
| Create rules | | ✓ | ✓ | ✓ |
| Approve low severity | | ✓ | ✓ | ✓ |
| Approve medium severity | | | ✓ | ✓ |
| Approve high/critical | | | | ✓ |
| Manage users | | | ✓ | ✓ |
| System configuration | | | | ✓ |

**Deliverable:** RBAC documentation and Azure AD groups

### Approval Workflow Policies
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Define severity levels for actions | Product Owner | | |
| [ ] Set approval timeout (default: 72 hours) | Product Owner | | |
| [ ] Define auto-approval rules | Product Owner | | Low severity only? |
| [ ] Create approval notification templates | Product Owner | | Email/Teams |
| [ ] Document escalation procedures | Manager | | |
| [ ] Define audit requirements | Compliance | | |

**Approval Matrix:**

| Action Type | Low | Medium | High | Critical |
|-------------|-----|--------|------|----------|
| Create incident | Auto | Auto | 1 approver | 2 approvers |
| Restart service | Auto | 1 approver | 2 approvers | Not allowed |
| Clear temp files | Auto | Auto | 1 approver | 1 approver |
| Deploy patch | 1 approver | 2 approvers | CAB | CAB |
| Custom action | 1 approver | 2 approvers | 2 approvers | Not allowed |

**Deliverable:** Approval policy document

---

## Phase 3: Testing & Validation (Weeks 5-8)

### Ground Truth Test Library
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Create 20+ rule interpretation test cases | QA | | |
| [ ] Create 20+ query generation test cases | QA | | |
| [ ] Create 10+ remediation suggestion tests | QA | | |
| [ ] Document expected outputs for each | QA | | |
| [ ] Set accuracy thresholds | Product Owner | | Min 85% |
| [ ] Create edge case tests | QA | | |
| [ ] Review tests with SMEs | MECM Admin | | |

**Sample Test Categories:**
```
1. Rule Interpretation
   - Simple conditions
   - Complex AND/OR logic
   - Negation handling
   - Threshold comparisons

2. Query Generation
   - Device queries
   - Software queries
   - Patch queries
   - Combined queries

3. Remediation Suggestions
   - Disk space issues
   - Patching recommendations
   - Service restart suggestions
```

**Deliverable:** Test library JSON files

### MECM Query Validation
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Validate v_R_System query | MECM Admin | | |
| [ ] Validate v_GS_DISK query | MECM Admin | | |
| [ ] Validate v_GS_ADD_REMOVE_PROGRAMS | MECM Admin | | |
| [ ] Validate patch compliance queries | MECM Admin | | |
| [ ] Test with production data volume | DBA | | |
| [ ] Document query performance | DBA | | Target: <5s |
| [ ] Identify missing indexes | DBA | | |

**Deliverable:** Validated MECM queries document

### User Acceptance Testing Plan
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Define UAT scenarios | Product Owner | | |
| [ ] Identify UAT participants (Windows users) | Manager | | 2-3 users |
| [ ] Identify UAT participants (macOS users) | Manager | | 2-3 users |
| [ ] Schedule UAT sessions | PM | | Week 11 |
| [ ] Create UAT feedback form | QA | | |
| [ ] Define go/no-go criteria | Product Owner | | |
| [ ] Test platform-specific UI differences | QA | | Menu bar, shortcuts |

**Deliverable:** UAT plan and schedule

---

## Phase 4: Documentation & Training (Weeks 9-12)

### User Documentation
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Desktop app user guide | Tech Writer | | |
| [ ] Rule creation tutorial | Tech Writer | | |
| [ ] Natural language query examples | Tech Writer | | |
| [ ] FAQ document | Tech Writer | | |
| [ ] Video walkthrough (optional) | Tech Writer | | |

**User Guide Sections:**
```
1. Getting Started
   - Installation
   - Login process
   - Dashboard overview

2. Working with Rules
   - Creating rules
   - Natural language input
   - Condition builder
   - Testing rules

3. Running Scans
   - Manual scans
   - Scheduled scans
   - Viewing results

4. Managing Actions
   - Understanding recommendations
   - Approval workflow
   - Tracking execution

5. Troubleshooting
   - Common issues
   - Getting help
```

**Deliverable:** User documentation package

### Operations Documentation
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] System architecture diagram | Architect | | |
| [ ] Runbook: Service restart procedures | DevOps | | |
| [ ] Runbook: Database maintenance | DBA | | |
| [ ] Runbook: Log analysis | DevOps | | |
| [ ] Incident response procedures | DevOps | | |
| [ ] Disaster recovery plan | DevOps | | |
| [ ] Capacity planning guide | Architect | | |

**Deliverable:** Operations runbook

### Training Plan
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Schedule admin training | PM | | 2 hours |
| [ ] Schedule operator training | PM | | 1 hour |
| [ ] Schedule end-user training | PM | | 30 min |
| [ ] Create training materials | Tech Writer | | |
| [ ] Record training sessions | Tech Writer | | |
| [ ] Create quick reference cards | Tech Writer | | |

**Deliverable:** Training materials and schedule

---

## Phase 5: Deployment Planning (Weeks 10-12)

### Environment Preparation
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Staging environment ready | DevOps | | |
| [ ] Production environment ready | DevOps | | |
| [ ] DNS entries configured | DevOps | | itops-api.company.com |
| [ ] TLS certificates provisioned | DevOps | | |
| [ ] Firewall rules configured | Network | | |
| [ ] Load balancer configured | DevOps | | |

**Deliverable:** Environment readiness checklist

### Monitoring & Alerting
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Configure Prometheus/metrics | DevOps | | |
| [ ] Create Grafana dashboards | DevOps | | |
| [ ] Define alert thresholds | DevOps | | See below |
| [ ] Configure PagerDuty/alert routing | DevOps | | |
| [ ] Set up log aggregation | DevOps | | ELK/Splunk/Loki |
| [ ] Create log dashboards | DevOps | | |
| [ ] Test alerting | DevOps | | |

**Alert Thresholds:**

| Metric | Warning | Critical |
|--------|---------|----------|
| API response time | >500ms | >2000ms |
| Error rate | >1% | >5% |
| CPU utilization | >70% | >90% |
| Memory utilization | >80% | >95% |
| Queue depth | >100 | >500 |
| Database connections | >80% | >95% |
| Disk space | <20% | <10% |

**Deliverable:** Monitoring dashboards and alert configuration

### Go-Live Checklist
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] All tests passing | QA | | |
| [ ] Security approval obtained | Security | | |
| [ ] UAT sign-off | Product Owner | | |
| [ ] Runbooks reviewed | DevOps | | |
| [ ] Rollback plan documented | DevOps | | |
| [ ] Support team briefed | Support | | |
| [ ] Communication plan ready | PM | | |
| [ ] Maintenance window scheduled | PM | | |

**Deliverable:** Go-live approval

---

## Phase 6: Stakeholder Activities (Ongoing)

### Business Approvals
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Define auto-remediation scope | Director | | Which actions? |
| [ ] Budget approval for cloud costs | Finance | | |
| [ ] Legal review of LLM usage | Legal | | Data handling |
| [ ] Privacy impact assessment | Privacy | | If required |
| [ ] Change advisory board briefing | Manager | | |

**Deliverable:** Business approval documentation

### SLA & Support
| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| [ ] Define system SLAs | Manager | | |
| [ ] Establish support hours | Manager | | |
| [ ] Create escalation contacts | Manager | | |
| [ ] Define maintenance windows | Manager | | |
| [ ] Document support process | Support | | |

**Proposed SLAs:**

| Metric | Target |
|--------|--------|
| System availability | 99.5% |
| API response time (p95) | <1s |
| Incident creation time | <30s |
| Action execution (after approval) | <5min |
| Support response (P1) | <15min |
| Support response (P2) | <1hr |
| Support response (P3) | <4hr |

**Deliverable:** SLA document

---

## Quick Reference: Key Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Project Manager | | | |
| Technical Lead | | | |
| MECM Admin | | | |
| ServiceNow Admin | | | |
| 1E/Tachyon Admin | | | |
| DBA | | | |
| Security Lead | | | |
| DevOps Lead | | | |

---

## Timeline Summary

| Phase | Weeks | Key Milestones |
|-------|-------|----------------|
| Infrastructure Setup | 1-2 | All credentials obtained |
| Security & Compliance | 2-4 | Security approval |
| Testing & Validation | 5-8 | Test library complete |
| Documentation | 9-12 | All docs ready |
| Deployment Planning | 10-12 | Environments ready |
| Stakeholder Activities | Ongoing | Business sign-off |
| Go-Live | Week 14 | Production deployment |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| MECM access delayed | High | Medium | Start request Week 1 |
| LLM accuracy below threshold | High | Low | Extensive testing, fallback to rule-based |
| Security approval delayed | High | Medium | Early engagement with InfoSec |
| ServiceNow customization delayed | Medium | Medium | Use default fields initially |
| Tachyon cert issues | Medium | Low | Test early, have backup plan |
| macOS notarization rejected | Medium | Low | Test with Apple early, follow guidelines |
| Platform-specific UI bugs | Medium | Medium | Test on both platforms throughout dev |

---

**Last Updated:** [Date]
**Document Owner:** [Name]
**Version:** 1.0
