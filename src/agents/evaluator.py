"""Evaluator Agent - Validates hypotheses with quantitative evidence."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """Agent responsible for validating hypotheses with production-grade evidence structure."""

    def execute(
        self, hypotheses: List[Dict], data_summary: str, evidence: str
    ) -> Dict[str, Any]:
        """Validate hypotheses using quantitative evidence with baseline/current comparisons.

        Args:
            hypotheses: List of hypotheses to validate
            data_summary: Summary of data
            evidence: Quantitative evidence from analysis

        Returns:
            Dictionary with validation results including structured evidence
        """
        try:
            # Format hypotheses for prompt
            hypotheses_text = self._format_hypotheses(hypotheses)

            prompt = self.load_prompt(
                "evaluator_prompt.md",
                hypotheses=hypotheses_text,
                data_summary=data_summary,
                evidence=evidence,
            )

            system = """You are a production-level validation specialist. Validate hypotheses with STRUCTURED EVIDENCE including:
            - Baseline vs current value comparisons
            - Absolute and relative deltas
            - Impact and severity classification
            - Specific segment/campaign identification

            CRITICAL: Every evaluation MUST include evidence with baseline_value, current_value, absolute_delta, and relative_delta_pct.
            Always output valid JSON matching the required structure."""

            response = self.call_llm(prompt, system=system)
            evaluation = self.parse_json_response(response)

            # Validate and enhance the evaluation structure
            evaluation = self._validate_evaluation_structure(evaluation)

            # Apply confidence threshold and quality filters
            confidence_min = self.config["thresholds"]["confidence_min"]
            validated_evals = self._filter_valid_evaluations(
                evaluation.get("evaluations", []), confidence_min
            )

            # Add metadata
            evaluation["validated_count"] = len(validated_evals)
            evaluation["total_evaluated"] = len(evaluation.get("evaluations", []))
            evaluation["confidence_threshold"] = confidence_min
            evaluation["rejected_count"] = len(evaluation.get("rejected_hypotheses", []))

            # Log validation summary
            logger.info(
                f"Evaluation complete: {evaluation['validated_count']}/{evaluation['total_evaluated']} validated, "
                f"{evaluation['rejected_count']} rejected"
            )

            return evaluation

        except Exception as e:
            logger.error(f"Error in evaluator execution: {str(e)}")
            # Return graceful fallback
            return {
                "evaluations": [],
                "validated_insights": [],
                "rejected_hypotheses": [],
                "validated_count": 0,
                "total_evaluated": len(hypotheses),
                "error": str(e),
            }

    def _validate_evaluation_structure(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that evaluation has required structure with evidence.

        Args:
            evaluation: Raw evaluation from LLM

        Returns:
            Validated and enhanced evaluation
        """
        if "evaluations" not in evaluation:
            logger.warning("Missing 'evaluations' field in response")
            evaluation["evaluations"] = []

        validated_evals = []
        for i, eval_item in enumerate(evaluation.get("evaluations", [])):
            # Check for required fields
            if not self._has_valid_evidence(eval_item):
                logger.warning(
                    f"Evaluation {i} missing valid evidence structure, attempting to fix"
                )
                eval_item = self._fix_evidence_structure(eval_item)

            # Ensure confidence field exists (normalize old confidence_score)
            if "confidence" not in eval_item and "confidence_score" in eval_item:
                eval_item["confidence"] = eval_item["confidence_score"]

            validated_evals.append(eval_item)

        evaluation["evaluations"] = validated_evals
        return evaluation

    def _has_valid_evidence(self, eval_item: Dict) -> bool:
        """Check if evaluation has valid evidence structure.

        Args:
            eval_item: Single evaluation item

        Returns:
            True if has valid evidence
        """
        if "evidence" not in eval_item:
            return False

        evidence = eval_item["evidence"]
        required_fields = [
            "baseline_value",
            "current_value",
            "absolute_delta",
            "relative_delta_pct",
        ]

        return all(field in evidence for field in required_fields)

    def _fix_evidence_structure(self, eval_item: Dict) -> Dict:
        """Attempt to fix missing evidence structure.

        Args:
            eval_item: Evaluation item with incomplete evidence

        Returns:
            Fixed evaluation item
        """
        if "evidence" not in eval_item:
            eval_item["evidence"] = {}

        evidence = eval_item["evidence"]

        # Try to extract from statistical_measures if available
        if "statistical_measures" in eval_item:
            stats = eval_item["statistical_measures"]
            if "metric_change_pct" in stats and "relative_delta_pct" not in evidence:
                evidence["relative_delta_pct"] = stats.get("metric_change_pct", 0.0)

        # Set defaults for missing fields
        if "baseline_value" not in evidence:
            evidence["baseline_value"] = None
        if "current_value" not in evidence:
            evidence["current_value"] = None
        if "absolute_delta" not in evidence:
            evidence["absolute_delta"] = None
        if "relative_delta_pct" not in evidence:
            evidence["relative_delta_pct"] = None

        eval_item["evidence"] = evidence
        return eval_item

    def _filter_valid_evaluations(
        self, evaluations: List[Dict], confidence_min: float
    ) -> List[Dict]:
        """Filter evaluations by confidence and quality.

        Args:
            evaluations: List of evaluation items
            confidence_min: Minimum confidence threshold

        Returns:
            Filtered list of valid evaluations
        """
        validated = []
        for eval_item in evaluations:
            confidence = eval_item.get("confidence", eval_item.get("confidence_score", 0))

            # Must meet confidence threshold
            if confidence < confidence_min:
                continue

            # Must have valid evidence (or at least attempted)
            if not eval_item.get("evidence"):
                continue

            # Must not be refuted or insufficient_data
            status = eval_item.get("validation_status", "")
            if status in ["refuted", "insufficient_data"]:
                continue

            validated.append(eval_item)

        return validated

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
