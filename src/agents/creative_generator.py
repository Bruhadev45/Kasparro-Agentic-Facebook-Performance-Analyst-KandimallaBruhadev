"""Creative Generator Agent - Produces tightly linked creative recommendations."""

from typing import Dict, Any
import pandas as pd
from .base_agent import BaseAgent
import logging
import json

logger = logging.getLogger(__name__)


class CreativeGeneratorAgent(BaseAgent):
    """Agent responsible for generating creative recommendations linked to diagnosed issues."""

    def execute(
        self,
        low_performers: pd.DataFrame,
        top_performers: pd.DataFrame,
        insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate creative recommendations TIGHTLY LINKED to diagnosed issues.

        Args:
            low_performers: DataFrame with low CTR campaigns
            top_performers: DataFrame with high-performing creatives
            insights: Validated insights with evidence structure

        Returns:
            Dictionary with creative recommendations linked to specific diagnoses
        """
        try:
            logger.info("Generating creative recommendations linked to validated insights")

            # Format data for prompt with emphasis on linkage
            low_perf_text = self._format_dataframe(low_performers, "Low Performers")
            top_perf_text = self._format_dataframe(top_performers, "Top Performers")
            insights_text = self._format_insights_with_evidence(insights)

            prompt = self.load_prompt(
                "creative_generator_prompt.md",
                low_performers=low_perf_text,
                top_performers=top_perf_text,
                insights=insights_text,
            )

            system = """You are a production-level creative strategist. Generate recommendations that are TIGHTLY LINKED to diagnosed issues.

            CRITICAL REQUIREMENTS:
            - Every recommendation MUST reference a specific insight (linked_to_insight field)
            - Include diagnosed_issue with baseline/current/delta values
            - Explain how creative addresses the root cause
            - Set specific target improvements

            DO NOT create generic recommendations. Only create recommendations for campaigns with validated insights.
            Always output valid JSON."""

            response = self.call_llm(prompt, system=system)
            recommendations = self.parse_json_response(response)

            # Validate linkage
            recommendations = self._validate_recommendation_linkage(recommendations, insights)

            # Add metadata
            recommendations["total_recommendations"] = len(
                recommendations.get("recommendations", [])
            )
            recommendations["generated_at"] = pd.Timestamp.now().isoformat()
            recommendations["linked_to_insights"] = self._count_linked_recommendations(
                recommendations
            )

            logger.info(
                f"Generated {recommendations['total_recommendations']} recommendations, "
                f"{recommendations['linked_to_insights']} linked to insights"
            )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating creative recommendations: {str(e)}")
            return {
                "recommendations": [],
                "total_recommendations": 0,
                "error": str(e),
            }

    def _format_dataframe(self, df: pd.DataFrame, title: str) -> str:
        """Format DataFrame for prompt.

        Args:
            df: DataFrame to format
            title: Title for this section

        Returns:
            Formatted string
        """
        if df is None or len(df) == 0:
            return f"{title}: No data available"

        return f"{title}:\n{df.to_string()}"

    def _format_insights_with_evidence(self, insights: Dict[str, Any]) -> str:
        """Format insights with full evidence structure for tight linkage.

        Args:
            insights: Insights dictionary with evaluations

        Returns:
            Formatted string with evidence details
        """
        if "evaluations" not in insights:
            logger.warning("No evaluations found in insights")
            return "No validated insights available"

        formatted = []
        formatted.append("VALIDATED INSIGHTS (Link your recommendations to these):")
        formatted.append("=" * 60)

        for eval_item in insights.get("evaluations", []):
            # Only include validated insights
            confidence = eval_item.get("confidence", eval_item.get("confidence_score", 0))
            status = eval_item.get("validation_status", "")

            if confidence >= 0.6 and status not in ["refuted", "insufficient_data"]:
                hyp_id = eval_item.get("hypothesis_id", "N/A")
                evidence = eval_item.get("evidence", {})

                formatted.append(f"\n[{hyp_id}] Confidence: {confidence:.2f}")
                formatted.append(f"Status: {status}")

                if evidence:
                    formatted.append("Evidence:")
                    formatted.append(f"  Metric: {evidence.get('metric', 'N/A')}")
                    formatted.append(f"  Segment: {evidence.get('segment', 'N/A')}")
                    formatted.append(
                        f"  Baseline: {evidence.get('baseline_value', 'N/A')} → "
                        f"Current: {evidence.get('current_value', 'N/A')}"
                    )
                    formatted.append(
                        f"  Change: {evidence.get('relative_delta_pct', 'N/A')}%"
                    )
                    formatted.append(f"  Sample size: {evidence.get('sample_size', 'N/A')}")

                formatted.append(f"Impact: {eval_item.get('impact', 'N/A')}")
                formatted.append(f"Affected campaigns: {eval_item.get('affected_campaigns', [])}")
                formatted.append("-" * 60)

        if len(formatted) == 2:  # Only header
            return "No validated insights with sufficient confidence"

        return "\n".join(formatted)

    def _validate_recommendation_linkage(
        self, recommendations: Dict[str, Any], insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that recommendations are properly linked to insights.

        Args:
            recommendations: Generated recommendations
            insights: Validated insights

        Returns:
            Validated recommendations with warnings
        """
        warnings = []

        # Get valid insight IDs
        valid_insight_ids = {
            eval_item.get("hypothesis_id")
            for eval_item in insights.get("evaluations", [])
            if eval_item.get("confidence", 0) >= 0.6
        }

        # Check each recommendation
        for i, rec in enumerate(recommendations.get("recommendations", [])):
            linked_to = rec.get("linked_to_insight")

            if not linked_to:
                warnings.append(
                    f"Recommendation {i+1} ({rec.get('campaign_name')}) "
                    f"missing 'linked_to_insight' field"
                )
            elif linked_to not in valid_insight_ids:
                warnings.append(
                    f"Recommendation {i+1} links to invalid insight '{linked_to}'"
                )

            if "diagnosed_issue" not in rec:
                warnings.append(
                    f"Recommendation {i+1} missing 'diagnosed_issue' field"
                )

        if warnings:
            logger.warning(f"Recommendation linkage issues: {'; '.join(warnings)}")
            recommendations["linkage_warnings"] = warnings

        return recommendations

    def _count_linked_recommendations(self, recommendations: Dict[str, Any]) -> int:
        """Count recommendations with proper linkage.

        Args:
            recommendations: Recommendations dictionary

        Returns:
            Count of properly linked recommendations
        """
        count = 0
        for rec in recommendations.get("recommendations", []):
            if rec.get("linked_to_insight") and rec.get("diagnosed_issue"):
                count += 1
        return count
