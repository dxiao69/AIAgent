# Ground Truth Test Requirements

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Related Document:** [Ground Truth Testing Plan](Ground_Truth_Testing_Plan.md)

---

## Functional Requirements

### GTR-001: Manual Test Case Management

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| GTR-001.1 | System shall support JSON-based test case definitions | High |
| GTR-001.2 | Test cases shall include input, expected output, and metadata | High |
| GTR-001.3 | System shall support multiple evaluation modes (exact, semantic, partial, range) | High |
| GTR-001.4 | Test cases shall be version-controlled in Git | High |
| GTR-001.5 | System shall support acceptable variations for flexible matching | Medium |

### GTR-002: LLM-Assisted Evaluation

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| GTR-002.1 | System shall integrate with external LLM for evaluation (GPT-4 or equivalent) | High |
| GTR-002.2 | Evaluation shall produce scores (0-100) with breakdown by criteria | High |
| GTR-002.3 | System shall support configurable pass/fail thresholds | High |
| GTR-002.4 | Failed evaluations shall include detailed feedback | High |
| GTR-002.5 | System shall flag disputed cases for human review | Medium |
| GTR-002.6 | Evaluation prompts shall be configurable and version-controlled | Medium |

### GTR-003: Test Categories

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| GTR-003.1 | System shall test Natural Language to Condition parsing | High |
| GTR-003.2 | System shall test Action Recommendation accuracy | High |
| GTR-003.3 | System shall test Risk Classification accuracy | High |
| GTR-003.4 | System shall test Summarization quality | Medium |
| GTR-003.5 | System shall support adding new test categories | Low |

### GTR-004: DevOps Pipeline Integration

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| GTR-004.1 | Ground truth tests shall run automatically on PR/merge to main | High |
| GTR-004.2 | Pipeline shall block deployment if pass rate < 95% | High |
| GTR-004.3 | System shall detect and alert on regressions (>10 point score drop) | High |
| GTR-004.4 | Test results shall be published to Azure DevOps test reporting | High |
| GTR-004.5 | Pipeline shall generate JSON and XML reports | Medium |
| GTR-004.6 | Pipeline shall integrate with team alerting (Teams/Email) | Medium |

### GTR-005: Reporting & Analytics

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| GTR-005.1 | System shall generate per-build test reports | High |
| GTR-005.2 | System shall track test pass rate trends over time | Medium |
| GTR-005.3 | System shall identify commonly failing test categories | Medium |
| GTR-005.4 | Dashboard shall display current ground truth health | Medium |
| GTR-005.5 | System shall export reports in multiple formats (JSON, CSV, PDF) | Low |

---

## Non-Functional Requirements

### GTR-NFR-001: Performance

| Req ID | Requirement | Target |
|--------|-------------|--------|
| GTR-NFR-001.1 | Full test suite shall complete within 10 minutes | < 10 min |
| GTR-NFR-001.2 | Individual test evaluation shall complete within 30 seconds | < 30 sec |
| GTR-NFR-001.3 | System shall support parallel test execution | 4+ parallel |

### GTR-NFR-002: Reliability

| Req ID | Requirement | Target |
|--------|-------------|--------|
| GTR-NFR-002.1 | LLM evaluator shall have retry logic for API failures | 3 retries |
| GTR-NFR-002.2 | Test results shall be deterministic (same input = same score ±5) | ±5 points |
| GTR-NFR-002.3 | System shall gracefully handle LLM service outages | Fallback mode |

### GTR-NFR-003: Maintainability

| Req ID | Requirement | Target |
|--------|-------------|--------|
| GTR-NFR-003.1 | Test cases shall follow documented JSON schema | 100% compliance |
| GTR-NFR-003.2 | Evaluation prompts shall be externalized (not hardcoded) | Configurable |
| GTR-NFR-003.3 | Adding new test cases shall not require code changes | Schema-driven |

---

## Acceptance Criteria

### Phase 1: Manual Ground Truth

- [ ] Minimum 115 test cases created and peer-reviewed
- [ ] Test case JSON schema validated
- [ ] All test categories covered (NL, Actions, Risk, Summary)
- [ ] Test framework integrated with pytest

### Phase 2: LLM-Assisted Evaluation

- [ ] Evaluator achieves >90% agreement with human reviewers
- [ ] False positive rate < 5%
- [ ] All evaluation modes functional (exact, semantic, partial, range)
- [ ] Disputed case workflow implemented

### Phase 3: DevOps Pipeline

- [ ] Pipeline runs on every PR to main branch
- [ ] Deployment blocked when pass rate < 95%
- [ ] Regression alerts configured
- [ ] Dashboard operational with trend tracking

---

## Test Data Minimum Requirements

| Category | Minimum Cases | Coverage Requirements |
|----------|---------------|----------------------|
| NL Parsing - Disk Space | 10 | Simple, compound, negation |
| NL Parsing - EOL | 10 | Date ranges, relative dates |
| NL Parsing - Inactivity | 8 | Days, weeks, months |
| NL Parsing - Applications | 10 | App name, version, CVE |
| NL Parsing - Compound | 12 | AND, OR, nested |
| Action Recommendations | 30 | All action types |
| Risk Classification | 20 | Low, Medium, High |
| Summarization | 15 | Various sizes |
| **Total** | **115** | |

---

## Dependencies

| Dependency | Description | Required By |
|------------|-------------|-------------|
| LLM API Access | OpenAI GPT-4 or Azure OpenAI | Phase 2 |
| Azure DevOps | Pipeline and test reporting | Phase 3 |
| pytest | Test framework | Phase 1 |
| JSON Schema Validator | Test case validation | Phase 1 |
