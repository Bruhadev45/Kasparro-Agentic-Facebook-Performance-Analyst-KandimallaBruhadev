"""Data Agent - Loads and analyzes dataset."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class DataAgent(BaseAgent):
    """Agent responsible for data loading, processing, and analysis."""

    def __init__(self, config: Dict[str, Any], client):
        """Initialize data agent.

        Args:
            config: Configuration dictionary
            client: Anthropic API client
        """
        super().__init__(config, client)
        self.df = None
        self.data_path = config["data"]["full_csv"]
        if config["data"].get("use_sample_data"):
            self.data_path = config["data"]["sample_csv"]

    def load_data(self) -> pd.DataFrame:
        """Load Facebook Ads dataset.

        Returns:
            DataFrame with ads data
        """
        if self.df is None:
            self.df = pd.read_csv(self.data_path)
            self.df["date"] = pd.to_datetime(self.df["date"])
            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            # Handle missing values
            self.df["spend"] = pd.to_numeric(self.df["spend"], errors="coerce")
            self.df.fillna({"purchases": 0}, inplace=True)
        return self.df

    def get_data_summary(self) -> str:
        """Generate high-level data summary.

        Returns:
            String description of dataset
        """
        df = self.load_data()

        date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"
        total_spend = df["spend"].sum()
        total_revenue = df["revenue"].sum()
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0

        summary = f"""
Dataset Overview:
- Total Records: {len(df):,}
- Date Range: {date_range}
- Unique Campaigns: {df['campaign_name'].nunique()}
- Unique Adsets: {df['adset_name'].nunique()}
- Total Spend: ${total_spend:,.2f}
- Total Revenue: ${total_revenue:,.2f}
- Overall ROAS: {overall_roas:.2f}
- Avg CTR: {df['ctr'].mean():.4f}
- Creative Types: {', '.join(df['creative_type'].unique())}
- Platforms: {', '.join(df['platform'].unique())}
- Countries: {', '.join(df['country'].unique())}
"""
        return summary.strip()

    def execute(
        self, task_description: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute data analysis task.

        Args:
            task_description: Description of what to analyze
            context: Optional additional context

        Returns:
            Dictionary with analysis results
        """
        df = self.load_data()

        # Prepare data summary for LLM
        data_desc = self.get_data_summary()

        # Add specific analysis based on task
        analysis_data = self._perform_analysis(df, task_description)

        prompt = self.load_prompt(
            "data_agent_prompt.md", task_description=task_description
        )

        # Add analysis results to prompt
        prompt += f"\n\n## Analysis Results\n{analysis_data}"

        system = "You are a data analyst. Analyze Facebook Ads data and provide structured insights. Always output valid JSON."

        response = self.call_llm(prompt, system=system)
        result = self.parse_json_response(response)

        # Add raw analysis data
        result["raw_analysis"] = analysis_data

        return result

    def _perform_analysis(self, df: pd.DataFrame, task: str) -> str:
        """Perform quantitative analysis based on task.

        Args:
            df: DataFrame to analyze
            task: Task description

        Returns:
            String with analysis results
        """
        analysis = []

        # Time-based analysis
        if "roas" in task.lower() or "drop" in task.lower() or "change" in task.lower():
            # Compare recent vs previous period
            max_date = df["date"].max()
            last_7_days = df[df["date"] > max_date - timedelta(days=7)]
            prev_7_days = df[
                (df["date"] <= max_date - timedelta(days=7))
                & (df["date"] > max_date - timedelta(days=14))
            ]

            if len(last_7_days) > 0 and len(prev_7_days) > 0:
                recent_roas = (
                    last_7_days["revenue"].sum() / last_7_days["spend"].sum()
                    if last_7_days["spend"].sum() > 0
                    else 0
                )
                prev_roas = (
                    prev_7_days["revenue"].sum() / prev_7_days["spend"].sum()
                    if prev_7_days["spend"].sum() > 0
                    else 0
                )

                roas_change = (
                    (recent_roas - prev_roas) / prev_roas * 100 if prev_roas > 0 else 0
                )

                analysis.append(
                    f"ROAS Trend:\n- Last 7 days: {recent_roas:.2f}\n- Previous 7 days: {prev_roas:.2f}\n- Change: {roas_change:+.1f}%"
                )

        # CTR analysis
        if "ctr" in task.lower() or "click" in task.lower():
            low_ctr_threshold = self.config["thresholds"]["low_ctr_threshold"]
            low_ctr_campaigns = (
                df[df["ctr"] < low_ctr_threshold]
                .groupby("campaign_name")
                .agg({"ctr": "mean", "spend": "sum", "impressions": "sum"})
                .sort_values("spend", ascending=False)
                .head(5)
            )

            if len(low_ctr_campaigns) > 0:
                analysis.append(
                    f"\nLow CTR Campaigns (<{low_ctr_threshold}):\n{low_ctr_campaigns.to_string()}"
                )

        # Creative performance
        creative_perf = (
            df.groupby("creative_type")
            .agg({"roas": "mean", "ctr": "mean", "spend": "sum"})
            .sort_values("roas", ascending=False)
        )
        analysis.append(f"\nCreative Type Performance:\n{creative_perf.to_string()}")

        # Top and bottom performers
        campaign_perf = (
            df.groupby("campaign_name")
            .agg({"roas": "mean", "ctr": "mean", "spend": "sum", "revenue": "sum"})
            .sort_values("roas", ascending=False)
        )

        analysis.append(
            f"\nTop 3 Campaigns by ROAS:\n{campaign_perf.head(3).to_string()}"
        )
        analysis.append(
            f"\nBottom 3 Campaigns by ROAS:\n{campaign_perf.tail(3).to_string()}"
        )

        return "\n".join(analysis)

    def get_low_ctr_campaigns(self) -> pd.DataFrame:
        """Get campaigns with low CTR.

        Returns:
            DataFrame with low CTR campaigns
        """
        df = self.load_data()
        threshold = self.config["thresholds"]["low_ctr_threshold"]

        low_ctr = (
            df[df["ctr"] < threshold]
            .groupby(["campaign_name", "creative_message"])
            .agg({"ctr": "mean", "spend": "sum", "roas": "mean"})
            .reset_index()
            .sort_values("spend", ascending=False)
        )

        return low_ctr.head(10)

    def get_top_performers(self) -> pd.DataFrame:
        """Get high-performing creative messages.

        Returns:
            DataFrame with top performers
        """
        df = self.load_data()

        top_perf = (
            df.groupby(["creative_type", "creative_message"])
            .agg({"ctr": "mean", "roas": "mean", "spend": "sum"})
            .reset_index()
        )

        # Filter for good performers
        top_perf = top_perf[
            (top_perf["ctr"] >= self.config["thresholds"]["low_ctr_threshold"])
            & (top_perf["roas"] >= self.config["thresholds"]["low_roas_threshold"])
        ].sort_values(["roas", "ctr"], ascending=False)

        return top_perf.head(10)
