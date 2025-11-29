"""Tests for Creative Generator Agent."""

import pytest
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.creative_generator import CreativeGeneratorAgent


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
    """Mock OpenAI client for testing."""


    class Chat:
        class Completions:
            def create(self, **kwargs):
                return MockClient.MockCompletion('''{
                    "recommendations": [
                        {
                            "campaign_name": "Men ComfortMax Launch",
                            "current_issue": "Low CTR (0.012) due to creative fatigue",
                            "creative_variations": [
                                {
                                    "creative_type": "UGC",
                                    "headline": "Recommended by Athletes",
                                    "message": "See why men everywhere are switching to ComfortMax",
                                    "cta": "Shop Now",
                                    "rationale": "UGC shows 2.1x better performance in retargeting",
                                    "expected_improvement": "+15% CTR"
                                },
                                {
                                    "creative_type": "Video",
                                    "headline": "The Comfort Revolution",
                                    "message": "Watch how ComfortMax technology works",
                                    "cta": "Learn More",
                                    "rationale": "Video creatives have 3x higher engagement",
                                    "expected_improvement": "+20% CTR"
                                }
                            ]
                        }
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


@pytest.fixture
def low_performers():
    """Create sample low-performing campaigns."""
    return pd.DataFrame({
        'campaign_name': ['Campaign A', 'Campaign B'],
        'creative_message': ['Old message A', 'Old message B'],
        'ctr': [0.012, 0.010],
        'spend': [500.0, 450.0],
        'roas': [1.8, 1.5]
    })


@pytest.fixture
def top_performers():
    """Create sample top-performing creatives."""
    return pd.DataFrame({
        'creative_type': ['UGC', 'Video', 'Image'],
        'creative_message': [
            'Real customer testimonial',
            'Product demonstration video',
            'Clean product shot with benefit'
        ],
        'ctr': [0.035, 0.032, 0.028],
        'roas': [4.2, 3.8, 3.5],
        'spend': [200.0, 300.0, 250.0]
    })


@pytest.fixture
def insights():
    """Create sample validated insights."""
    return {
        'validated_insights': [
            'UGC creatives outperform static images by 2x',
            'Video ads show higher engagement in retargeting',
            'Benefit-focused messaging drives higher CTR'
        ],
        'validated_count': 3
    }


def test_creative_generator_initialization(config):
    """Test creative generator initialization."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    assert agent.config == config
    assert agent.client == client


def test_creative_generator_execute(config, low_performers, top_performers, insights):
    """Test creative generator execution."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    result = agent.execute(low_performers, top_performers, insights)

    assert 'recommendations' in result
    assert 'total_recommendations' in result
    assert 'generated_at' in result
    assert len(result['recommendations']) > 0


def test_creative_generator_recommendation_structure(config, low_performers, top_performers, insights):
    """Test recommendations have correct structure."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    result = agent.execute(low_performers, top_performers, insights)

    for rec in result['recommendations']:
        assert 'campaign_name' in rec
        assert 'current_issue' in rec
        assert 'creative_variations' in rec

        for variation in rec['creative_variations']:
            assert 'creative_type' in variation
            assert 'headline' in variation
            assert 'message' in variation
            assert 'cta' in variation
            assert 'rationale' in variation
            assert 'expected_improvement' in variation


def test_creative_generator_counts_recommendations(config, low_performers, top_performers, insights):
    """Test total_recommendations is correctly calculated."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    result = agent.execute(low_performers, top_performers, insights)

    assert result['total_recommendations'] == len(result['recommendations'])


def test_creative_generator_adds_timestamp(config, low_performers, top_performers, insights):
    """Test generated_at timestamp is added."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    result = agent.execute(low_performers, top_performers, insights)

    assert 'generated_at' in result
    # Should be valid ISO timestamp
    pd.Timestamp(result['generated_at'])


def test_creative_generator_format_dataframe(config):
    """Test DataFrame formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    df = pd.DataFrame({
        'campaign': ['A', 'B'],
        'ctr': [0.01, 0.02]
    })

    formatted = agent._format_dataframe(df, "Test Data")

    assert 'Test Data:' in formatted
    assert 'campaign' in formatted
    assert 'ctr' in formatted


def test_creative_generator_format_empty_dataframe(config):
    """Test empty DataFrame formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    df = pd.DataFrame()

    formatted = agent._format_dataframe(df, "Empty Data")

    assert 'Empty Data: No data available' in formatted


def test_creative_generator_format_none_dataframe(config):
    """Test None DataFrame formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    formatted = agent._format_dataframe(None, "Null Data")

    assert 'Null Data: No data available' in formatted


def test_creative_generator_format_insights(config):
    """Test insights formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    insights = {
        'validated_insights': [
            'Insight 1',
            'Insight 2',
            'Insight 3'
        ]
    }

    formatted = agent._format_insights(insights)

    assert 'Key Insights:' in formatted
    assert '- Insight 1' in formatted
    assert '- Insight 2' in formatted
    assert '- Insight 3' in formatted


def test_creative_generator_format_empty_insights(config):
    """Test empty insights formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    insights = {'validated_insights': []}

    formatted = agent._format_insights(insights)

    assert 'No validated insights available' in formatted


def test_creative_generator_format_missing_insights(config):
    """Test missing insights formatting."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    insights = {}

    formatted = agent._format_insights(insights)

    assert 'No validated insights available' in formatted


def test_creative_generator_with_empty_data(config, insights):
    """Test generator handles empty data gracefully."""
    client = MockClient()
    agent = CreativeGeneratorAgent(config, client)

    empty_df = pd.DataFrame()

    result = agent.execute(empty_df, empty_df, insights)

    # Should still return valid structure
    assert 'recommendations' in result
    assert isinstance(result['recommendations'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
