"""Tests for Planner Agent."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.planner import PlannerAgent


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
                return MockClient.MockCompletion('''{
                    "query_understanding": "Analyze ROAS decline in recent period",
                    "required_metrics": ["ROAS", "CTR", "Spend", "Revenue"],
                    "subtasks": [
                        {
                            "task_id": "T1",
                            "description": "Calculate ROAS trend over time",
                            "assigned_agent": "data_agent",
                            "priority": 1,
                            "dependencies": []
                        },
                        {
                            "task_id": "T2",
                            "description": "Identify low-performing campaigns",
                            "assigned_agent": "data_agent",
                            "priority": 2,
                            "dependencies": ["T1"]
                        },
                        {
                            "task_id": "T3",
                            "description": "Generate hypotheses for decline",
                            "assigned_agent": "insight_agent",
                            "priority": 3,
                            "dependencies": ["T1", "T2"]
                        }
                    ],
                    "expected_insights": [
                        "ROAS trend analysis",
                        "Campaign performance comparison",
                        "Root cause hypotheses"
                    ]
                }''')

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


@pytest.fixture
def config():
    """Create test configuration."""
    return {
        'llm': {
            'model': 'gpt-4o',
            'temperature': 0.3,
            'max_tokens': 2500
        }
    }


def test_planner_initialization(config):
    """Test planner initialization."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    assert planner.config == config
    assert planner.client == client


def test_planner_execute(config):
    """Test planner execution."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    query = "Why did ROAS drop in the last 7 days?"
    data_summary = "Dataset has 1000 records from Jan 1-15, 2025"

    result = planner.execute(query, data_summary)

    assert 'query_understanding' in result
    assert 'required_metrics' in result
    assert 'subtasks' in result
    assert 'expected_insights' in result
    assert 'original_query' in result
    assert 'total_subtasks' in result


def test_planner_subtasks_structure(config):
    """Test subtasks have correct structure."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    result = planner.execute("Test query", "Test summary")

    assert len(result['subtasks']) > 0

    for subtask in result['subtasks']:
        assert 'task_id' in subtask
        assert 'description' in subtask
        assert 'assigned_agent' in subtask
        assert 'priority' in subtask
        assert 'dependencies' in subtask


def test_planner_preserves_query(config):
    """Test that original query is preserved."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    query = "Analyze CTR performance"
    result = planner.execute(query, "Test summary")

    assert result['original_query'] == query


def test_planner_counts_subtasks(config):
    """Test total_subtasks is correctly calculated."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    result = planner.execute("Test query", "Test summary")

    assert result['total_subtasks'] == len(result['subtasks'])
    assert result['total_subtasks'] == 3  # Based on mock response


def test_planner_handles_complex_query(config):
    """Test planner with complex multi-part query."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    complex_query = """
    Analyze the ROAS decline in the last 7 days.
    Identify which campaigns are underperforming and why.
    Generate creative recommendations for low-performing campaigns.
    """

    result = planner.execute(complex_query, "Test summary")

    assert result is not None
    assert len(result['subtasks']) > 0


def test_planner_handles_empty_query(config):
    """Test planner handles empty query gracefully."""
    client = MockClient()
    planner = PlannerAgent(config, client)

    result = planner.execute("", "Test summary")

    # Should still return valid structure even with empty query
    assert 'subtasks' in result
    assert isinstance(result['subtasks'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
