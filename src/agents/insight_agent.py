"""Insight Agent - Generates hypotheses about performance patterns."""

from typing import Dict, Any
from .base_agent import BaseAgent


class InsightAgent(BaseAgent):
    """Agent responsible for generating hypotheses and insights."""

    def execute(self, context: str, data_summary: str) -> Dict[str, Any]:
        """Generate hypotheses about performance patterns.

        Args:
            context: Context about what to analyze
            data_summary: Summary of data analysis results

        Returns:
            Dictionary with hypotheses and insights
        """
        prompt = self.load_prompt(
            "insight_agent_prompt.md", context=context, data_summary=data_summary
        )

        system = """You are an expert marketing analyst. Generate clear, testable hypotheses 
        that explain performance patterns. Focus on actionable insights. Always output valid JSON."""

        response = self.call_llm(prompt, system=system)
        insights = self.parse_json_response(response)

        # Validate confidence scores
        for hypothesis in insights.get("hypotheses", []):
            if "confidence" not in hypothesis:
                hypothesis["confidence"] = 0.5
            hypothesis["confidence"] = max(0.0, min(1.0, hypothesis["confidence"]))

        return insights
