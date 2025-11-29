"""Shared test fixtures and utilities."""

import pytest
from typing import Dict, Any


class MockMessage:
    """Mock message object for OpenAI responses."""

    def __init__(self, content: str):
        self.content = content


class MockChoice:
    """Mock choice object for OpenAI responses."""

    def __init__(self, message: MockMessage):
        self.message = message


class MockCompletion:
    """Mock completion response from OpenAI."""

    def __init__(self, content: str):
        self.choices = [MockChoice(MockMessage(content))]


class MockChatCompletions:
    """Mock chat completions API."""

    def __init__(self, response_content: str):
        self.response_content = response_content

    def create(self, **kwargs):
        """Create a mock completion."""
        return MockCompletion(self.response_content)


class MockChat:
    """Mock chat API."""

    def __init__(self, response_content: str):
        self.completions = MockChatCompletions(response_content)


class MockOpenAIClient:
    """Mock OpenAI client for testing."""

    def __init__(self, response_content: str):
        self.chat = MockChat(response_content)


@pytest.fixture
def mock_openai_client():
    """Fixture providing a configurable mock OpenAI client."""

    def _create_client(response: str):
        return MockOpenAIClient(response)

    return _create_client
