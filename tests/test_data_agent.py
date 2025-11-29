"""Tests for Data Agent."""

import pytest
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.data_agent import DataAgent


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
                    "key_findings": [
                        {
                            "finding": "ROAS declined by 15%",
                            "evidence": "Last 7 days: 2.1, Previous 7 days: 2.5"
                        }
                    ],
                    "metrics": {
                        "roas_change": -15.0,
                        "avg_ctr": 0.018
                    }
                }''')

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


@pytest.fixture
def sample_data():
    """Create sample Facebook Ads data for testing."""
    dates = pd.date_range(start='2025-01-01', end='2025-01-15', freq='D')
    campaigns = ['Campaign A', 'Campaign B', 'Campaign C']

    data = []
    for date in dates:
        for campaign in campaigns:
            data.append({
                'date': date,
                'campaign_name': campaign,
                'adset_name': f'{campaign} - Adset 1',
                'creative_type': 'Image',
                'creative_message': f'Test message for {campaign}',
                'spend': 100.0 + (hash(str(date) + campaign) % 50),
                'impressions': 10000 + (hash(str(date) + campaign) % 5000),
                'clicks': 150 + (hash(str(date) + campaign) % 50),
                'ctr': 0.015 + (hash(str(date) + campaign) % 100) / 10000,
                'purchases': 10 + (hash(str(date) + campaign) % 10),
                'revenue': 200.0 + (hash(str(date) + campaign) % 100),
                'roas': 2.0 + (hash(str(date) + campaign) % 30) / 10,
                'audience_type': 'Broad',
                'platform': 'Facebook',
                'country': 'US'
            })

    return pd.DataFrame(data)


@pytest.fixture
def config(tmp_path, sample_data):
    """Create test configuration."""
    # Save sample data to temporary CSV
    csv_path = tmp_path / "test_data.csv"
    sample_data.to_csv(csv_path, index=False)

    return {
        'data': {
            'full_csv': str(csv_path),
            'sample_csv': str(csv_path),
            'use_sample_data': False
        },
        'thresholds': {
            'low_ctr_threshold': 0.015,
            'low_roas_threshold': 2.0,
            'confidence_min': 0.6
        },
        'llm': {
            'model': 'gpt-4o',
            'temperature': 0.3,
            'max_tokens': 2500
        }
    }


def test_data_agent_initialization(config):
    """Test data agent initialization."""
    client = MockClient()
    agent = DataAgent(config, client)

    assert agent.config == config
    assert agent.df is None
    assert agent.data_path == config['data']['full_csv']


def test_data_agent_load_data(config, sample_data):
    """Test data loading."""
    client = MockClient()
    agent = DataAgent(config, client)

    df = agent.load_data()

    assert df is not None
    assert len(df) == len(sample_data)
    assert 'date' in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    assert agent.df is not None  # Should be cached


def test_data_agent_load_data_caching(config):
    """Test data loading caches result."""
    client = MockClient()
    agent = DataAgent(config, client)

    df1 = agent.load_data()
    df2 = agent.load_data()

    # Should return same object (cached)
    assert df1 is df2


def test_data_agent_get_data_summary(config, sample_data):
    """Test data summary generation."""
    client = MockClient()
    agent = DataAgent(config, client)

    summary = agent.get_data_summary()

    assert isinstance(summary, str)
    assert 'Total Records:' in summary
    assert 'Date Range:' in summary
    assert 'Unique Campaigns:' in summary
    assert 'Total Spend:' in summary
    assert 'Total Revenue:' in summary
    assert 'Overall ROAS:' in summary


def test_data_agent_execute(config):
    """Test data agent execution."""
    client = MockClient()
    agent = DataAgent(config, client)

    result = agent.execute(
        task_description="Analyze ROAS trends over time",
        context={}
    )

    assert 'key_findings' in result
    assert 'raw_analysis' in result
    assert isinstance(result['key_findings'], list)


def test_data_agent_perform_analysis_roas(config, sample_data):
    """Test ROAS analysis."""
    client = MockClient()
    agent = DataAgent(config, client)
    agent.load_data()

    analysis = agent._perform_analysis(sample_data, "analyze roas drop")

    assert 'ROAS Trend:' in analysis
    assert 'Last 7 days:' in analysis
    assert 'Previous 7 days:' in analysis
    assert 'Change:' in analysis


def test_data_agent_perform_analysis_ctr(config, sample_data):
    """Test CTR analysis."""
    client = MockClient()
    agent = DataAgent(config, client)
    agent.load_data()

    analysis = agent._perform_analysis(sample_data, "analyze ctr performance")

    assert 'Low CTR Campaigns' in analysis or 'Creative Type Performance' in analysis


def test_data_agent_get_low_ctr_campaigns(config, sample_data):
    """Test getting low CTR campaigns."""
    client = MockClient()
    agent = DataAgent(config, client)

    low_ctr = agent.get_low_ctr_campaigns()

    assert isinstance(low_ctr, pd.DataFrame)
    assert 'campaign_name' in low_ctr.columns
    assert 'ctr' in low_ctr.columns
    assert 'spend' in low_ctr.columns


def test_data_agent_get_top_performers(config, sample_data):
    """Test getting top performing creatives."""
    client = MockClient()
    agent = DataAgent(config, client)

    top_performers = agent.get_top_performers()

    assert isinstance(top_performers, pd.DataFrame)
    assert 'creative_type' in top_performers.columns
    assert 'creative_message' in top_performers.columns
    assert 'ctr' in top_performers.columns
    assert 'roas' in top_performers.columns


def test_data_agent_handles_missing_values(config, tmp_path):
    """Test handling of missing values in data."""
    # Create data with missing values
    data = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02'],
        'campaign_name': ['Test', 'Test'],
        'adset_name': ['Adset', 'Adset'],
        'creative_type': ['Image', 'Video'],
        'creative_message': ['Msg1', 'Msg2'],
        'spend': [None, 100.0],
        'impressions': [1000, 2000],
        'clicks': [10, 20],
        'ctr': [0.01, 0.01],
        'purchases': [None, 5],
        'revenue': [50, 100],
        'roas': [2.0, 2.5],
        'audience_type': ['Broad', 'Broad'],
        'platform': ['Facebook', 'Instagram'],
        'country': ['US', 'US']
    })

    csv_path = tmp_path / "test_missing.csv"
    data.to_csv(csv_path, index=False)

    config['data']['full_csv'] = str(csv_path)

    client = MockClient()
    agent = DataAgent(config, client)
    df = agent.load_data()

    # purchases should be filled with 0
    assert df['purchases'].isna().sum() == 0


def test_data_agent_date_parsing(config):
    """Test date column is properly parsed."""
    client = MockClient()
    agent = DataAgent(config, client)

    df = agent.load_data()

    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    assert df['date'].notna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
