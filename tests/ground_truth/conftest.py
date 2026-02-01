"""
Pytest configuration for Ground Truth Tests.

This file configures pytest to work with the ground truth testing framework.
"""

import pytest
import json
from pathlib import Path


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "ground_truth: mark test as a ground truth test"
    )
    config.addinivalue_line(
        "markers", "nl_parsing: mark test as NL parsing ground truth test"
    )
    config.addinivalue_line(
        "markers", "action_recommendations: mark test as action recommendation test"
    )
    config.addinivalue_line(
        "markers", "risk_classification: mark test as risk classification test"
    )
    config.addinivalue_line(
        "markers", "summarization: mark test as summarization test"
    )
    config.addinivalue_line(
        "markers", "semantic: mark test as requiring semantic (LLM) evaluation"
    )


def pytest_addoption(parser):
    """Add command line options for ground truth testing."""
    parser.addoption(
        "--gt-category",
        action="store",
        default=None,
        help="Run only tests in specified category (nl_parsing, action_recommendations, etc.)"
    )
    parser.addoption(
        "--gt-threshold",
        action="store",
        type=float,
        default=80.0,
        help="Minimum pass rate threshold (default: 80.0)"
    )
    parser.addoption(
        "--gt-report",
        action="store",
        default=None,
        help="Path to save JSON report file"
    )
    parser.addoption(
        "--use-llm",
        action="store_true",
        default=False,
        help="Enable LLM-based semantic evaluation (requires API key)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    category_filter = config.getoption("--gt-category")
    
    if category_filter:
        skip_marker = pytest.mark.skip(reason=f"Only running {category_filter} tests")
        for item in items:
            # Check if test has the specified category marker
            if not any(
                marker.name == category_filter 
                for marker in item.iter_markers()
            ):
                item.add_marker(skip_marker)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def ground_truth_data_dir():
    """Return the path to ground truth test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def nl_parsing_test_cases(ground_truth_data_dir):
    """Load NL parsing test cases."""
    return _load_category_test_cases(ground_truth_data_dir / "nl_parsing")


@pytest.fixture(scope="session")
def action_recommendation_test_cases(ground_truth_data_dir):
    """Load action recommendation test cases."""
    return _load_category_test_cases(ground_truth_data_dir / "action_recommendations")


@pytest.fixture(scope="session")
def risk_classification_test_cases(ground_truth_data_dir):
    """Load risk classification test cases."""
    return _load_category_test_cases(ground_truth_data_dir / "risk_classification")


@pytest.fixture(scope="session")
def summarization_test_cases(ground_truth_data_dir):
    """Load summarization test cases."""
    return _load_category_test_cases(ground_truth_data_dir / "summarization")


@pytest.fixture
def llm_evaluator(request):
    """
    Fixture that provides an LLM evaluator.
    
    Only returns actual LLM evaluator if --use-llm flag is set.
    """
    use_llm = request.config.getoption("--use-llm")
    
    if use_llm:
        # TODO: Initialize actual LLM client
        # from app.services.llm import LLMClient
        # return LLMClient()
        pass
    
    return None


@pytest.fixture(scope="session")
def test_results_collector():
    """Collect test results across the session for reporting."""
    return {
        "results": [],
        "by_category": {}
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _load_category_test_cases(category_dir: Path) -> list:
    """Load all test cases from a category directory."""
    test_cases = []
    
    if not category_dir.exists():
        return test_cases
    
    for json_file in category_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            test_cases.extend(data)
        else:
            test_cases.append(data)
    
    return test_cases


# ============================================================================
# Hooks for Test Results
# ============================================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for reporting."""
    outcome = yield
    report = outcome.get_result()
    
    # Only process ground truth tests
    if not any(marker.name == "ground_truth" for marker in item.iter_markers()):
        return
    
    if report.when == "call":
        # Store result for later reporting
        result = {
            "test_id": item.name,
            "passed": report.passed,
            "duration": report.duration,
            "category": _get_test_category(item)
        }
        
        # Get collector from session
        collector = item.session.config._ground_truth_results
        if collector is None:
            item.session.config._ground_truth_results = {"results": []}
            collector = item.session.config._ground_truth_results
        
        collector["results"].append(result)


def pytest_sessionstart(session):
    """Initialize results collector at session start."""
    session.config._ground_truth_results = {"results": []}


def pytest_sessionfinish(session, exitstatus):
    """Generate report at session end."""
    report_path = session.config.getoption("--gt-report")
    
    if report_path and hasattr(session.config, "_ground_truth_results"):
        results = session.config._ground_truth_results
        
        # Calculate summary statistics
        total = len(results["results"])
        passed = sum(1 for r in results["results"] if r["passed"])
        
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": (passed / total * 100) if total > 0 else 0
            },
            "results": results["results"]
        }
        
        # Group by category
        by_category = {}
        for r in results["results"]:
            cat = r.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0}
            if r["passed"]:
                by_category[cat]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1
        
        report["by_category"] = by_category
        
        # Write report
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nGround Truth Report saved to: {report_path}")


def _get_test_category(item) -> str:
    """Extract test category from markers."""
    category_markers = [
        "nl_parsing", "action_recommendations", 
        "risk_classification", "summarization"
    ]
    
    for marker in item.iter_markers():
        if marker.name in category_markers:
            return marker.name
    
    return "unknown"
