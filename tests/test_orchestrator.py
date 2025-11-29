"""Integration tests for Agent Orchestrator."""

import pytest
import sys
from pathlib import Path
import pandas as pd
import tempfile
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator.orchestrator import AgentOrchestrator


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
            def __init__(self):
                self.call_count = 0

            def create(self, **kwargs):
                """Return different responses based on call count."""
                self.call_count += 1

                # Planner response
                if self.call_count == 1:
                    return MockClient.MockCompletion(
                        """{
                        "query_understanding": "Analyze ROAS decline",
                        "required_metrics": ["ROAS", "CTR"],
                        "subtasks": [
                            {"task_id": "T1", "description": "Analyze ROAS trend", "assigned_agent": "data_agent", "priority": 1, "dependencies": []}
                        ],
                        "expected_insights": ["ROAS trend analysis"]
                    }"""
                    )
                # Data agent analysis response
                elif self.call_count == 2:
                    return MockClient.MockCompletion(
                        """{
                        "key_findings": [
                            {"finding": "ROAS declined by 15%", "evidence": "Data shows decline"}
                        ],
                        "metrics": {"roas_change": -15.0}
                    }"""
                    )
                # Insight agent response
                elif self.call_count == 3:
                    return MockClient.MockCompletion(
                        """{
                        "hypotheses": [
                            {
                                "hypothesis_id": "H1",
                                "title": "Creative Fatigue",
                                "description": "Creatives showing fatigue",
                                "supporting_evidence": ["CTR decline"],
                                "potential_causes": ["Ad frequency"],
                                "affected_segments": ["Video"],
                                "confidence": 0.75,
                                "testable": true,
                                "validation_approach": "Compare frequency groups"
                            }
                        ],
                        "insight_summary": "Creative fatigue detected"
                    }"""
                    )
                # Evaluator response
                elif self.call_count == 4:
                    return MockClient.MockCompletion(
                        """{
                        "evaluations": [
                            {
                                "hypothesis_id": "H1",
                                "validation_status": "confirmed",
                                "confidence_score": 0.85,
                                "evidence_summary": {"supporting": ["Evidence"], "contradicting": [], "missing": []},
                                "statistical_measures": {"metric_change_pct": 15.0, "sample_size": 100, "effect_magnitude": "medium"},
                                "reasoning": "Strong evidence",
                                "reliability": "high"
                            }
                        ],
                        "validated_insights": ["Creative fatigue confirmed"],
                        "rejected_hypotheses": [],
                        "requires_more_data": []
                    }"""
                    )
                # Creative generator response
                else:
                    return MockClient.MockCompletion(
                        """{
                        "recommendations": [
                            {
                                "campaign_name": "Test Campaign",
                                "current_issue": "Low CTR",
                                "creative_variations": [
                                    {
                                        "creative_type": "UGC",
                                        "headline": "Test Headline",
                                        "message": "Test message",
                                        "cta": "Shop Now",
                                        "rationale": "UGC performs better",
                                        "expected_improvement": "+15% CTR"
                                    }
                                ]
                            }
                        ]
                    }"""
                    )

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    dates = pd.date_range(start="2025-01-01", end="2025-01-15", freq="D")
    data = []
    for date in dates:
        data.append(
            {
                "date": date,
                "campaign_name": "Test Campaign",
                "adset_name": "Test Adset",
                "creative_type": "Image",
                "creative_message": "Test message",
                "spend": 100.0,
                "impressions": 10000,
                "clicks": 150,
                "ctr": 0.015,
                "purchases": 10,
                "revenue": 200.0,
                "roas": 2.0,
                "audience_type": "Broad",
                "platform": "Facebook",
                "country": "US",
            }
        )
    return pd.DataFrame(data)


@pytest.fixture
def config(tmp_path, sample_data):
    """Create test configuration."""
    csv_path = tmp_path / "test_data.csv"
    sample_data.to_csv(csv_path, index=False)

    reports_dir = tmp_path / "reports"
    logs_dir = tmp_path / "logs"
    reports_dir.mkdir()
    logs_dir.mkdir()

    return {
        "data": {
            "full_csv": str(csv_path),
            "sample_csv": str(csv_path),
            "use_sample_data": False,
        },
        "thresholds": {
            "low_ctr_threshold": 0.015,
            "low_roas_threshold": 2.0,
            "confidence_min": 0.6,
        },
        "llm": {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 2500},
        "outputs": {
            "reports_dir": str(reports_dir),
            "logs_dir": str(logs_dir),
            "insights_file": str(reports_dir / "insights.json"),
            "creatives_file": str(reports_dir / "creatives.json"),
            "report_file": str(reports_dir / "report.md"),
        },
        "logging": {"level": "INFO", "format": "json"},
    }


def test_orchestrator_initialization(config):
    """Test orchestrator initialization."""
    client = MockClient()
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    orchestrator.config = config
    orchestrator.client = client

    # Verify initial state
    assert orchestrator.config == config
    assert orchestrator.client == client


def test_orchestrator_run_success(config):
    """Test successful end-to-end orchestration."""
    # Use mock client
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    orchestrator.config = config
    orchestrator.client = MockClient()

    # Manually initialize components
    from utils.logger import Logger
    from agents.planner import PlannerAgent
    from agents.data_agent import DataAgent
    from agents.insight_agent import InsightAgent
    from agents.evaluator import EvaluatorAgent
    from agents.creative_generator import CreativeGeneratorAgent

    orchestrator.logger = Logger(config)
    orchestrator.planner = PlannerAgent(config, orchestrator.client)
    orchestrator.data_agent = DataAgent(config, orchestrator.client)
    orchestrator.insight_agent = InsightAgent(config, orchestrator.client)
    orchestrator.evaluator = EvaluatorAgent(config, orchestrator.client)
    orchestrator.creative_generator = CreativeGeneratorAgent(
        config, orchestrator.client
    )

    orchestrator.state = {
        "query": None,
        "plan": None,
        "data_summary": None,
        "analysis": None,
        "insights": None,
        "evaluation": None,
        "creatives": None,
    }

    query = "Why did ROAS drop in the last 7 days?"
    result = orchestrator.run(query)

    # Verify result structure
    assert result is not None
    assert "status" in result
    assert result["status"] == "success"
    assert "query" in result
    assert "insights" in result
    assert "evaluation" in result
    assert "creatives" in result
    assert "report" in result


def test_orchestrator_state_management(config):
    """Test orchestrator maintains state correctly."""
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    orchestrator.config = config
    orchestrator.client = MockClient()

    from utils.logger import Logger
    from agents.planner import PlannerAgent
    from agents.data_agent import DataAgent
    from agents.insight_agent import InsightAgent
    from agents.evaluator import EvaluatorAgent
    from agents.creative_generator import CreativeGeneratorAgent

    orchestrator.logger = Logger(config)
    orchestrator.planner = PlannerAgent(config, orchestrator.client)
    orchestrator.data_agent = DataAgent(config, orchestrator.client)
    orchestrator.insight_agent = InsightAgent(config, orchestrator.client)
    orchestrator.evaluator = EvaluatorAgent(config, orchestrator.client)
    orchestrator.creative_generator = CreativeGeneratorAgent(
        config, orchestrator.client
    )

    orchestrator.state = {
        "query": None,
        "plan": None,
        "data_summary": None,
        "analysis": None,
        "insights": None,
        "evaluation": None,
        "creatives": None,
    }

    query = "Test query"
    orchestrator.run(query)

    # Verify state was updated
    assert orchestrator.state["query"] == query
    assert orchestrator.state["data_summary"] is not None
    assert orchestrator.state["plan"] is not None
    assert orchestrator.state["analysis"] is not None
    assert orchestrator.state["insights"] is not None
    assert orchestrator.state["evaluation"] is not None


def test_orchestrator_agent_pipeline(config):
    """Test agents execute in correct order."""
    execution_order = []

    class TrackingMockClient:
        """Mock that tracks execution order."""

        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockCompletion:
            def __init__(self, content):
                self.choices = [
                    TrackingMockClient.MockChoice(
                        TrackingMockClient.MockMessage(content)
                    )
                ]

        class Chat:
            class Completions:
                def __init__(self, tracker):
                    self.tracker = tracker
                    self.call_count = 0

                def create(self, **kwargs):
                    self.call_count += 1
                    if self.call_count == 1:
                        self.tracker.append("planner")
                        return TrackingMockClient.MockCompletion(
                            '{"query_understanding": "test", "required_metrics": [], "subtasks": [{"task_id": "T1", "description": "test", "assigned_agent": "data_agent", "priority": 1, "dependencies": []}], "expected_insights": []}'
                        )
                    elif self.call_count == 2:
                        self.tracker.append("data_agent")
                        return TrackingMockClient.MockCompletion(
                            '{"key_findings": [], "metrics": {}}'
                        )
                    elif self.call_count == 3:
                        self.tracker.append("insight_agent")
                        return TrackingMockClient.MockCompletion(
                            '{"hypotheses": [{"hypothesis_id": "H1", "title": "test", "description": "test", "supporting_evidence": [], "potential_causes": [], "affected_segments": [], "confidence": 0.7, "testable": true, "validation_approach": "test"}], "insight_summary": "test"}'
                        )
                    elif self.call_count == 4:
                        self.tracker.append("evaluator")
                        return TrackingMockClient.MockCompletion(
                            '{"evaluations": [{"hypothesis_id": "H1", "validation_status": "confirmed", "confidence_score": 0.7, "evidence_summary": {"supporting": [], "contradicting": [], "missing": []}, "statistical_measures": {}, "reasoning": "test", "reliability": "medium"}], "validated_insights": [], "rejected_hypotheses": [], "requires_more_data": []}'
                        )
                    else:
                        self.tracker.append("creative_generator")
                        return TrackingMockClient.MockCompletion(
                            '{"recommendations": []}'
                        )

            def __init__(self, tracker):
                self.completions = self.Completions(tracker)

        def __init__(self, tracker):
            self.chat = self.Chat(tracker)

    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    orchestrator.config = config
    orchestrator.client = TrackingMockClient(execution_order)

    from utils.logger import Logger
    from agents.planner import PlannerAgent
    from agents.data_agent import DataAgent
    from agents.insight_agent import InsightAgent
    from agents.evaluator import EvaluatorAgent
    from agents.creative_generator import CreativeGeneratorAgent

    orchestrator.logger = Logger(config)
    orchestrator.planner = PlannerAgent(config, orchestrator.client)
    orchestrator.data_agent = DataAgent(config, orchestrator.client)
    orchestrator.insight_agent = InsightAgent(config, orchestrator.client)
    orchestrator.evaluator = EvaluatorAgent(config, orchestrator.client)
    orchestrator.creative_generator = CreativeGeneratorAgent(
        config, orchestrator.client
    )

    orchestrator.state = {
        "query": None,
        "plan": None,
        "data_summary": None,
        "analysis": None,
        "insights": None,
        "evaluation": None,
        "creatives": None,
    }

    orchestrator.run("Test query")

    # Verify agents executed in correct order
    expected_order = [
        "planner",
        "data_agent",
        "insight_agent",
        "evaluator",
        "creative_generator",
    ]
    assert execution_order == expected_order


def test_orchestrator_error_handling(config):
    """Test orchestrator handles errors gracefully."""

    class ErrorMockClient:
        """Mock that raises errors."""

        class Chat:
            class Completions:
                def create(self, **kwargs):
                    raise Exception("API Error")

            def __init__(self):
                self.completions = self.Completions()

        def __init__(self):
            self.chat = self.Chat()

    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    orchestrator.config = config
    orchestrator.client = ErrorMockClient()

    from utils.logger import Logger
    from agents.planner import PlannerAgent
    from agents.data_agent import DataAgent
    from agents.insight_agent import InsightAgent
    from agents.evaluator import EvaluatorAgent
    from agents.creative_generator import CreativeGeneratorAgent

    orchestrator.logger = Logger(config)
    orchestrator.planner = PlannerAgent(config, orchestrator.client)
    orchestrator.data_agent = DataAgent(config, orchestrator.client)
    orchestrator.insight_agent = InsightAgent(config, orchestrator.client)
    orchestrator.evaluator = EvaluatorAgent(config, orchestrator.client)
    orchestrator.creative_generator = CreativeGeneratorAgent(
        config, orchestrator.client
    )

    orchestrator.state = {
        "query": None,
        "plan": None,
        "data_summary": None,
        "analysis": None,
        "insights": None,
        "evaluation": None,
        "creatives": None,
    }

    # Should raise exception
    with pytest.raises(Exception):
        orchestrator.run("Test query")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
