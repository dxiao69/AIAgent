"""
Ground Truth Test Runner for ITOA Agent

This module provides the infrastructure for running ground truth tests
against AI/LLM components including NL parsing, action recommendations,
risk classification, and summarization.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import pytest


class EvaluationMode(Enum):
    """Evaluation modes for ground truth testing."""
    EXACT = "exact"
    SEMANTIC = "semantic"
    PARTIAL = "partial"
    RANGE = "range"


class TestCategory(Enum):
    """Categories of ground truth tests."""
    NL_PARSING = "nl_parsing"
    ACTION_RECOMMENDATIONS = "action_recommendations"
    RISK_CLASSIFICATION = "risk_classification"
    SUMMARIZATION = "summarization"


@dataclass
class TestCase:
    """Represents a single ground truth test case."""
    test_id: str
    category: str
    description: str
    input: Any
    expected_output: Any
    evaluation_mode: EvaluationMode
    acceptable_variations: Optional[List[Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """Result of a ground truth test evaluation."""
    test_id: str
    category: str
    passed: bool
    actual_output: Any
    expected_output: Any
    confidence_score: float
    evaluation_details: Dict[str, Any]
    error_message: Optional[str] = None


class GroundTruthTestLoader:
    """Loads ground truth test cases from JSON files."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the test loader.
        
        Args:
            data_dir: Path to the ground truth data directory.
                     Defaults to tests/ground_truth/data/
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
    
    def load_test_cases(self, category: TestCategory) -> List[TestCase]:
        """
        Load all test cases for a specific category.
        
        Args:
            category: The test category to load.
            
        Returns:
            List of TestCase objects.
        """
        category_dir = self.data_dir / category.value
        test_cases = []
        
        if not category_dir.exists():
            return test_cases
        
        for json_file in category_dir.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Handle both single object and array of objects
            if isinstance(data, list):
                for item in data:
                    test_cases.append(self._parse_test_case(item))
            else:
                test_cases.append(self._parse_test_case(data))
        
        return test_cases
    
    def _parse_test_case(self, data: Dict[str, Any]) -> TestCase:
        """Parse a dictionary into a TestCase object."""
        return TestCase(
            test_id=data["test_id"],
            category=data["category"],
            description=data.get("description", ""),
            input=data["input"],
            expected_output=data["expected_output"],
            evaluation_mode=EvaluationMode(data.get("evaluation_mode", "exact")),
            acceptable_variations=data.get("acceptable_variations"),
            metadata=data.get("metadata")
        )
    
    def load_all_test_cases(self) -> Dict[TestCategory, List[TestCase]]:
        """
        Load all test cases across all categories.
        
        Returns:
            Dictionary mapping categories to their test cases.
        """
        all_cases = {}
        for category in TestCategory:
            cases = self.load_test_cases(category)
            if cases:
                all_cases[category] = cases
        return all_cases


class BaseEvaluator:
    """Base class for ground truth evaluators."""
    
    def evaluate(self, actual: Any, expected: Any, mode: EvaluationMode, 
                 acceptable_variations: List[Any] = None) -> TestResult:
        """
        Evaluate actual output against expected output.
        
        Args:
            actual: The actual output from the system.
            expected: The expected output from ground truth.
            mode: The evaluation mode to use.
            acceptable_variations: List of acceptable alternative outputs.
            
        Returns:
            TestResult with evaluation details.
        """
        raise NotImplementedError("Subclasses must implement evaluate()")


class ExactEvaluator(BaseEvaluator):
    """Evaluator for exact match comparisons."""
    
    def evaluate(self, actual: Any, expected: Any, mode: EvaluationMode,
                 acceptable_variations: List[Any] = None) -> Dict[str, Any]:
        """
        Perform exact match evaluation.
        
        Returns dictionary with:
            - passed: bool
            - confidence_score: float (100 if match, 0 if not)
            - details: comparison details
        """
        if actual == expected:
            return {
                "passed": True,
                "confidence_score": 100.0,
                "details": {"match_type": "exact"}
            }
        
        # Check acceptable variations
        if acceptable_variations:
            for variation in acceptable_variations:
                if actual == variation:
                    return {
                        "passed": True,
                        "confidence_score": 95.0,
                        "details": {
                            "match_type": "variation",
                            "matched_variation": variation
                        }
                    }
        
        return {
            "passed": False,
            "confidence_score": 0.0,
            "details": {
                "match_type": "no_match",
                "actual": actual,
                "expected": expected
            }
        }


class SemanticEvaluator(BaseEvaluator):
    """
    Evaluator for semantic equivalence using LLM.
    
    This evaluator uses GPT-4 or equivalent to determine if two outputs
    are semantically equivalent, even if they differ in wording.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the semantic evaluator.
        
        Args:
            llm_client: LLM client for semantic evaluation.
                       If None, will be initialized from settings.
        """
        self.llm_client = llm_client
        self._evaluation_prompt_template = """
You are evaluating whether an AI system's actual output is semantically equivalent 
to the expected ground truth output.

EXPECTED OUTPUT:
{expected}

ACTUAL OUTPUT:
{actual}

ACCEPTABLE VARIATIONS (if any):
{variations}

Please evaluate and respond with a JSON object containing:
1. "is_equivalent": boolean - Are the outputs semantically equivalent?
2. "confidence_score": number 0-100 - How confident are you in this assessment?
3. "reasoning": string - Brief explanation of your assessment
4. "key_differences": array - List any significant differences (empty if equivalent)

Focus on meaning, not exact wording. Minor phrasing differences should still be 
considered equivalent if the core meaning is preserved.
"""
    
    def evaluate(self, actual: Any, expected: Any, mode: EvaluationMode,
                 acceptable_variations: List[Any] = None) -> Dict[str, Any]:
        """
        Perform semantic evaluation using LLM.
        
        In production, this calls the LLM. For testing without LLM,
        it falls back to a simple heuristic comparison.
        """
        # TODO: Integrate with actual LLM client
        # For now, provide a placeholder implementation
        
        if self.llm_client is None:
            # Fallback to heuristic comparison
            return self._heuristic_evaluation(actual, expected, acceptable_variations)
        
        # LLM-based evaluation (to be implemented)
        prompt = self._evaluation_prompt_template.format(
            expected=json.dumps(expected, indent=2),
            actual=json.dumps(actual, indent=2),
            variations=json.dumps(acceptable_variations, indent=2) if acceptable_variations else "None"
        )
        
        # TODO: Call LLM and parse response
        # response = self.llm_client.complete(prompt)
        # return self._parse_llm_response(response)
        
        return self._heuristic_evaluation(actual, expected, acceptable_variations)
    
    def _heuristic_evaluation(self, actual: Any, expected: Any,
                              acceptable_variations: List[Any] = None) -> Dict[str, Any]:
        """Simple heuristic evaluation when LLM is not available."""
        # Convert to strings for comparison
        actual_str = str(actual).lower()
        expected_str = str(expected).lower()
        
        # Check for exact match
        if actual_str == expected_str:
            return {
                "passed": True,
                "confidence_score": 100.0,
                "details": {"match_type": "exact", "method": "heuristic"}
            }
        
        # Check for high overlap (simple word-based similarity)
        actual_words = set(actual_str.split())
        expected_words = set(expected_str.split())
        
        if actual_words and expected_words:
            overlap = len(actual_words & expected_words)
            total = len(actual_words | expected_words)
            similarity = (overlap / total) * 100
            
            return {
                "passed": similarity >= 70,
                "confidence_score": similarity,
                "details": {
                    "match_type": "heuristic_similarity",
                    "similarity_score": similarity,
                    "method": "word_overlap",
                    "note": "LLM evaluation not available, using heuristic"
                }
            }
        
        return {
            "passed": False,
            "confidence_score": 0.0,
            "details": {"match_type": "no_match", "method": "heuristic"}
        }


class PartialEvaluator(BaseEvaluator):
    """Evaluator for partial match comparisons (key fields must match)."""
    
    def __init__(self, required_fields: List[str] = None):
        """
        Initialize partial evaluator.
        
        Args:
            required_fields: List of field names that must match exactly.
        """
        self.required_fields = required_fields or []
    
    def evaluate(self, actual: Any, expected: Any, mode: EvaluationMode,
                 acceptable_variations: List[Any] = None) -> Dict[str, Any]:
        """
        Evaluate that required fields match exactly.
        """
        if not isinstance(actual, dict) or not isinstance(expected, dict):
            return {
                "passed": False,
                "confidence_score": 0.0,
                "details": {"error": "Both actual and expected must be dictionaries"}
            }
        
        matched_fields = []
        mismatched_fields = []
        
        # Check required fields
        fields_to_check = self.required_fields if self.required_fields else expected.keys()
        
        for field in fields_to_check:
            if field in actual and field in expected:
                if actual[field] == expected[field]:
                    matched_fields.append(field)
                else:
                    mismatched_fields.append({
                        "field": field,
                        "actual": actual[field],
                        "expected": expected[field]
                    })
            elif field in expected:
                mismatched_fields.append({
                    "field": field,
                    "actual": None,
                    "expected": expected[field]
                })
        
        total_fields = len(fields_to_check)
        match_score = (len(matched_fields) / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "passed": len(mismatched_fields) == 0,
            "confidence_score": match_score,
            "details": {
                "matched_fields": matched_fields,
                "mismatched_fields": mismatched_fields,
                "total_required_fields": total_fields
            }
        }


class RangeEvaluator(BaseEvaluator):
    """Evaluator for numeric range comparisons."""
    
    def __init__(self, tolerance_percent: float = 10.0):
        """
        Initialize range evaluator.
        
        Args:
            tolerance_percent: Acceptable percentage deviation (default 10%).
        """
        self.tolerance_percent = tolerance_percent
    
    def evaluate(self, actual: Any, expected: Any, mode: EvaluationMode,
                 acceptable_variations: List[Any] = None) -> Dict[str, Any]:
        """
        Evaluate that numeric value is within acceptable range.
        """
        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (ValueError, TypeError):
            return {
                "passed": False,
                "confidence_score": 0.0,
                "details": {"error": "Values must be numeric"}
            }
        
        if expected_num == 0:
            # Handle zero case
            passed = actual_num == 0
            return {
                "passed": passed,
                "confidence_score": 100.0 if passed else 0.0,
                "details": {"expected": 0, "actual": actual_num}
            }
        
        deviation = abs(actual_num - expected_num) / abs(expected_num) * 100
        passed = deviation <= self.tolerance_percent
        
        # Calculate confidence based on how close the value is
        confidence = max(0, 100 - deviation)
        
        return {
            "passed": passed,
            "confidence_score": confidence,
            "details": {
                "actual_value": actual_num,
                "expected_value": expected_num,
                "deviation_percent": deviation,
                "tolerance_percent": self.tolerance_percent
            }
        }


class GroundTruthTestRunner:
    """
    Main test runner for ground truth tests.
    
    Orchestrates loading test cases, running evaluations, and
    generating reports.
    """
    
    def __init__(self, data_dir: str = None, llm_client=None):
        """
        Initialize the test runner.
        
        Args:
            data_dir: Path to ground truth data directory.
            llm_client: LLM client for semantic evaluation.
        """
        self.loader = GroundTruthTestLoader(data_dir)
        
        # Initialize evaluators
        self.evaluators = {
            EvaluationMode.EXACT: ExactEvaluator(),
            EvaluationMode.SEMANTIC: SemanticEvaluator(llm_client),
            EvaluationMode.PARTIAL: PartialEvaluator(),
            EvaluationMode.RANGE: RangeEvaluator(),
        }
        
        self.results: List[TestResult] = []
    
    def run_single_test(self, test_case: TestCase, 
                        get_actual_output: callable) -> TestResult:
        """
        Run a single ground truth test.
        
        Args:
            test_case: The test case to run.
            get_actual_output: Callable that takes input and returns actual output.
            
        Returns:
            TestResult with evaluation details.
        """
        try:
            # Get actual output from system
            actual_output = get_actual_output(test_case.input)
            
            # Get appropriate evaluator
            evaluator = self.evaluators.get(test_case.evaluation_mode)
            if evaluator is None:
                evaluator = self.evaluators[EvaluationMode.EXACT]
            
            # Evaluate
            eval_result = evaluator.evaluate(
                actual=actual_output,
                expected=test_case.expected_output,
                mode=test_case.evaluation_mode,
                acceptable_variations=test_case.acceptable_variations
            )
            
            result = TestResult(
                test_id=test_case.test_id,
                category=test_case.category,
                passed=eval_result["passed"],
                actual_output=actual_output,
                expected_output=test_case.expected_output,
                confidence_score=eval_result["confidence_score"],
                evaluation_details=eval_result["details"]
            )
            
        except Exception as e:
            result = TestResult(
                test_id=test_case.test_id,
                category=test_case.category,
                passed=False,
                actual_output=None,
                expected_output=test_case.expected_output,
                confidence_score=0.0,
                evaluation_details={},
                error_message=str(e)
            )
        
        self.results.append(result)
        return result
    
    def run_category_tests(self, category: TestCategory,
                           get_actual_output: callable) -> List[TestResult]:
        """
        Run all tests for a specific category.
        
        Args:
            category: The test category to run.
            get_actual_output: Callable for getting actual outputs.
            
        Returns:
            List of TestResults for the category.
        """
        test_cases = self.loader.load_test_cases(category)
        results = []
        
        for test_case in test_cases:
            result = self.run_single_test(test_case, get_actual_output)
            results.append(result)
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all test results.
        
        Returns:
            Dictionary with summary statistics and details.
        """
        if not self.results:
            return {"total_tests": 0, "passed": 0, "failed": 0}
        
        # Group by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)
        
        # Calculate statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        category_stats = {}
        for cat, cat_results in by_category.items():
            cat_passed = sum(1 for r in cat_results if r.passed)
            category_stats[cat] = {
                "total": len(cat_results),
                "passed": cat_passed,
                "failed": len(cat_results) - cat_passed,
                "pass_rate": (cat_passed / len(cat_results) * 100) if cat_results else 0,
                "avg_confidence": sum(r.confidence_score for r in cat_results) / len(cat_results)
            }
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "by_category": category_stats,
            "failed_tests": [
                {
                    "test_id": r.test_id,
                    "category": r.category,
                    "error": r.error_message,
                    "details": r.evaluation_details
                }
                for r in self.results if not r.passed
            ]
        }


# ============================================================================
# Pytest Integration
# ============================================================================

@pytest.fixture
def ground_truth_loader():
    """Pytest fixture for ground truth test loader."""
    return GroundTruthTestLoader()


@pytest.fixture
def ground_truth_runner():
    """Pytest fixture for ground truth test runner."""
    return GroundTruthTestRunner()


def pytest_generate_tests(metafunc):
    """
    Generate test cases dynamically from ground truth data.
    
    This allows pytest to discover and run ground truth tests
    as individual test cases.
    """
    if "ground_truth_test_case" in metafunc.fixturenames:
        loader = GroundTruthTestLoader()
        all_cases = loader.load_all_test_cases()
        
        test_cases = []
        test_ids = []
        
        for category, cases in all_cases.items():
            for case in cases:
                test_cases.append(case)
                test_ids.append(f"{category.value}:{case.test_id}")
        
        metafunc.parametrize("ground_truth_test_case", test_cases, ids=test_ids)


# Example test function using ground truth data
class TestGroundTruth:
    """Ground truth test class for pytest integration."""
    
    def test_loader_loads_test_cases(self, ground_truth_loader):
        """Test that the loader can load test cases."""
        for category in TestCategory:
            cases = ground_truth_loader.load_test_cases(category)
            # Each category should have test cases defined
            assert isinstance(cases, list)
    
    def test_exact_evaluator(self):
        """Test exact match evaluator."""
        evaluator = ExactEvaluator()
        
        # Test exact match
        result = evaluator.evaluate("hello", "hello", EvaluationMode.EXACT)
        assert result["passed"] is True
        assert result["confidence_score"] == 100.0
        
        # Test mismatch
        result = evaluator.evaluate("hello", "world", EvaluationMode.EXACT)
        assert result["passed"] is False
        
        # Test with variations
        result = evaluator.evaluate(
            "hi", "hello", EvaluationMode.EXACT,
            acceptable_variations=["hi", "hey"]
        )
        assert result["passed"] is True
    
    def test_range_evaluator(self):
        """Test range evaluator with tolerance."""
        evaluator = RangeEvaluator(tolerance_percent=10.0)
        
        # Within tolerance
        result = evaluator.evaluate(95, 100, EvaluationMode.RANGE)
        assert result["passed"] is True
        
        # Outside tolerance
        result = evaluator.evaluate(80, 100, EvaluationMode.RANGE)
        assert result["passed"] is False
    
    def test_partial_evaluator(self):
        """Test partial match evaluator."""
        evaluator = PartialEvaluator(required_fields=["field1", "field2"])
        
        actual = {"field1": "a", "field2": "b", "field3": "c"}
        expected = {"field1": "a", "field2": "b", "field3": "different"}
        
        result = evaluator.evaluate(actual, expected, EvaluationMode.PARTIAL)
        assert result["passed"] is True  # Required fields match


if __name__ == "__main__":
    # Run a quick test
    loader = GroundTruthTestLoader()
    
    print("Loading ground truth test cases...")
    all_cases = loader.load_all_test_cases()
    
    for category, cases in all_cases.items():
        print(f"\n{category.value}: {len(cases)} test cases")
        for case in cases[:3]:  # Show first 3
            print(f"  - {case.test_id}: {case.description}")
