"""Tests for Insight Agent."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.insight_agent import InsightAgent


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
                    "hypotheses": [
                        {
                            "hypothesis_id": "H1",
                            "title": "Creative Fatigue in Video Ads",
                            "description": "Video creatives showing declining CTR over time",
                            "supporting_evidence": [
                                "CTR declined from 0.025 to 0.016 over 14 days",
                                "Video creative type has highest spend"
                            ],
                            "potential_causes": [
                                "Ad frequency too high",
                                "Creative message worn out"
                            ],
                            "affected_segments": ["Video creatives", "Retargeting campaigns"],
                            "confidence": 0.75,
                            "testable": true,
                            "validation_approach": "Compare performance by ad frequency groups"
                        },
                        {
                            "hypothesis_id": "H2",
                            "title": "Audience Saturation",
                            "description": "Retargeting audiences showing diminishing returns",
                            "supporting_evidence": [
                                "Retargeting ROAS dropped 20%",
                                "Impression frequency increased to 5.2"
                            ],
                            "potential_causes": [
                                "Small audience size",
                                "High ad frequency"
                            ],
                            "affected_segments": ["Retargeting", "US market"],
                            "confidence": 0.68,
                            "testable": true,
                            "validation_approach": "Analyze frequency vs performance correlation"
                        }
                    ],
                    "insight_summary": "Performance decline driven by creative fatigue and audience saturation"
                }"""
                )

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


@pytest.fixture
def config():
    """Create test configuration."""
    return {"llm": {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 2500}}


def test_insight_agent_initialization(config):
    """Test insight agent initialization."""
    client = MockClient()
    agent = InsightAgent(config, client)

    assert agent.config == config
    assert agent.client == client


def test_insight_agent_execute(config):
    """Test insight agent execution."""
    client = MockClient()
    agent = InsightAgent(config, client)

    context = "Analyze ROAS decline"
    data_summary = "ROAS dropped from 2.5 to 2.0 in last 7 days"

    result = agent.execute(context, data_summary)

    assert "hypotheses" in result
    assert "insight_summary" in result
    assert len(result["hypotheses"]) > 0


def test_insight_agent_hypothesis_structure(config):
    """Test hypotheses have correct structure."""
    client = MockClient()
    agent = InsightAgent(config, client)

    result = agent.execute("Test context", "Test summary")

    for hypothesis in result["hypotheses"]:
        assert "hypothesis_id" in hypothesis
        assert "title" in hypothesis
        assert "description" in hypothesis
        assert "supporting_evidence" in hypothesis
        assert "potential_causes" in hypothesis
        assert "affected_segments" in hypothesis
        assert "confidence" in hypothesis
        assert "testable" in hypothesis
        assert "validation_approach" in hypothesis


def test_insight_agent_confidence_validation(config):
    """Test confidence scores are validated and bounded."""
    client = MockClient()
    agent = InsightAgent(config, client)

    result = agent.execute("Test context", "Test summary")

    for hypothesis in result["hypotheses"]:
        confidence = hypothesis["confidence"]
        assert isinstance(confidence, (int, float))
        assert 0.0 <= confidence <= 1.0


def test_insight_agent_missing_confidence(config):
    """Test missing confidence scores are set to default."""

    # Create mock that returns hypothesis without confidence
    class MockClientNoConfidence:
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockCompletion:
            def __init__(self, content):
                self.choices = [
                    MockClientNoConfidence.MockChoice(
                        MockClientNoConfidence.MockMessage(content)
                    )
                ]

        class Chat:
            class Completions:
                def create(self, **kwargs):
                    return MockClientNoConfidence.MockCompletion(
                        """{
                        "hypotheses": [
                            {
                                "hypothesis_id": "H1",
                                "title": "Test Hypothesis",
                                "description": "Test description",
                                "supporting_evidence": ["Evidence"],
                                "potential_causes": ["Cause"],
                                "affected_segments": ["Segment"],
                                "testable": true,
                                "validation_approach": "Test approach"
                            }
                        ],
                        "insight_summary": "Test summary"
                    }"""
                    )

            def __init__(self):
                self.completions = self.Completions()

        def __init__(self):
            self.chat = self.Chat()

    client = MockClientNoConfidence()
    agent = InsightAgent(config, client)

    result = agent.execute("Test", "Test")

    # Should have default confidence of 0.5
    assert result["hypotheses"][0]["confidence"] == 0.5


def test_insight_agent_confidence_bounds(config):
    """Test confidence scores are clamped to valid range."""

    # Create mock with out-of-bounds confidence
    class MockClientBadConfidence:
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockCompletion:
            def __init__(self, content):
                self.choices = [
                    MockClientBadConfidence.MockChoice(
                        MockClientBadConfidence.MockMessage(content)
                    )
                ]

        class Chat:
            class Completions:
                def create(self, **kwargs):
                    return MockClientBadConfidence.MockCompletion(
                        """{
                        "hypotheses": [
                            {
                                "hypothesis_id": "H1",
                                "title": "Test",
                                "description": "Test",
                                "supporting_evidence": [],
                                "potential_causes": [],
                                "affected_segments": [],
                                "confidence": 1.5,
                                "testable": true,
                                "validation_approach": "Test"
                            },
                            {
                                "hypothesis_id": "H2",
                                "title": "Test 2",
                                "description": "Test 2",
                                "supporting_evidence": [],
                                "potential_causes": [],
                                "affected_segments": [],
                                "confidence": -0.2,
                                "testable": true,
                                "validation_approach": "Test"
                            }
                        ],
                        "insight_summary": "Test"
                    }"""
                    )

            def __init__(self):
                self.completions = self.Completions()

        def __init__(self):
            self.chat = self.Chat()

    client = MockClientBadConfidence()
    agent = InsightAgent(config, client)

    result = agent.execute("Test", "Test")

    # Confidence should be clamped to [0, 1]
    assert result["hypotheses"][0]["confidence"] == 1.0
    assert result["hypotheses"][1]["confidence"] == 0.0


def test_insight_agent_multiple_hypotheses(config):
    """Test agent generates multiple hypotheses."""
    client = MockClient()
    agent = InsightAgent(config, client)

    result = agent.execute("Test context", "Test summary")

    # Mock returns 2 hypotheses
    assert len(result["hypotheses"]) >= 2


def test_insight_agent_hypothesis_uniqueness(config):
    """Test hypotheses have unique IDs."""
    client = MockClient()
    agent = InsightAgent(config, client)

    result = agent.execute("Test context", "Test summary")

    hypothesis_ids = [h["hypothesis_id"] for h in result["hypotheses"]]
    assert len(hypothesis_ids) == len(set(hypothesis_ids))  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
