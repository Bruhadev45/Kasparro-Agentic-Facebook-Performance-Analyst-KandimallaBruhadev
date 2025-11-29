"""Evaluator Agent - Validates hypotheses with quantitative evidence."""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class EvaluatorAgent(BaseAgent):
    """Agent responsible for validating hypotheses."""

    def execute(
        self, hypotheses: List[Dict], data_summary: str, evidence: str
    ) -> Dict[str, Any]:
        """Validate hypotheses using quantitative evidence.

        Args:
            hypotheses: List of hypotheses to validate
            data_summary: Summary of data
            evidence: Quantitative evidence from analysis

        Returns:
            Dictionary with validation results
        """
        # Format hypotheses for prompt
        hypotheses_text = self._format_hypotheses(hypotheses)

        prompt = self.load_prompt(
            "evaluator_prompt.md",
            hypotheses=hypotheses_text,
            data_summary=data_summary,
            evidence=evidence,
        )

        system = """You are a rigorous validation specialist. Test hypotheses critically 
        using quantitative evidence. Assign accurate confidence scores. Always output valid JSON."""

        response = self.call_llm(prompt, system=system)
        evaluation = self.parse_json_response(response)

        # Apply confidence threshold
        confidence_min = self.config["thresholds"]["confidence_min"]
        validated = [
            eval_result
            for eval_result in evaluation.get("evaluations", [])
            if eval_result.get("confidence_score", 0) >= confidence_min
        ]

        evaluation["validated_count"] = len(validated)
        evaluation["total_evaluated"] = len(evaluation.get("evaluations", []))
        evaluation["confidence_threshold"] = confidence_min

        return evaluation

    def _format_hypotheses(self, hypotheses: List[Dict]) -> str:
        """Format hypotheses for prompt.

        Args:
            hypotheses: List of hypothesis dictionaries

        Returns:
            Formatted string
        """
        formatted = []
        for h in hypotheses:
            formatted.append(
                f"""
Hypothesis {h.get('hypothesis_id', 'N/A')}:
Title: {h.get('title', 'N/A')}
Description: {h.get('description', 'N/A')}
Confidence: {h.get('confidence', 0.0)}
Evidence: {', '.join(h.get('supporting_evidence', []))}
"""
            )
        return "\n".join(formatted)
