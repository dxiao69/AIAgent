"""
Ground Truth Testing Framework for ITOA Agent

This package provides infrastructure for validating AI/LLM components
against known correct outputs (ground truth data).

Modules:
    - test_runner: Main test runner and evaluators
    - conftest: Pytest configuration and fixtures

Usage:
    # Run all ground truth tests
    pytest tests/ground_truth/ -v
    
    # Run specific category
    pytest tests/ground_truth/ --gt-category=nl_parsing
    
    # Generate report
    pytest tests/ground_truth/ --gt-report=report.json
    
    # Enable LLM evaluation
    pytest tests/ground_truth/ --use-llm
"""

from .test_runner import (
    GroundTruthTestLoader,
    GroundTruthTestRunner,
    TestCase,
    TestResult,
    EvaluationMode,
    TestCategory,
    ExactEvaluator,
    SemanticEvaluator,
    PartialEvaluator,
    RangeEvaluator,
)

__all__ = [
    "GroundTruthTestLoader",
    "GroundTruthTestRunner",
    "TestCase",
    "TestResult",
    "EvaluationMode",
    "TestCategory",
    "ExactEvaluator",
    "SemanticEvaluator",
    "PartialEvaluator",
    "RangeEvaluator",
]

__version__ = "1.0.0"
