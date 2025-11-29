"""Planner Agent - Decomposes queries into subtasks."""

from typing import Dict, Any
from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for query decomposition and task planning."""

    def execute(self, query: str, data_summary: str) -> Dict[str, Any]:
        """Break down user query into actionable subtasks.

        Args:
            query: User's question or request
            data_summary: High-level summary of available data

        Returns:
            Dictionary with query understanding and subtask plan
        """
        prompt = self.load_prompt(
            "planner_prompt.md", query=query, data_summary=data_summary
        )

        system = "You are a strategic planner. Decompose complex queries into clear, executable subtasks. Always output valid JSON."

        response = self.call_llm(prompt, system=system)
        plan = self.parse_json_response(response)

        # Validate and enhance plan
        plan["original_query"] = query
        plan["total_subtasks"] = len(plan.get("subtasks", []))

        return plan
