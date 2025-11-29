"""Tests for Evaluator Agent."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.evaluator import EvaluatorAgent


class MockClient:
    """Mock OpenAI client for testing."""

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockCompletion:
        def __init__(self, content):
            self.choices = [MockClient.MockChoice(MockClient.MockMessage(content))]

    class Chat:
        class Completions:
            def create(self, **kwargs):
                return MockClient.MockCompletion(
                    """{
                    "evaluations": [
                        {
                            "hypothesis_id": "H1",
                            "validation_status": "confirmed",
                            "confidence_score": 0.85,
                            "evidence_summary": {
                                "supporting": ["Evidence 1"],
                                "contradicting": [],
                                "missing": []
                            },
                            "statistical_measures": {
                                "metric_change_pct": 15.0,
                                "sample_size": 100,
                                "effect_magnitude": "medium"
                            },
                            "reasoning": "Test reasoning",
                            "reliability": "high"
                        }
                    ],
                    "validated_insights": ["Insight 1"],
                    "rejected_hypotheses": [],
                    "requires_more_data": []
                }"""
                )

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


def test_evaluator_initialization():
    """Test evaluator initialization."""
    config = {
        "llm": {"model": "test", "temperature": 0.7, "max_tokens": 1000},
        "thresholds": {"confidence_min": 0.6},
    }
    client = MockClient()

    evaluator = EvaluatorAgent(config, client)
    assert evaluator.config == config


def test_evaluator_execute():
    """Test evaluator execution."""
    config = {
        "llm": {"model": "test", "temperature": 0.7, "max_tokens": 1000},
        "thresholds": {"confidence_min": 0.6},
    }
    client = MockClient()
    evaluator = EvaluatorAgent(config, client)

    hypotheses = [
        {
            "hypothesis_id": "H1",
            "title": "Test Hypothesis",
            "description": "Test description",
            "confidence": 0.7,
        }
    ]

    result = evaluator.execute(
        hypotheses=hypotheses, data_summary="Test summary", evidence="Test evidence"
    )

    assert "evaluations" in result
    assert "validated_count" in result
    assert result["validated_count"] >= 0


def test_evaluator_confidence_threshold():
    """Test confidence threshold filtering."""
    config = {
        "llm": {"model": "test", "temperature": 0.7, "max_tokens": 1000},
        "thresholds": {"confidence_min": 0.8},
    }
    client = MockClient()
    evaluator = EvaluatorAgent(config, client)

    result = evaluator.execute(
        hypotheses=[{"hypothesis_id": "H1", "title": "Test"}],
        data_summary="Test",
        evidence="Test",
    )

    # Should have filtered based on confidence >= 0.8
    assert result["confidence_threshold"] == 0.8
    assert result["validated_count"] == 1  # Mock returns 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
