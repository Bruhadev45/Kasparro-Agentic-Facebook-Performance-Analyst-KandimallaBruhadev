"""Creative Generator Agent - Produces new creative recommendations."""

from typing import Dict, Any
import pandas as pd
from .base_agent import BaseAgent


class CreativeGeneratorAgent(BaseAgent):
    """Agent responsible for generating creative recommendations."""

    def execute(
        self,
        low_performers: pd.DataFrame,
        top_performers: pd.DataFrame,
        insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate creative recommendations for low-performing campaigns.

        Args:
            low_performers: DataFrame with low CTR campaigns
            top_performers: DataFrame with high-performing creatives
            insights: Validated insights about performance

        Returns:
            Dictionary with creative recommendations
        """
        # Format data for prompt
        low_perf_text = self._format_dataframe(low_performers, "Low Performers")
        top_perf_text = self._format_dataframe(top_performers, "Top Performers")
        insights_text = self._format_insights(insights)

        prompt = self.load_prompt(
            "creative_generator_prompt.md",
            low_performers=low_perf_text,
            top_performers=top_perf_text,
            insights=insights_text,
        )

        system = """You are a creative strategist for Facebook Ads. Generate compelling, 
        data-driven creative recommendations. Ground ideas in proven patterns. Always output valid JSON."""

        response = self.call_llm(prompt, system=system)
        recommendations = self.parse_json_response(response)

        # Validate structure
        recommendations["total_recommendations"] = len(
            recommendations.get("recommendations", [])
        )
        recommendations["generated_at"] = pd.Timestamp.now().isoformat()

        return recommendations

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

    def _format_insights(self, insights: Dict[str, Any]) -> str:
        """Format insights for prompt.

        Args:
            insights: Insights dictionary

        Returns:
            Formatted string
        """
        validated = insights.get("validated_insights", [])
        if not validated:
            return "No validated insights available"

        return "Key Insights:\n" + "\n".join(f"- {insight}" for insight in validated)
