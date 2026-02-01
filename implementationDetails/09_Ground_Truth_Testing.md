# 09 - Ground Truth Testing Implementation Guide

## Overview

This guide covers implementing the Ground Truth Testing framework for validating AI-generated responses and ensuring rule interpretation accuracy. This is critical for maintaining quality as the system evolves.

---

## Prerequisites

- LLM service implemented (see [08_LLM_Service.md](08_LLM_Service.md))
- Core service API complete
- pytest installed

---

## Step 1: Test Framework Architecture

📝 **PROMPT: Create Ground Truth Testing framework architecture**
```
Create a testing framework for validating LLM responses that:
- Stores expected input/output pairs in a test library
- Supports multiple test categories (rule interpretation, remediation, etc.)
- Uses LLM-as-judge for semantic similarity evaluation
- Generates detailed test reports
- Integrates with CI/CD pipelines
```

**Directory Structure:**

```
tests/
├── ground_truth/
│   ├── __init__.py
│   ├── framework.py        # Core testing framework
│   ├── evaluators.py       # LLM-based evaluation
│   ├── reporters.py        # Test reporting
│   ├── test_library/
│   │   ├── __init__.py
│   │   ├── rule_interpretation.json
│   │   ├── remediation.json
│   │   └── explanation.json
│   ├── fixtures/
│   │   └── sample_data.py
│   └── test_runner.py
└── conftest.py
```

---

## Step 2: Test Case Model

**File: `tests/ground_truth/models.py`**

```python
"""Models for Ground Truth Testing."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCategory(str, Enum):
    """Categories of ground truth tests."""
    RULE_INTERPRETATION = "rule_interpretation"
    REMEDIATION = "remediation"
    EXPLANATION = "explanation"
    SUMMARIZATION = "summarization"


class TestDifficulty(str, Enum):
    """Test difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestCase(BaseModel):
    """Single ground truth test case."""
    id: str
    category: TestCategory
    difficulty: TestDifficulty = TestDifficulty.MEDIUM
    name: str
    description: str
    
    # Input
    input_prompt: str
    input_context: Optional[Dict[str, Any]] = None
    
    # Expected output
    expected_output: Dict[str, Any]
    
    # Evaluation criteria
    required_fields: List[str] = Field(default_factory=list)
    semantic_match_fields: List[str] = Field(default_factory=list)
    exact_match_fields: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    author: Optional[str] = None


class TestResult(BaseModel):
    """Result of a single test execution."""
    test_id: str
    test_name: str
    category: TestCategory
    
    # Execution
    passed: bool
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float
    
    # Details
    actual_output: Dict[str, Any]
    expected_output: Dict[str, Any]
    
    # Evaluation scores
    overall_score: float  # 0.0 - 1.0
    field_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Errors
    error_message: Optional[str] = None
    evaluation_notes: List[str] = Field(default_factory=list)


class TestSuiteResult(BaseModel):
    """Results of a test suite execution."""
    suite_name: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    total_duration_ms: float
    
    # Summary
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    pass_rate: float
    
    # By category
    category_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Individual results
    results: List[TestResult]
    
    # Environment
    llm_provider: str
    llm_model: str
```

---

## Step 3: Core Testing Framework

**File: `tests/ground_truth/framework.py`**

```python
"""Core Ground Truth Testing framework."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

from .models import (
    TestCase,
    TestResult,
    TestSuiteResult,
    TestCategory,
)
from .evaluators import LLMEvaluator, RuleBasedEvaluator

logger = structlog.get_logger()


class TestLibrary:
    """Manages the ground truth test case library."""
    
    def __init__(self, library_path: Path):
        self.library_path = library_path
        self._tests: Dict[str, TestCase] = {}
        self._load_tests()
    
    def _load_tests(self):
        """Load all test cases from library."""
        for file_path in self.library_path.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                for test_data in data.get("tests", []):
                    test = TestCase(**test_data)
                    self._tests[test.id] = test
                    
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
    
    def get_test(self, test_id: str) -> Optional[TestCase]:
        """Get a single test case."""
        return self._tests.get(test_id)
    
    def get_tests_by_category(self, category: TestCategory) -> List[TestCase]:
        """Get all tests in a category."""
        return [t for t in self._tests.values() if t.category == category]
    
    def get_tests_by_tags(self, tags: List[str]) -> List[TestCase]:
        """Get tests matching any of the tags."""
        return [
            t for t in self._tests.values()
            if any(tag in t.tags for tag in tags)
        ]
    
    def get_all_tests(self) -> List[TestCase]:
        """Get all test cases."""
        return list(self._tests.values())
    
    @property
    def test_count(self) -> int:
        """Total number of tests."""
        return len(self._tests)


class GroundTruthRunner:
    """Executes ground truth tests."""
    
    def __init__(
        self,
        test_library: TestLibrary,
        llm_evaluator: LLMEvaluator,
        rule_evaluator: RuleBasedEvaluator,
    ):
        self.library = test_library
        self.llm_evaluator = llm_evaluator
        self.rule_evaluator = rule_evaluator
        
        # Test handlers by category
        self._handlers: Dict[TestCategory, Callable] = {}
    
    def register_handler(
        self,
        category: TestCategory,
        handler: Callable[[TestCase], Any],
    ):
        """Register a handler for a test category."""
        self._handlers[category] = handler
    
    async def run_test(self, test: TestCase) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()
        
        try:
            # Get handler for this category
            handler = self._handlers.get(test.category)
            if not handler:
                raise ValueError(f"No handler for category: {test.category}")
            
            # Execute the test
            actual_output = await handler(test)
            
            # Evaluate results
            evaluation = await self._evaluate_output(
                test=test,
                actual_output=actual_output,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                test_id=test.id,
                test_name=test.name,
                category=test.category,
                passed=evaluation["passed"],
                duration_ms=duration_ms,
                actual_output=actual_output,
                expected_output=test.expected_output,
                overall_score=evaluation["overall_score"],
                field_scores=evaluation.get("field_scores", {}),
                evaluation_notes=evaluation.get("notes", []),
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Test {test.id} failed with error: {e}")
            
            return TestResult(
                test_id=test.id,
                test_name=test.name,
                category=test.category,
                passed=False,
                duration_ms=duration_ms,
                actual_output={},
                expected_output=test.expected_output,
                overall_score=0.0,
                error_message=str(e),
            )
    
    async def run_suite(
        self,
        tests: Optional[List[TestCase]] = None,
        category: Optional[TestCategory] = None,
        tags: Optional[List[str]] = None,
        parallel: bool = True,
    ) -> TestSuiteResult:
        """Run a suite of tests."""
        start_time = time.time()
        
        # Select tests
        if tests is None:
            if category:
                tests = self.library.get_tests_by_category(category)
            elif tags:
                tests = self.library.get_tests_by_tags(tags)
            else:
                tests = self.library.get_all_tests()
        
        # Execute tests
        if parallel:
            results = await asyncio.gather(
                *[self.run_test(test) for test in tests],
                return_exceptions=True,
            )
            # Handle any exceptions
            results = [
                r if isinstance(r, TestResult) else TestResult(
                    test_id="error",
                    test_name="Unknown",
                    category=TestCategory.RULE_INTERPRETATION,
                    passed=False,
                    duration_ms=0,
                    actual_output={},
                    expected_output={},
                    overall_score=0.0,
                    error_message=str(r),
                )
                for r in results
            ]
        else:
            results = []
            for test in tests:
                result = await self.run_test(test)
                results.append(result)
        
        # Calculate statistics
        total_duration = (time.time() - start_time) * 1000
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        
        # Group by category
        category_results = {}
        for cat in TestCategory:
            cat_results = [r for r in results if r.category == cat]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r.passed)
                category_results[cat.value] = {
                    "total": len(cat_results),
                    "passed": cat_passed,
                    "failed": len(cat_results) - cat_passed,
                    "pass_rate": cat_passed / len(cat_results) if cat_results else 0,
                }
        
        return TestSuiteResult(
            suite_name="Ground Truth Tests",
            total_duration_ms=total_duration,
            total_tests=len(tests),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=0,
            pass_rate=passed / len(tests) if tests else 0,
            category_results=category_results,
            results=results,
            llm_provider="openai",  # Get from config
            llm_model="gpt-4",
        )
    
    async def _evaluate_output(
        self,
        test: TestCase,
        actual_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate actual output against expected."""
        notes = []
        field_scores = {}
        
        # Check required fields
        for field in test.required_fields:
            if field not in actual_output:
                notes.append(f"Missing required field: {field}")
                field_scores[field] = 0.0
            else:
                field_scores[field] = 1.0
        
        # Check exact match fields
        for field in test.exact_match_fields:
            expected = test.expected_output.get(field)
            actual = actual_output.get(field)
            
            if expected == actual:
                field_scores[field] = 1.0
            else:
                field_scores[field] = 0.0
                notes.append(f"Exact match failed for {field}: expected {expected}, got {actual}")
        
        # Check semantic match fields using LLM
        for field in test.semantic_match_fields:
            expected = test.expected_output.get(field)
            actual = actual_output.get(field)
            
            if expected and actual:
                score = await self.llm_evaluator.evaluate_semantic_similarity(
                    expected=str(expected),
                    actual=str(actual),
                    context=test.description,
                )
                field_scores[field] = score
                
                if score < 0.7:
                    notes.append(f"Semantic match score low for {field}: {score:.2f}")
        
        # Calculate overall score
        if field_scores:
            overall_score = sum(field_scores.values()) / len(field_scores)
        else:
            overall_score = 1.0 if not notes else 0.0
        
        # Determine pass/fail
        passed = overall_score >= 0.8 and all(
            field_scores.get(f, 0) > 0 for f in test.required_fields
        )
        
        return {
            "passed": passed,
            "overall_score": overall_score,
            "field_scores": field_scores,
            "notes": notes,
        }
```

---

## Step 4: LLM-Based Evaluator

📝 **PROMPT: Create LLM-based test evaluator**
```
Create an evaluator that uses LLM (GPT-4) to:
- Assess semantic similarity between expected and actual outputs
- Evaluate correctness of rule interpretations
- Score remediation suggestion quality
- Provide detailed feedback on discrepancies
```

**File: `tests/ground_truth/evaluators.py`**

```python
"""Evaluators for Ground Truth Testing."""

import json
from typing import Any, Dict, Optional

from llm_service.providers import LLMProviderFactory


class LLMEvaluator:
    """LLM-based evaluation for semantic similarity."""
    
    SIMILARITY_PROMPT = """You are evaluating the similarity between an expected output and an actual output.

Expected Output:
{expected}

Actual Output:
{actual}

Context: {context}

Evaluate on a scale of 0.0 to 1.0 how semantically similar the outputs are.
Consider:
1. Do they convey the same meaning?
2. Are the key concepts preserved?
3. Would both outputs lead to the same action/result?

Respond with ONLY a JSON object:
{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}"""

    RULE_EVALUATION_PROMPT = """You are evaluating if a rule interpretation is correct.

Original Natural Language: {natural_language}

Expected Rule Structure:
{expected_rule}

Actual Rule Structure:
{actual_rule}

Evaluate:
1. Is the entity_type correct? (0 or 1)
2. Are the conditions semantically equivalent? (0.0-1.0)
3. Are the operators appropriate? (0.0-1.0)
4. Would both rules match the same set of entities? (0.0-1.0)

Respond with ONLY a JSON object:
{{
    "entity_type_correct": <0 or 1>,
    "conditions_score": <float>,
    "operators_score": <float>,
    "equivalence_score": <float>,
    "overall_score": <float>,
    "issues": [<list of issues if any>]
}}"""

    def __init__(self):
        self.provider = LLMProviderFactory.get_available_provider()
    
    async def evaluate_semantic_similarity(
        self,
        expected: str,
        actual: str,
        context: str = "",
    ) -> float:
        """
        Evaluate semantic similarity between expected and actual.
        
        Returns a score from 0.0 to 1.0.
        """
        prompt = self.SIMILARITY_PROMPT.format(
            expected=expected,
            actual=actual,
            context=context,
        )
        
        try:
            response = await self.provider.generate(prompt)
            result = json.loads(response)
            return float(result.get("score", 0.0))
        except Exception:
            # Fallback to simple comparison
            return 1.0 if expected.lower() == actual.lower() else 0.0
    
    async def evaluate_rule_interpretation(
        self,
        natural_language: str,
        expected_rule: Dict[str, Any],
        actual_rule: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate if a rule interpretation is correct.
        
        Returns detailed evaluation scores.
        """
        prompt = self.RULE_EVALUATION_PROMPT.format(
            natural_language=natural_language,
            expected_rule=json.dumps(expected_rule, indent=2),
            actual_rule=json.dumps(actual_rule, indent=2),
        )
        
        try:
            response = await self.provider.generate(prompt)
            return json.loads(response)
        except Exception as e:
            return {
                "entity_type_correct": 0,
                "conditions_score": 0.0,
                "operators_score": 0.0,
                "equivalence_score": 0.0,
                "overall_score": 0.0,
                "issues": [str(e)],
            }
    
    async def evaluate_remediation(
        self,
        scan_results: Dict[str, Any],
        expected_actions: list,
        actual_actions: list,
    ) -> Dict[str, Any]:
        """Evaluate remediation suggestion quality."""
        prompt = f"""Evaluate these remediation suggestions:

Scan Results Summary:
{json.dumps(scan_results, indent=2)}

Expected Actions:
{json.dumps(expected_actions, indent=2)}

Actual Suggested Actions:
{json.dumps(actual_actions, indent=2)}

Evaluate:
1. Are the action types appropriate? (0.0-1.0)
2. Are the priorities reasonable? (0.0-1.0)
3. Would the actions address the issues? (0.0-1.0)
4. Are there any missing critical actions? (list)

Respond with JSON only."""

        try:
            response = await self.provider.generate(prompt)
            return json.loads(response)
        except Exception:
            return {"score": 0.0, "error": "Evaluation failed"}


class RuleBasedEvaluator:
    """Rule-based evaluation for structured outputs."""
    
    def evaluate_exact_match(
        self,
        expected: Any,
        actual: Any,
    ) -> bool:
        """Check for exact match."""
        return expected == actual
    
    def evaluate_contains(
        self,
        expected_items: list,
        actual_items: list,
    ) -> float:
        """Check if all expected items are present."""
        if not expected_items:
            return 1.0
        
        found = sum(1 for item in expected_items if item in actual_items)
        return found / len(expected_items)
    
    def evaluate_json_structure(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        required_keys: list,
    ) -> Dict[str, Any]:
        """Evaluate JSON structure match."""
        results = {
            "missing_keys": [],
            "type_mismatches": [],
            "score": 1.0,
        }
        
        # Check required keys
        for key in required_keys:
            if key not in actual:
                results["missing_keys"].append(key)
        
        # Check types match
        for key in expected:
            if key in actual:
                if type(expected[key]) != type(actual[key]):
                    results["type_mismatches"].append(key)
        
        # Calculate score
        total_checks = len(required_keys) + len(expected)
        failures = len(results["missing_keys"]) + len(results["type_mismatches"])
        results["score"] = max(0, (total_checks - failures) / total_checks)
        
        return results
```

---

## Step 5: Test Case Library

**File: `tests/ground_truth/test_library/rule_interpretation.json`**

```json
{
    "category": "rule_interpretation",
    "description": "Tests for natural language to rule conversion",
    "tests": [
        {
            "id": "rule_001",
            "category": "rule_interpretation",
            "difficulty": "easy",
            "name": "Simple disk space rule",
            "description": "Basic rule for low disk space detection",
            "input_prompt": "Find devices with less than 10GB free disk space",
            "expected_output": {
                "entity_type": "devices",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "free_disk_gb",
                            "operator": "lt",
                            "value": 10
                        }
                    ]
                },
                "suggested_name": "Low Disk Space Devices"
            },
            "required_fields": ["entity_type", "conditions"],
            "semantic_match_fields": ["suggested_name"],
            "exact_match_fields": ["entity_type"],
            "tags": ["disk", "simple"]
        },
        {
            "id": "rule_002",
            "category": "rule_interpretation",
            "difficulty": "medium",
            "name": "OS and disk compound rule",
            "description": "Rule combining OS filter with disk space",
            "input_prompt": "Find Windows 10 devices with less than 10GB free disk space",
            "expected_output": {
                "entity_type": "devices",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "operating_system",
                            "operator": "contains",
                            "value": "Windows 10"
                        },
                        {
                            "field": "free_disk_gb",
                            "operator": "lt",
                            "value": 10
                        }
                    ]
                }
            },
            "required_fields": ["entity_type", "conditions"],
            "exact_match_fields": ["entity_type"],
            "tags": ["os", "disk", "compound"]
        },
        {
            "id": "rule_003",
            "category": "rule_interpretation",
            "difficulty": "medium",
            "name": "Inactive devices rule",
            "description": "Rule for finding inactive devices",
            "input_prompt": "Find devices that haven't been active in the last 30 days",
            "expected_output": {
                "entity_type": "devices",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "last_active_days",
                            "operator": "gt",
                            "value": 30
                        }
                    ]
                }
            },
            "required_fields": ["entity_type", "conditions"],
            "tags": ["inactive", "time-based"]
        },
        {
            "id": "rule_004",
            "category": "rule_interpretation",
            "difficulty": "hard",
            "name": "Complex OR rule",
            "description": "Rule with OR logic for multiple conditions",
            "input_prompt": "Find devices with either low disk space (under 5GB) or missing critical patches",
            "expected_output": {
                "entity_type": "devices",
                "conditions": {
                    "logic": "OR",
                    "conditions": [
                        {
                            "field": "free_disk_gb",
                            "operator": "lt",
                            "value": 5
                        },
                        {
                            "field": "missing_critical_patches",
                            "operator": "gt",
                            "value": 0
                        }
                    ]
                }
            },
            "required_fields": ["entity_type", "conditions"],
            "tags": ["or-logic", "complex"]
        },
        {
            "id": "rule_005",
            "category": "rule_interpretation",
            "difficulty": "hard",
            "name": "Nested conditions rule",
            "description": "Rule with nested AND/OR conditions",
            "input_prompt": "Find Windows devices that have either low disk space or are Dell laptops missing patches",
            "expected_output": {
                "entity_type": "devices",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "operating_system",
                            "operator": "contains",
                            "value": "Windows"
                        },
                        {
                            "logic": "OR",
                            "conditions": [
                                {
                                    "field": "free_disk_gb",
                                    "operator": "lt",
                                    "value": 10
                                },
                                {
                                    "logic": "AND",
                                    "conditions": [
                                        {
                                            "field": "manufacturer",
                                            "operator": "eq",
                                            "value": "Dell"
                                        },
                                        {
                                            "field": "missing_critical_patches",
                                            "operator": "gt",
                                            "value": 0
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            },
            "required_fields": ["entity_type", "conditions"],
            "tags": ["nested", "complex", "advanced"]
        },
        {
            "id": "rule_006",
            "category": "rule_interpretation",
            "difficulty": "easy",
            "name": "Application vulnerability rule",
            "description": "Rule for finding vulnerable applications",
            "input_prompt": "Find applications with known vulnerabilities",
            "expected_output": {
                "entity_type": "applications",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "field": "cve_count",
                            "operator": "gt",
                            "value": 0
                        }
                    ]
                }
            },
            "required_fields": ["entity_type", "conditions"],
            "exact_match_fields": ["entity_type"],
            "tags": ["applications", "security"]
        }
    ]
}
```

---

## Step 6: Test Runner

**File: `tests/ground_truth/test_runner.py`**

```python
"""Ground Truth Test Runner."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .framework import TestLibrary, GroundTruthRunner
from .evaluators import LLMEvaluator, RuleBasedEvaluator
from .reporters import HTMLReporter, JUnitReporter
from .models import TestCategory


console = Console()


async def run_ground_truth_tests(
    category: Optional[str] = None,
    tags: Optional[list] = None,
    output_format: str = "console",
    output_file: Optional[str] = None,
):
    """Run ground truth tests."""
    # Initialize
    library_path = Path(__file__).parent / "test_library"
    library = TestLibrary(library_path)
    
    llm_evaluator = LLMEvaluator()
    rule_evaluator = RuleBasedEvaluator()
    
    runner = GroundTruthRunner(library, llm_evaluator, rule_evaluator)
    
    # Register test handlers
    from llm_service.service import LLMService
    llm_service = LLMService()
    
    async def rule_interpretation_handler(test):
        """Handler for rule interpretation tests."""
        result = await llm_service.interpret_rule(test.input_prompt)
        return result
    
    runner.register_handler(
        TestCategory.RULE_INTERPRETATION,
        rule_interpretation_handler,
    )
    
    # Run tests
    console.print("\n[bold blue]Running Ground Truth Tests[/bold blue]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running tests...", total=None)
        
        cat = TestCategory(category) if category else None
        results = await runner.run_suite(category=cat, tags=tags)
        
        progress.update(task, completed=True)
    
    # Output results
    if output_format == "console":
        _print_console_results(results)
    elif output_format == "html":
        reporter = HTMLReporter()
        report_path = output_file or "ground_truth_report.html"
        reporter.generate(results, report_path)
        console.print(f"\nHTML report saved to: {report_path}")
    elif output_format == "junit":
        reporter = JUnitReporter()
        report_path = output_file or "ground_truth_results.xml"
        reporter.generate(results, report_path)
        console.print(f"\nJUnit report saved to: {report_path}")
    
    return results


def _print_console_results(results):
    """Print results to console."""
    # Summary
    console.print("\n[bold]Summary[/bold]")
    console.print(f"Total Tests: {results.total_tests}")
    console.print(f"Passed: [green]{results.passed_tests}[/green]")
    console.print(f"Failed: [red]{results.failed_tests}[/red]")
    console.print(f"Pass Rate: {results.pass_rate:.1%}")
    console.print(f"Duration: {results.total_duration_ms:.0f}ms\n")
    
    # By category
    if results.category_results:
        console.print("[bold]By Category[/bold]")
        cat_table = Table()
        cat_table.add_column("Category")
        cat_table.add_column("Total")
        cat_table.add_column("Passed")
        cat_table.add_column("Failed")
        cat_table.add_column("Pass Rate")
        
        for cat, data in results.category_results.items():
            cat_table.add_row(
                cat,
                str(data["total"]),
                str(data["passed"]),
                str(data["failed"]),
                f"{data['pass_rate']:.1%}",
            )
        
        console.print(cat_table)
    
    # Failed tests details
    failed = [r for r in results.results if not r.passed]
    if failed:
        console.print("\n[bold red]Failed Tests[/bold red]")
        for result in failed:
            console.print(f"\n[red]✗[/red] {result.test_name} ({result.test_id})")
            console.print(f"  Score: {result.overall_score:.2f}")
            if result.error_message:
                console.print(f"  Error: {result.error_message}")
            for note in result.evaluation_notes:
                console.print(f"  • {note}")


@click.command()
@click.option("--category", "-c", help="Test category to run")
@click.option("--tag", "-t", multiple=True, help="Tags to filter tests")
@click.option("--format", "-f", "output_format", default="console", 
              type=click.Choice(["console", "html", "junit"]))
@click.option("--output", "-o", "output_file", help="Output file path")
def main(category, tag, output_format, output_file):
    """Run ground truth tests."""
    tags = list(tag) if tag else None
    results = asyncio.run(
        run_ground_truth_tests(category, tags, output_format, output_file)
    )
    
    # Exit with error code if tests failed
    sys.exit(0 if results.passed_tests == results.total_tests else 1)


if __name__ == "__main__":
    main()
```

---

## Step 7: pytest Integration

**File: `tests/test_ground_truth.py`**

```python
"""Pytest integration for Ground Truth Tests."""

import pytest
import asyncio
from pathlib import Path

from tests.ground_truth.framework import TestLibrary, GroundTruthRunner
from tests.ground_truth.evaluators import LLMEvaluator, RuleBasedEvaluator
from tests.ground_truth.models import TestCategory


@pytest.fixture
def test_library():
    """Load test library."""
    library_path = Path(__file__).parent / "ground_truth" / "test_library"
    return TestLibrary(library_path)


@pytest.fixture
def runner(test_library):
    """Create test runner."""
    llm_evaluator = LLMEvaluator()
    rule_evaluator = RuleBasedEvaluator()
    return GroundTruthRunner(test_library, llm_evaluator, rule_evaluator)


class TestRuleInterpretation:
    """Ground truth tests for rule interpretation."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_id", [
        "rule_001",  # Simple disk space
        "rule_002",  # OS and disk compound
        "rule_003",  # Inactive devices
    ])
    async def test_basic_rules(self, runner, test_library, test_id):
        """Test basic rule interpretations."""
        test = test_library.get_test(test_id)
        assert test is not None, f"Test {test_id} not found"
        
        # Register handler
        from llm_service.service import LLMService
        llm_service = LLMService()
        
        async def handler(test):
            return await llm_service.interpret_rule(test.input_prompt)
        
        runner.register_handler(TestCategory.RULE_INTERPRETATION, handler)
        
        result = await runner.run_test(test)
        
        assert result.passed, f"Test failed: {result.evaluation_notes}"
        assert result.overall_score >= 0.8, f"Score too low: {result.overall_score}"
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_id", [
        "rule_004",  # Complex OR rule
        "rule_005",  # Nested conditions
    ])
    async def test_complex_rules(self, runner, test_library, test_id):
        """Test complex rule interpretations."""
        test = test_library.get_test(test_id)
        assert test is not None
        
        # Setup and run similar to above
        pass


class TestGroundTruthSuite:
    """Full ground truth test suite."""
    
    @pytest.mark.asyncio
    async def test_full_suite(self, runner):
        """Run full ground truth test suite."""
        results = await runner.run_suite()
        
        # Assert minimum pass rate
        assert results.pass_rate >= 0.9, f"Pass rate too low: {results.pass_rate}"
        
        # Assert no critical failures
        critical_failures = [
            r for r in results.results
            if not r.passed and r.overall_score == 0
        ]
        assert len(critical_failures) == 0, f"Critical failures: {critical_failures}"


# CI/CD marker for running only ground truth tests
def pytest_collection_modifyitems(items):
    """Add markers to ground truth tests."""
    for item in items:
        if "ground_truth" in item.nodeid:
            item.add_marker(pytest.mark.ground_truth)
```

---

## Step 8: CI/CD Integration

**File: `.github/workflows/ground-truth.yml`**

```yaml
name: Ground Truth Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  ground-truth-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run Ground Truth Tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m tests.ground_truth.test_runner \
            --format junit \
            --output ground_truth_results.xml
      
      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: ground_truth_results.xml
      
      - name: Generate HTML Report
        if: always()
        run: |
          python -m tests.ground_truth.test_runner \
            --format html \
            --output ground_truth_report.html
      
      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: ground-truth-report
          path: ground_truth_report.html
      
      - name: Check Pass Rate
        run: |
          PASS_RATE=$(jq '.pass_rate' ground_truth_summary.json)
          if (( $(echo "$PASS_RATE < 0.9" | bc -l) )); then
            echo "Pass rate below threshold: $PASS_RATE"
            exit 1
          fi
```

---

## Verification

### Run Tests Locally

```powershell
# Run all ground truth tests
python -m tests.ground_truth.test_runner

# Run specific category
python -m tests.ground_truth.test_runner --category rule_interpretation

# Generate HTML report
python -m tests.ground_truth.test_runner --format html --output report.html

# Run via pytest
pytest tests/test_ground_truth.py -v
```

### Add New Test Cases

```python
# Add to test_library/rule_interpretation.json
{
    "id": "rule_007",
    "category": "rule_interpretation",
    "difficulty": "medium",
    "name": "Your new test",
    "description": "Description of what this tests",
    "input_prompt": "Natural language input",
    "expected_output": {
        "entity_type": "devices",
        "conditions": {...}
    },
    "required_fields": ["entity_type", "conditions"],
    "tags": ["your-tag"]
}
```

---

## Common Issues

### Issue: LLM responses vary between runs

**Solution:** Use lower temperature (0.1) and add retry logic with score averaging

### Issue: Tests timeout

**Solution:** Increase timeout and run tests in parallel with rate limiting

### Issue: Semantic evaluation too strict/lenient

**Solution:** Tune the similarity threshold and add more specific evaluation criteria

---

## Next Steps

→ [10_ServiceNow_Connector.md](10_ServiceNow_Connector.md) - Implement ServiceNow integration

---

**Checkpoint:** You should now have:
- [ ] Test library with 6+ rule interpretation tests
- [ ] Framework running and evaluating tests
- [ ] LLM-based semantic evaluation working
- [ ] Console and HTML reports generating
- [ ] CI/CD pipeline configured
- [ ] Pass rate threshold enforced
