"""Data Agent - Loads and analyzes dataset with production-level validation."""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from utils.data_validation import DataValidator
import logging

logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """Agent responsible for data loading, processing, and analysis with comprehensive error handling."""

    def __init__(self, config: Dict[str, Any], client):
        """Initialize data agent.

        Args:
            config: Configuration dictionary
            client: Anthropic API client
        """
        super().__init__(config, client)
        self.df = None
        self.data_quality_report = None
        self.data_path = config["data"]["full_csv"]
        if config["data"].get("use_sample_data"):
            self.data_path = config["data"]["sample_csv"]

    def load_data(self) -> pd.DataFrame:
        """Load and validate Facebook Ads dataset with comprehensive error handling.

        Returns:
            Cleaned DataFrame with ads data

        Raises:
            ValueError: If data validation fails
        """
        if self.df is None:
            try:
                logger.info(f"Loading data from {self.data_path}")

                # Load raw data
                self.df = pd.read_csv(self.data_path)
                logger.info(f"Loaded {len(self.df)} rows, {len(self.df.columns)} columns")

                # Pre-validation schema check
                is_valid, errors = DataValidator.validate_schema(self.df)
                if not is_valid:
                    logger.warning(f"Schema validation issues: {'; '.join(errors)}")
                    logger.info("Attempting to clean and fix data...")

                # Clean and validate data
                self.df = DataValidator.clean_data(self.df, self.config)

                # Post-validation check
                is_valid, errors = DataValidator.validate_schema(self.df)
                if not is_valid:
                    raise ValueError(f"Data validation failed after cleaning: {'; '.join(errors)}")

                # Generate data quality report
                self.data_quality_report = DataValidator.get_data_quality_report(self.df)
                logger.info(
                    f"Data quality score: {self.data_quality_report['data_quality_score']:.1f}/100"
                )

                logger.info(f"Data loaded successfully. Final shape: {self.df.shape}")

            except FileNotFoundError:
                logger.error(f"Data file not found: {self.data_path}")
                raise
            except Exception as e:
                logger.error(f"Error loading data: {str(e)}")
                raise

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
        """Perform comprehensive baseline vs current analysis.

        Args:
            df: DataFrame to analyze
            task: Task description

        Returns:
            String with detailed baseline/current comparisons
        """
        analysis = []

        try:
            logger.info("Starting performance analysis with baseline comparisons")

            # Define time periods
            max_date = df["date"].max()
            current_start = max_date - timedelta(days=7)
            baseline_start = max_date - timedelta(days=14)
            baseline_end = max_date - timedelta(days=7)

            current_period = df[df["date"] > current_start]
            baseline_period = df[(df["date"] > baseline_start) & (df["date"] <= baseline_end)]

            analysis.append("=" * 60)
            analysis.append("BASELINE vs CURRENT PERFORMANCE COMPARISON")
            analysis.append("=" * 60)
            analysis.append(f"Baseline Period: {baseline_start.date()} to {baseline_end.date()}")
            analysis.append(f"Current Period: {current_start.date()} to {max_date.date()}")
            analysis.append("")

            # Overall metrics comparison
            analysis.append("--- OVERALL METRICS ---")
            analysis.extend(
                self._compare_periods(baseline_period, current_period, "Overall")
            )

            # Campaign-level analysis
            analysis.append("\n--- TOP 5 CAMPAIGNS (by spend) ---")
            top_campaigns = (
                df.groupby("campaign_name")["spend"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .index
            )

            for campaign in top_campaigns:
                baseline_camp = baseline_period[baseline_period["campaign_name"] == campaign]
                current_camp = current_period[current_period["campaign_name"] == campaign]

                if len(baseline_camp) > 0 and len(current_camp) > 0:
                    analysis.append(f"\nCampaign: {campaign}")
                    analysis.extend(
                        self._compare_periods(baseline_camp, current_camp, campaign, indent=2)
                    )

            # Creative type analysis
            analysis.append("\n--- CREATIVE TYPE PERFORMANCE ---")
            for creative_type in df["creative_type"].unique():
                baseline_creative = baseline_period[baseline_period["creative_type"] == creative_type]
                current_creative = current_period[current_period["creative_type"] == creative_type]

                if len(baseline_creative) > 10 and len(current_creative) > 10:
                    analysis.append(f"\n{creative_type}:")
                    analysis.extend(
                        self._compare_periods(
                            baseline_creative, current_creative, creative_type, indent=2
                        )
                    )

            # Platform analysis
            analysis.append("\n--- PLATFORM PERFORMANCE ---")
            for platform in df["platform"].unique():
                baseline_platform = baseline_period[baseline_period["platform"] == platform]
                current_platform = current_period[current_period["platform"] == platform]

                if len(baseline_platform) > 0 and len(current_platform) > 0:
                    analysis.append(f"\n{platform}:")
                    analysis.extend(
                        self._compare_periods(
                            baseline_platform, current_platform, platform, indent=2
                        )
                    )

            # Low performers (current period)
            analysis.append("\n--- LOW PERFORMING CAMPAIGNS (Current Period) ---")
            low_ctr_threshold = self.config["thresholds"]["low_ctr_threshold"]
            low_ctr_campaigns = (
                current_period[current_period["ctr"] < low_ctr_threshold]
                .groupby("campaign_name")
                .agg(
                    {
                        "ctr": "mean",
                        "roas": "mean",
                        "spend": "sum",
                        "impressions": "sum",
                    }
                )
                .sort_values("spend", ascending=False)
                .head(5)
            )

            if len(low_ctr_campaigns) > 0:
                analysis.append(
                    f"\nCampaigns with CTR < {low_ctr_threshold}:"
                )
                analysis.append(low_ctr_campaigns.to_string())

            logger.info("Performance analysis complete")

        except Exception as e:
            logger.error(f"Error in performance analysis: {str(e)}")
            analysis.append(f"\n[ERROR] Analysis failed: {str(e)}")

        return "\n".join(analysis)

    def _compare_periods(
        self,
        baseline: pd.DataFrame,
        current: pd.DataFrame,
        segment_name: str,
        indent: int = 0,
    ) -> List[str]:
        """Compare two time periods with detailed metrics.

        Args:
            baseline: Baseline period data
            current: Current period data
            segment_name: Name of segment being compared
            indent: Indentation level

        Returns:
            List of formatted comparison strings
        """
        indent_str = "  " * indent
        lines = []

        try:
            if len(baseline) == 0 or len(current) == 0:
                lines.append(f"{indent_str}Insufficient data for comparison")
                return lines

            # Calculate metrics for both periods
            metrics = {
                "ROAS": (
                    baseline["revenue"].sum() / baseline["spend"].sum()
                    if baseline["spend"].sum() > 0
                    else 0,
                    current["revenue"].sum() / current["spend"].sum()
                    if current["spend"].sum() > 0
                    else 0,
                ),
                "CTR": (baseline["ctr"].mean(), current["ctr"].mean()),
                "Spend": (baseline["spend"].sum(), current["spend"].sum()),
                "Revenue": (baseline["revenue"].sum(), current["revenue"].sum()),
                "Impressions": (
                    baseline["impressions"].sum(),
                    current["impressions"].sum(),
                ),
            }

            # Calculate and format deltas
            for metric_name, (baseline_val, current_val) in metrics.items():
                if baseline_val > 0:
                    absolute_delta = current_val - baseline_val
                    relative_delta_pct = (absolute_delta / baseline_val) * 100

                    # Format based on metric type
                    if metric_name in ["ROAS", "CTR"]:
                        lines.append(
                            f"{indent_str}{metric_name}: {baseline_val:.4f} → {current_val:.4f} "
                            f"(Δ {absolute_delta:+.4f}, {relative_delta_pct:+.1f}%)"
                        )
                    else:
                        lines.append(
                            f"{indent_str}{metric_name}: ${baseline_val:,.0f} → ${current_val:,.0f} "
                            f"(Δ ${absolute_delta:+,.0f}, {relative_delta_pct:+.1f}%)"
                        )
                else:
                    lines.append(
                        f"{indent_str}{metric_name}: N/A → {current_val:.2f} (new data)"
                    )

            # Sample size
            lines.append(f"{indent_str}Sample Size: {len(baseline)} → {len(current)}")

        except Exception as e:
            logger.error(f"Error comparing periods for {segment_name}: {str(e)}")
            lines.append(f"{indent_str}[ERROR] Comparison failed: {str(e)}")

        return lines

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
