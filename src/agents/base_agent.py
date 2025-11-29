"""Base Agent class for all specialized agents."""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
from pathlib import Path


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(self, config: Dict[str, Any], client: OpenAI):
        """Initialize base agent.

        Args:
            config: Configuration dictionary
            client: OpenAI API client
        """
        self.config = config
        self.client = client
        self.model = config.get("llm", {}).get("model", "gpt-4-turbo-preview")
        self.temperature = config.get("llm", {}).get("temperature", 0.7)
        self.max_tokens = config.get("llm", {}).get("max_tokens", 4000)

        # Retry configuration
        self.max_retries = config.get("llm", {}).get("max_retries", 3)
        self.initial_retry_delay = config.get("llm", {}).get("initial_retry_delay", 1.0)
        self.max_retry_delay = config.get("llm", {}).get("max_retry_delay", 60.0)
        self.backoff_factor = config.get("llm", {}).get("backoff_factor", 2.0)

    def load_prompt(self, prompt_file: str, **kwargs) -> str:
        """Load and format prompt template.

        Args:
            prompt_file: Name of prompt file in prompts/ directory
            **kwargs: Variables to substitute in prompt

        Returns:
            Formatted prompt string
        """
        prompt_path = Path("prompts") / prompt_file
        with open(prompt_path, "r") as f:
            template = f.read()

        return template.format(**kwargs)

    def call_llm(self, prompt: str, system: Optional[str] = None) -> str:
        """Call OpenAI API with prompt, includes retry logic with exponential backoff.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            Model response text

        Raises:
            Exception: If all retry attempts fail
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        last_exception = None
        retry_delay = self.initial_retry_delay

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=messages,
                )
                return response.choices[0].message.content

            except Exception as e:
                last_exception = e
                error_type = type(e).__name__

                # Check if error is retryable
                retryable_errors = [
                    "RateLimitError",
                    "APIConnectionError",
                    "APITimeoutError",
                    "InternalServerError",
                    "ServiceUnavailableError",
                ]

                if error_type not in retryable_errors and not any(
                    err in str(e) for err in ["rate limit", "timeout", "connection"]
                ):
                    # Non-retryable error, raise immediately
                    print(f"Non-retryable error: {error_type}: {str(e)}")
                    raise

                # Calculate delay with exponential backoff
                if attempt < self.max_retries - 1:
                    delay = min(retry_delay, self.max_retry_delay)
                    print(
                        f"API call failed (attempt {attempt + 1}/{self.max_retries}): {error_type}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    retry_delay *= self.backoff_factor

        # All retries exhausted
        print(f"All {self.max_retries} retry attempts failed.")
        raise last_exception

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from response.

        Args:
            response: LLM response that may contain JSON

        Returns:
            Parsed JSON dictionary
        """
        import re

        # Try to find JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # Try to parse entire response
            json_str = response.strip()

        # Clean up common JSON issues
        json_str = json_str.replace("\n", " ")
        json_str = re.sub(r",\s*}", "}", json_str)  # Remove trailing commas
        json_str = re.sub(r",\s*]", "]", json_str)  # Remove trailing commas in arrays

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON object with greedy matching
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # Clean again
                json_str = json_str.replace("\n", " ")
                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)
                try:
                    return json.loads(json_str)
                except:
                    pass

            # Last resort: print the response for debugging
            print(f"Failed to parse JSON. Response:\n{response[:500]}")
            raise ValueError(f"Could not parse JSON from response: {e}")

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute agent's main task.

        Returns:
            Dictionary with agent output
        """
        pass
