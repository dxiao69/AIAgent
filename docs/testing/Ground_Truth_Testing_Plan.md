# Ground Truth Testing Plan

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Project:** IT Operations AI Agent (ITOA Agent)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Categories](#2-test-categories)
3. [Phase 1: Manual Ground Truth Data](#3-phase-1-manual-ground-truth-data)
4. [Phase 2: LLM-Assisted Evaluation](#4-phase-2-llm-assisted-evaluation)
5. [Phase 3: DevOps Pipeline Integration](#5-phase-3-devops-pipeline-integration)
6. [Test Data Format](#6-test-data-format)
7. [Success Metrics](#7-success-metrics)
8. [Implementation Roadmap](#8-implementation-roadmap)

---

## 1. Overview

### 1.1 Purpose

Ground truth testing ensures the AI/LLM components of the ITOA Agent produce accurate, reliable, and consistent outputs. This is critical for:

- **Natural Language Rule Parsing**: Ensuring user intent is correctly interpreted
- **Action Suggestions**: Validating AI-recommended remediation actions
- **Condition Generation**: Verifying generated query conditions match expectations
- **Risk Assessment**: Confirming action risk levels are accurately classified

### 1.2 Scope

| Component | Description | Priority |
|-----------|-------------|----------|
| NL-to-Condition Parser | Converts natural language to rule conditions | High |
| Action Recommender | Suggests appropriate remediation actions | High |
| Summarization Engine | Generates bulk operation summaries | Medium |
| Risk Classifier | Assesses action risk levels | High |

### 1.3 Testing Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Ground Truth Testing Pipeline                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: Manual        Phase 2: LLM-Assisted    Phase 3: DevOps   │
│  ┌─────────────────┐   ┌─────────────────────┐   ┌──────────────┐  │
│  │ Human-curated   │   │ LLM evaluates new   │   │ Automated    │  │
│  │ test cases with │ → │ outputs against     │ → │ CI/CD gate   │  │
│  │ expected output │   │ ground truth        │   │ for releases │  │
│  └─────────────────┘   └─────────────────────┘   └──────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Categories

### 2.1 Natural Language Parsing Tests

Tests that the NL input is correctly converted to structured conditions.

| Test ID | Category | Description |
|---------|----------|-------------|
| NL-001 | Disk Space | Simple disk space queries |
| NL-002 | EOL/EOS | End of life date queries |
| NL-003 | Inactivity | Last active/seen queries |
| NL-004 | Compound | Multiple conditions with AND/OR |
| NL-005 | Negation | "NOT" conditions |
| NL-006 | Application | App-specific queries |
| NL-007 | Vulnerability | CVE/vulnerability queries |
| NL-008 | Edge Cases | Ambiguous or complex phrasing |

### 2.2 Action Recommendation Tests

Tests that appropriate actions are suggested for given scenarios.

| Test ID | Category | Description |
|---------|----------|-------------|
| AR-001 | Notification | Email/Teams notification suggestions |
| AR-002 | Collection | MECM collection creation |
| AR-003 | Ticketing | ServiceNow ticket creation |
| AR-004 | Remediation | 1E Tachyon script execution |
| AR-005 | Multi-Action | Multiple action combinations |
| AR-006 | Risk Match | Correct risk level assignment |

### 2.3 Summarization Tests

Tests that bulk operation summaries are accurate and clear.

| Test ID | Category | Description |
|---------|----------|-------------|
| SM-001 | Device Summary | Summarizing device lists |
| SM-002 | Action Summary | Summarizing proposed actions |
| SM-003 | Impact Summary | Summarizing potential impact |

---

## 3. Phase 1: Manual Ground Truth Data

### 3.1 Overview

In Phase 1, human experts create and validate test cases with known correct outputs.

### 3.2 Test Case Creation Process

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Subject    │     │   Create     │     │    Peer      │     │   Add to     │
│   Matter     │ ──▶ │   Test Case  │ ──▶ │   Review     │ ──▶ │   Ground     │
│   Expert     │     │   + Expected │     │   Approval   │     │   Truth Set  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 3.3 Minimum Test Case Requirements

| Category | Minimum Cases | Coverage |
|----------|---------------|----------|
| NL Parsing | 50 cases | All condition types |
| Action Recommendations | 30 cases | All action types |
| Risk Classification | 20 cases | All risk levels |
| Summarization | 15 cases | Various sizes |
| **Total** | **115 cases** | |

### 3.4 Test Case Authoring Guidelines

1. **Diverse Phrasing**: Include multiple ways to express the same intent
2. **Edge Cases**: Include boundary conditions and unusual inputs
3. **Real-World Scenarios**: Based on actual IT operations use cases
4. **Negative Cases**: Include inputs that should fail or be rejected
5. **Version Control**: All test cases tracked in Git

---

## 4. Phase 2: LLM-Assisted Evaluation

### 4.1 Overview

Use a separate LLM instance (evaluator) to assess outputs against ground truth, enabling scalable and consistent evaluation.

### 4.2 Evaluation Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LLM-Assisted Evaluation                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Test Input          Production LLM          Evaluator LLM         │
│  ┌──────────┐        ┌──────────────┐        ┌──────────────┐      │
│  │ "Find    │        │              │        │              │      │
│  │ devices  │ ────▶  │  ITOA Agent  │ ────▶  │  GPT-4 /     │      │
│  │ with low │        │  (Under Test)│        │  Evaluator   │      │
│  │ disk"    │        │              │        │              │      │
│  └──────────┘        └──────────────┘        └──────────────┘      │
│       │                     │                       │              │
│       │                     ▼                       ▼              │
│       │              ┌──────────────┐        ┌──────────────┐      │
│       │              │   Actual     │        │   Evaluation │      │
│       └─────────────▶│   Output     │───────▶│   Score      │      │
│                      └──────────────┘        │   + Feedback │      │
│   Ground Truth                               └──────────────┘      │
│  ┌──────────┐                                      │               │
│  │ Expected │──────────────────────────────────────┘               │
│  │ Output   │                                                      │
│  └──────────┘                                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Evaluation Prompt Template

```
You are an evaluator for an IT Operations AI Agent. Compare the actual output 
against the expected ground truth and provide a score.

## Test Case
- **Input**: {input}
- **Expected Output**: {expected_output}
- **Actual Output**: {actual_output}

## Evaluation Criteria
1. **Semantic Correctness** (0-40 points): Does the output capture the correct intent?
2. **Structural Accuracy** (0-30 points): Is the format/structure correct?
3. **Completeness** (0-20 points): Are all required elements present?
4. **No Hallucination** (0-10 points): No invented or incorrect information?

## Response Format
{
  "total_score": <0-100>,
  "semantic_correctness": <0-40>,
  "structural_accuracy": <0-30>,
  "completeness": <0-20>,
  "no_hallucination": <0-10>,
  "pass": <true/false>,
  "feedback": "<explanation of score>"
}

Pass threshold: 80 points
```

### 4.4 Evaluation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Exact Match** | Output must match exactly | Structured conditions |
| **Semantic Match** | Meaning must be equivalent | NL variations |
| **Partial Match** | Key elements must be present | Action suggestions |
| **Range Match** | Output within acceptable range | Risk scores |

### 4.5 Handling Disagreements

When LLM evaluator score differs significantly from human assessment:

1. Flag for human review
2. Add to "disputed cases" queue
3. Human makes final determination
4. Update evaluation prompt if systematic issue found

---

## 5. Phase 3: DevOps Pipeline Integration

### 5.1 Pipeline Architecture

```yaml
# Azure DevOps Pipeline - Ground Truth Testing Stage
stages:
  - stage: GroundTruthTesting
    displayName: 'AI Ground Truth Validation'
    jobs:
      - job: RunGroundTruthTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          
          - script: |
              pip install -r requirements-test.txt
            displayName: 'Install test dependencies'
          
          - script: |
              python -m pytest tests/ground_truth/ \
                --gt-data=tests/ground_truth/data/ \
                --gt-threshold=80 \
                --gt-report=ground_truth_report.json
            displayName: 'Run Ground Truth Tests'
          
          - task: PublishTestResults@2
            inputs:
              testResultsFiles: '**/ground_truth_report.xml'
              testRunTitle: 'Ground Truth Test Results'
          
          - script: |
              python scripts/evaluate_gt_results.py \
                --report=ground_truth_report.json \
                --fail-threshold=95
            displayName: 'Evaluate Pass Rate'
            failOnStderr: true
```

### 5.2 Pipeline Gates

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Individual Test Pass | Score ≥ 80 | Mark test as failed |
| Overall Pass Rate | ≥ 95% tests pass | Block deployment |
| Regression Detection | No score drops > 10 | Alert + review |
| New Test Coverage | All new features tested | Block PR merge |

### 5.3 Pipeline Triggers

```yaml
trigger:
  branches:
    include:
      - main
      - release/*
  paths:
    include:
      - src/llm/**
      - src/nl_parser/**
      - src/action_recommender/**

pr:
  branches:
    include:
      - main
  paths:
    include:
      - src/llm/**
```

### 5.4 Reporting & Dashboards

| Report | Frequency | Audience |
|--------|-----------|----------|
| Per-Build Report | Every build | Developers |
| Weekly Summary | Weekly | Team Lead |
| Trend Analysis | Monthly | Management |
| Regression Alert | Immediate | On-call |

---

## 6. Test Data Format

### 6.1 Directory Structure

```
tests/
└── ground_truth/
    ├── data/
    │   ├── nl_parsing/
    │   │   ├── disk_space.json
    │   │   ├── eol_queries.json
    │   │   ├── compound_conditions.json
    │   │   └── edge_cases.json
    │   ├── action_recommendations/
    │   │   ├── notification_actions.json
    │   │   ├── remediation_actions.json
    │   │   └── multi_actions.json
    │   ├── risk_classification/
    │   │   └── risk_levels.json
    │   └── summarization/
    │       └── bulk_summaries.json
    ├── evaluator/
    │   ├── prompts/
    │   │   └── evaluation_prompt.txt
    │   └── config.yaml
    ├── conftest.py
    ├── test_nl_parsing.py
    ├── test_action_recommendations.py
    ├── test_risk_classification.py
    └── test_summarization.py
```

### 6.2 Test Case JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["test_id", "category", "input", "expected_output", "metadata"],
  "properties": {
    "test_id": {
      "type": "string",
      "pattern": "^[A-Z]{2,3}-[0-9]{3}$",
      "description": "Unique test identifier (e.g., NL-001)"
    },
    "category": {
      "type": "string",
      "enum": ["nl_parsing", "action_recommendation", "risk_classification", "summarization"]
    },
    "input": {
      "type": "object",
      "properties": {
        "text": { "type": "string" },
        "context": { "type": "object" }
      },
      "required": ["text"]
    },
    "expected_output": {
      "type": "object",
      "description": "The ground truth expected output"
    },
    "acceptable_variations": {
      "type": "array",
      "items": { "type": "object" },
      "description": "Alternative acceptable outputs"
    },
    "evaluation_mode": {
      "type": "string",
      "enum": ["exact", "semantic", "partial", "range"],
      "default": "semantic"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "author": { "type": "string" },
        "created_date": { "type": "string", "format": "date" },
        "reviewed_by": { "type": "string" },
        "difficulty": { "type": "string", "enum": ["easy", "medium", "hard"] },
        "tags": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

### 6.3 Example Test Cases

#### NL Parsing Test Case

```json
{
  "test_id": "NL-001",
  "category": "nl_parsing",
  "input": {
    "text": "Find all devices with less than 10GB free disk space"
  },
  "expected_output": {
    "conditions": [
      {
        "field": "disk_free_space_gb",
        "operator": "less_than",
        "value": 10
      }
    ],
    "logical_operator": null,
    "entity_type": "devices"
  },
  "acceptable_variations": [
    {
      "conditions": [
        {
          "field": "free_disk_space",
          "operator": "<",
          "value": 10
        }
      ]
    }
  ],
  "evaluation_mode": "semantic",
  "metadata": {
    "author": "john.doe@company.com",
    "created_date": "2026-01-31",
    "reviewed_by": "jane.smith@company.com",
    "difficulty": "easy",
    "tags": ["disk_space", "simple_query"]
  }
}
```

#### Action Recommendation Test Case

```json
{
  "test_id": "AR-001",
  "category": "action_recommendation",
  "input": {
    "text": "523 devices found with low disk space",
    "context": {
      "rule_category": "disk_space",
      "device_count": 523,
      "severity": "warning"
    }
  },
  "expected_output": {
    "recommended_actions": [
      {
        "action_type": "send_email_notification",
        "priority": 1,
        "risk_level": "low",
        "parameters": {
          "template": "low_disk_space_warning"
        }
      },
      {
        "action_type": "create_mecm_collection",
        "priority": 2,
        "risk_level": "medium",
        "parameters": {
          "collection_name_pattern": "ITOA_LowDiskSpace_{timestamp}"
        }
      }
    ],
    "explanation": "Notify device owners and group devices for potential remediation"
  },
  "evaluation_mode": "partial",
  "metadata": {
    "author": "john.doe@company.com",
    "created_date": "2026-01-31",
    "difficulty": "medium",
    "tags": ["disk_space", "notification", "collection"]
  }
}
```

---

## 7. Success Metrics

### 7.1 Key Performance Indicators (KPIs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Overall Pass Rate** | ≥ 95% | % of tests passing threshold |
| **NL Parsing Accuracy** | ≥ 90% | Semantic match score |
| **Action Recommendation Precision** | ≥ 85% | Correct actions suggested |
| **Risk Classification Accuracy** | ≥ 95% | Correct risk level assigned |
| **Regression Rate** | < 2% | Tests that regress between builds |
| **False Positive Rate** | < 5% | LLM evaluator false positives |

### 7.2 Quality Gates by Release Type

| Release Type | Pass Rate Required | Regression Allowed |
|--------------|-------------------|-------------------|
| Hotfix | 95% | 0% |
| Patch | 95% | 1% |
| Minor | 95% | 2% |
| Major | 90% | 5% (with approval) |

### 7.3 Continuous Improvement

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Continuous Improvement Cycle                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐  │
│    │ Analyze │      │ Identify│      │ Update  │      │ Retrain │  │
│    │ Failed  │ ───▶ │ Root    │ ───▶ │ Ground  │ ───▶ │ or Fix  │  │
│    │ Tests   │      │ Cause   │      │ Truth   │      │ Model   │  │
│    └─────────┘      └─────────┘      └─────────┘      └─────────┘  │
│         ▲                                                  │       │
│         └──────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Roadmap

### 8.1 Phase Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Manual** | Weeks 1-4 | 115 manual test cases, test framework |
| **Phase 2: LLM-Assisted** | Weeks 5-8 | Evaluator integration, prompt tuning |
| **Phase 3: DevOps** | Weeks 9-12 | Pipeline integration, dashboards |

### 8.2 Detailed Milestones

#### Phase 1: Manual Ground Truth (Weeks 1-4)

| Week | Tasks |
|------|-------|
| Week 1 | Define test case schema, create templates, set up test directory |
| Week 2 | Create NL parsing test cases (50 cases) |
| Week 3 | Create action recommendation + risk classification tests (50 cases) |
| Week 4 | Peer review all cases, finalize ground truth dataset |

#### Phase 2: LLM-Assisted Evaluation (Weeks 5-8)

| Week | Tasks |
|------|-------|
| Week 5 | Design evaluation prompts, select evaluator model |
| Week 6 | Implement evaluator integration, test with sample cases |
| Week 7 | Calibrate scoring thresholds, handle edge cases |
| Week 8 | Validate evaluator accuracy vs human judgments |

#### Phase 3: DevOps Integration (Weeks 9-12)

| Week | Tasks |
|------|-------|
| Week 9 | Create pytest fixtures, integrate with test framework |
| Week 10 | Build Azure DevOps pipeline stage, configure gates |
| Week 11 | Create dashboards, set up alerting |
| Week 12 | Documentation, training, go-live |

### 8.3 Resource Requirements

| Role | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| SME (Test Case Author) | 40 hrs | 10 hrs | 5 hrs |
| ML Engineer | 10 hrs | 40 hrs | 20 hrs |
| DevOps Engineer | 5 hrs | 10 hrs | 40 hrs |
| QA Lead | 20 hrs | 20 hrs | 20 hrs |

---

## Appendix A: Evaluation Prompt Library

### A.1 NL Parsing Evaluation Prompt

```
You are evaluating a natural language to condition parser. 

Input: "{input}"
Expected Conditions: {expected}
Actual Conditions: {actual}

Evaluate if the actual output correctly captures the user's intent.
Consider:
- Are all conditions present?
- Are operators correct (less than vs greater than)?
- Are values correct?
- Is the logical operator (AND/OR) correct?

Score (0-100) and explain.
```

### A.2 Action Recommendation Evaluation Prompt

```
You are evaluating an action recommendation system for IT operations.

Scenario: {scenario}
Expected Actions: {expected_actions}
Suggested Actions: {actual_actions}

Evaluate if the suggested actions are appropriate:
- Are the action types correct?
- Is the priority order reasonable?
- Are risk levels correctly assigned?
- Are all necessary actions included?

Score (0-100) and explain.
```

---

## Appendix B: Sample Test Data Files

See `tests/ground_truth/data/` for complete test data files.
