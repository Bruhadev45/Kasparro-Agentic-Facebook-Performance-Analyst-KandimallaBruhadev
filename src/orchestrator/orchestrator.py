"""Main Orchestrator - Coordinates agent execution."""

import json
from typing import Dict, Any
from pathlib import Path
from openai import OpenAI

from agents.planner import PlannerAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.evaluator import EvaluatorAgent
from agents.creative_generator import CreativeGeneratorAgent
from utils.logger import Logger


class AgentOrchestrator:
    """Coordinates multi-agent workflow for Facebook Ads analysis."""

    def __init__(self, config: Dict[str, Any], api_key: str):
        """Initialize orchestrator with configuration.

        Args:
            config: Configuration dictionary
            api_key: OpenAI API key
        """
        self.config = config
        self.client = OpenAI(api_key=api_key)
        self.logger = Logger(config)

        # Initialize agents
        self.planner = PlannerAgent(config, self.client)
        self.data_agent = DataAgent(config, self.client)
        self.insight_agent = InsightAgent(config, self.client)
        self.evaluator = EvaluatorAgent(config, self.client)
        self.creative_generator = CreativeGeneratorAgent(config, self.client)

        # Execution state
        self.state = {
            "query": None,
            "plan": None,
            "data_summary": None,
            "analysis": None,
            "insights": None,
            "evaluation": None,
            "creatives": None,
        }

    def run(self, query: str) -> Dict[str, Any]:
        """Execute full agentic workflow with comprehensive logging and validation.

        Args:
            query: User's query or question

        Returns:
            Dictionary with all results
        """
        self.logger.log("orchestrator", "start", {"query": query})
        self.state["query"] = query

        try:
            # Step 1: Load and validate data
            self.logger.log("data_agent", "start", {})
            self.state["data_summary"] = self.data_agent.get_data_summary()

            # Log data quality
            if self.data_agent.data_quality_report:
                self.logger.log_decision(
                    "data_agent",
                    "Data validated and loaded",
                    f"Data quality score: {self.data_agent.data_quality_report['data_quality_score']:.1f}/100. "
                    f"{self.data_agent.data_quality_report['total_rows']} rows loaded.",
                    inputs={"data_path": self.data_agent.data_path},
                    outputs={
                        "quality_score": self.data_agent.data_quality_report["data_quality_score"],
                        "total_rows": self.data_agent.data_quality_report["total_rows"],
                    },
                )

            self.logger.log(
                "data_agent",
                "complete",
                {"summary_length": len(self.state["data_summary"])},
            )

            # Step 2: Plan the analysis
            self.logger.log("planner", "start", {})
            self.state["plan"] = self.planner.execute(
                query=query, data_summary=self.state["data_summary"]
            )
            self.logger.log(
                "planner",
                "complete",
                {"subtasks": self.state["plan"].get("total_subtasks", 0)},
            )

            # Step 3: Execute data analysis
            self.logger.log("data_agent", "analysis_start", {})
            analysis_task = self._get_analysis_task_description()
            self.state["analysis"] = self.data_agent.execute(
                task_description=analysis_task, context=self.state["plan"]
            )
            self.logger.log(
                "data_agent",
                "analysis_complete",
                {"findings": len(self.state["analysis"].get("key_findings", []))},
            )

            # Step 4: Generate insights and hypotheses
            self.logger.log("insight_agent", "start", {})
            self.state["insights"] = self.insight_agent.execute(
                context=query, data_summary=json.dumps(self.state["analysis"], indent=2)
            )
            num_hypotheses = len(self.state["insights"].get("hypotheses", []))
            self.logger.log(
                "insight_agent",
                "complete",
                {"hypotheses": num_hypotheses},
            )
            self.logger.log_decision(
                "insight_agent",
                f"Generated {num_hypotheses} hypotheses",
                f"Based on analysis of {len(self.state['analysis'].get('key_findings', []))} key findings from data",
                inputs={"query": query, "findings_count": len(self.state["analysis"].get("key_findings", []))},
                outputs={"hypotheses_generated": num_hypotheses},
            )

            # Step 5: Validate hypotheses
            self.logger.log("evaluator", "start", {})
            self.state["evaluation"] = self.evaluator.execute(
                hypotheses=self.state["insights"].get("hypotheses", []),
                data_summary=self.state["data_summary"],
                evidence=self.state["analysis"].get("raw_analysis", ""),
            )
            validated_count = self.state["evaluation"].get("validated_count", 0)
            total_count = self.state["evaluation"].get("total_evaluated", 0)
            rejected_count = self.state["evaluation"].get("rejected_count", 0)

            self.logger.log(
                "evaluator",
                "complete",
                {
                    "validated": validated_count,
                    "total": total_count,
                    "rejected": rejected_count,
                },
            )
            self.logger.log_decision(
                "evaluator",
                f"Validated {validated_count}/{total_count} hypotheses",
                f"Applied confidence threshold of {self.config['thresholds']['confidence_min']}. "
                f"Rejected {rejected_count} hypotheses due to insufficient evidence or low confidence.",
                inputs={"hypotheses_count": total_count, "threshold": self.config["thresholds"]["confidence_min"]},
                outputs={"validated": validated_count, "rejected": rejected_count},
            )

            # Step 6: Generate creative recommendations
            self.logger.log("creative_generator", "start", {})
            low_ctr = self.data_agent.get_low_ctr_campaigns()
            top_perf = self.data_agent.get_top_performers()

            self.logger.log_decision(
                "creative_generator",
                f"Selected {len(low_ctr)} low-performing and {len(top_perf)} top-performing campaigns",
                f"Using CTR threshold of {self.config['thresholds']['low_ctr_threshold']} "
                f"and ROAS threshold of {self.config['thresholds']['low_roas_threshold']}",
                inputs={"low_ctr_count": len(low_ctr), "top_performers_count": len(top_perf)},
            )

            self.state["creatives"] = self.creative_generator.execute(
                low_performers=low_ctr,
                top_performers=top_perf,
                insights=self.state["evaluation"],
            )
            total_recs = self.state["creatives"].get("total_recommendations", 0)
            linked_recs = self.state["creatives"].get("linked_to_insights", 0)

            self.logger.log(
                "creative_generator",
                "complete",
                {
                    "recommendations": total_recs,
                    "linked_to_insights": linked_recs,
                },
            )
            self.logger.log_decision(
                "creative_generator",
                f"Generated {total_recs} creative recommendations",
                f"{linked_recs} recommendations tightly linked to validated insights. "
                f"All recommendations address specific diagnosed issues.",
                outputs={"total_recommendations": total_recs, "linked_recommendations": linked_recs},
            )

            # Step 7: Generate final report
            self.logger.log("report_generator", "start", {})
            report = self._generate_report()
            self.logger.log(
                "report_generator", "complete", {"report_length": len(report)}
            )

            # Save outputs
            self._save_outputs(report)

            self.logger.log("orchestrator", "complete", {"status": "success"})

            # Add executive summary to evaluation
            exec_summary = self._generate_executive_summary()
            self.state["evaluation"]["overall_assessment"] = exec_summary

            return {
                "status": "success",
                "query": query,
                "insights": self.state["insights"],
                "evaluation": self.state["evaluation"],
                "creatives": self.state["creatives"],
                "report": report,
            }

        except Exception as e:
            self.logger.log("orchestrator", "error", {"error": str(e)})
            raise

    def _get_analysis_task_description(self) -> str:
        """Generate task description from plan.

        Returns:
            Task description string
        """
        query = self.state["query"]
        subtasks = self.state["plan"].get("subtasks", [])

        task_desc = f"Analyze: {query}\n\n"
        task_desc += "Focus areas:\n"
        for task in subtasks:
            if task.get("agent") == "data":
                task_desc += f"- {task.get('description')}\n"

        return task_desc

    def _generate_executive_summary(self) -> str:
        """Generate comprehensive executive summary.

        Returns:
            Executive summary string
        """
        validated = self.state["evaluation"].get("validated_count", 0)
        total_hyp = len(self.state["insights"].get("hypotheses", []))
        findings = self.state["evaluation"].get("validated_insights", [])

        # Build summary
        summary = f"Analyzed {total_hyp} hypotheses and validated {validated} key insights.\n\n"

        if findings:
            summary += "**Top Issues Identified:**\n"
            for i, finding in enumerate(findings[:3], 1):
                summary += f"{i}. {finding}\n"

        # Add action items
        recommendations = self.state["creatives"].get("recommendations", [])
        if recommendations:
            summary += f"\n**Actionable Recommendations:** {len(recommendations)} campaigns identified for creative optimization.\n"

        return summary

    def _generate_report(self) -> str:
        """Generate final markdown report.

        Returns:
            Markdown report string
        """
        # Generate better executive summary
        exec_summary = self._generate_executive_summary()

        report = f"""# Facebook Ads Performance Analysis Report

## Query
{self.state['query']}

## Executive Summary

{exec_summary}

## Key Findings

"""
        # Add validated insights
        for insight in self.state["evaluation"].get("validated_insights", []):
            report += f"- {insight}\n"

        report += "\n## Detailed Hypotheses\n\n"

        # Add hypothesis evaluations
        for eval_result in self.state["evaluation"].get("evaluations", []):
            if (
                eval_result.get("confidence_score", 0)
                >= self.config["thresholds"]["confidence_min"]
            ):
                report += f"### {eval_result.get('hypothesis_id', 'N/A')}\n"
                report += f"**Status**: {eval_result.get('validation_status', 'N/A')}\n"
                report += (
                    f"**Confidence**: {eval_result.get('confidence_score', 0):.2%}\n\n"
                )
                report += f"{eval_result.get('reasoning', 'N/A')}\n\n"

        report += "## Creative Recommendations\n\n"

        # Add creative recommendations
        for rec in self.state["creatives"].get("recommendations", [])[:3]:
            report += f"### {rec.get('campaign_name', 'N/A')}\n"
            report += f"**Issue**: {rec.get('current_issue', 'N/A')}\n\n"

            for i, variant in enumerate(rec.get("creative_variations", [])[:2], 1):
                report += f"#### Variant {i}: {variant.get('creative_type', 'N/A')}\n"
                report += f"**Message**: {variant.get('message', 'N/A')}\n"
                report += f"**Rationale**: {variant.get('rationale', 'N/A')}\n\n"

        report += "\n## Data Summary\n\n"
        report += "```\n"
        report += self.state["data_summary"]
        report += "\n```\n"

        report += f"\n---\n*Generated: {self.logger.get_timestamp()}*\n"

        return report

    def _save_outputs(self, report: str):
        """Save all outputs to files with timestamps.

        Args:
            report: Markdown report
        """
        from datetime import datetime

        reports_dir = Path(self.config["outputs"]["reports_dir"])
        reports_dir.mkdir(exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save all reports with timestamps
        with open(reports_dir / f"report_{timestamp}.md", "w") as f:
            f.write(report)

        with open(reports_dir / f"insights_{timestamp}.json", "w") as f:
            json.dump(
                {
                    "query": self.state["query"],
                    "hypotheses": self.state["insights"].get("hypotheses", []),
                    "evaluation": self.state["evaluation"],
                },
                f,
                indent=2,
            )

        with open(reports_dir / f"creatives_{timestamp}.json", "w") as f:
            json.dump(self.state["creatives"], f, indent=2)

        self.logger.log(
            "outputs",
            "saved",
            {
                "report": str(reports_dir / f"report_{timestamp}.md"),
                "insights": str(reports_dir / f"insights_{timestamp}.json"),
                "creatives": str(reports_dir / f"creatives_{timestamp}.json"),
            },
        )
