"""Schema definitions and validation for agent outputs."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


# Schema version
SCHEMA_VERSION = "1.0.0"


class SchemaValidator:
    """Validates agent outputs against defined schemas."""

    # Planner output schema
    PLANNER_SCHEMA = {
        "version": "1.0.0",
        "required_fields": [
            "query_understanding",
            "required_metrics",
            "subtasks",
            "expected_insights",
        ],
        "optional_fields": ["original_query", "total_subtasks"],
        "subtask_fields": {
            "required": [
                "task_id",
                "description",
                "assigned_agent",
                "priority",
                "dependencies",
            ],
            "optional": [],
        },
    }

    # Data agent analysis schema
    DATA_AGENT_SCHEMA = {
        "version": "1.0.0",
        "required_fields": ["key_findings"],
        "optional_fields": ["metrics", "raw_analysis"],
        "finding_fields": {
            "required": ["finding"],
            "optional": ["evidence", "metric_value", "significance"],
        },
    }

    # Insight agent schema
    INSIGHT_AGENT_SCHEMA = {
        "version": "1.0.0",
        "required_fields": ["hypotheses"],
        "optional_fields": ["insight_summary"],
        "hypothesis_fields": {
            "required": [
                "hypothesis_id",
                "title",
                "description",
                "supporting_evidence",
                "potential_causes",
                "affected_segments",
                "confidence",
                "testable",
                "validation_approach",
            ],
            "optional": [],
        },
    }

    # Evaluator schema
    EVALUATOR_SCHEMA = {
        "version": "1.0.0",
        "required_fields": ["evaluations", "validated_insights"],
        "optional_fields": [
            "rejected_hypotheses",
            "requires_more_data",
            "validated_count",
            "confidence_threshold",
        ],
        "evaluation_fields": {
            "required": [
                "hypothesis_id",
                "validation_status",
                "confidence_score",
                "evidence_summary",
                "reasoning",
                "reliability",
            ],
            "optional": ["statistical_measures"],
        },
    }

    # Creative generator schema
    CREATIVE_GENERATOR_SCHEMA = {
        "version": "1.0.0",
        "required_fields": ["recommendations"],
        "optional_fields": ["total_recommendations", "generated_at"],
        "recommendation_fields": {
            "required": ["campaign_name", "current_issue", "creative_variations"],
            "optional": [],
        },
        "variation_fields": {
            "required": [
                "creative_type",
                "headline",
                "message",
                "cta",
                "rationale",
                "expected_improvement",
            ],
            "optional": [],
        },
    }

    @staticmethod
    def validate(
        data: Dict[str, Any], schema: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate data against schema.

        Args:
            data: Data to validate
            schema: Schema definition
            strict: If True, raise errors; if False, return warnings

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check schema version compatibility
        if "schema_version" in data:
            if data["schema_version"] != schema["version"]:
                issues.append(
                    f"Schema version mismatch: data has {data['schema_version']}, "
                    f"expected {schema['version']}"
                )

        # Check required fields
        for field in schema["required_fields"]:
            if field not in data:
                issues.append(f"Missing required field: {field}")

        # Check nested structures if they exist
        if "hypothesis_fields" in schema and "hypotheses" in data:
            for i, hypothesis in enumerate(data["hypotheses"]):
                for field in schema["hypothesis_fields"]["required"]:
                    if field not in hypothesis:
                        issues.append(
                            f"Hypothesis {i}: Missing required field '{field}'"
                        )

        if "evaluation_fields" in schema and "evaluations" in data:
            for i, evaluation in enumerate(data["evaluations"]):
                for field in schema["evaluation_fields"]["required"]:
                    if field not in evaluation:
                        issues.append(
                            f"Evaluation {i}: Missing required field '{field}'"
                        )

        if "recommendation_fields" in schema and "recommendations" in data:
            for i, rec in enumerate(data["recommendations"]):
                for field in schema["recommendation_fields"]["required"]:
                    if field not in rec:
                        issues.append(
                            f"Recommendation {i}: Missing required field '{field}'"
                        )

                # Check variations
                if "creative_variations" in rec and "variation_fields" in schema:
                    for j, variation in enumerate(rec["creative_variations"]):
                        for field in schema["variation_fields"]["required"]:
                            if field not in variation:
                                issues.append(
                                    f"Recommendation {i}, Variation {j}: "
                                    f"Missing required field '{field}'"
                                )

        if "subtask_fields" in schema and "subtasks" in data:
            for i, subtask in enumerate(data["subtasks"]):
                for field in schema["subtask_fields"]["required"]:
                    if field not in subtask:
                        issues.append(f"Subtask {i}: Missing required field '{field}'")

        if "finding_fields" in schema and "key_findings" in data:
            for i, finding in enumerate(data["key_findings"]):
                if isinstance(finding, dict):
                    for field in schema["finding_fields"]["required"]:
                        if field not in finding:
                            issues.append(
                                f"Finding {i}: Missing required field '{field}'"
                            )

        is_valid = len(issues) == 0
        return is_valid, issues

    @staticmethod
    def add_schema_version(data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """Add schema version metadata to data.

        Args:
            data: Data dictionary
            schema_type: Type of schema (planner, data_agent, etc.)

        Returns:
            Data with schema version added
        """
        data["schema_version"] = SCHEMA_VERSION
        data["schema_type"] = schema_type
        data["validated_at"] = datetime.now().isoformat()

        return data

    @staticmethod
    def validate_planner_output(
        data: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate planner output."""
        return SchemaValidator.validate(data, SchemaValidator.PLANNER_SCHEMA, strict)

    @staticmethod
    def validate_data_agent_output(
        data: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate data agent output."""
        return SchemaValidator.validate(data, SchemaValidator.DATA_AGENT_SCHEMA, strict)

    @staticmethod
    def validate_insight_agent_output(
        data: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate insight agent output."""
        return SchemaValidator.validate(
            data, SchemaValidator.INSIGHT_AGENT_SCHEMA, strict
        )

    @staticmethod
    def validate_evaluator_output(
        data: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate evaluator output."""
        return SchemaValidator.validate(data, SchemaValidator.EVALUATOR_SCHEMA, strict)

    @staticmethod
    def validate_creative_generator_output(
        data: Dict[str, Any], strict: bool = False
    ) -> tuple[bool, List[str]]:
        """Validate creative generator output."""
        return SchemaValidator.validate(
            data, SchemaValidator.CREATIVE_GENERATOR_SCHEMA, strict
        )


def check_schema_drift(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[str]:
    """Check for schema drift between two data structures.

    Args:
        old_data: Previous version of data
        new_data: New version of data

    Returns:
        List of drift warnings
    """
    warnings = []

    # Check version changes
    old_version = old_data.get("schema_version", "unknown")
    new_version = new_data.get("schema_version", "unknown")

    if old_version != new_version:
        warnings.append(f"Schema version changed from {old_version} to {new_version}")

    # Check for removed fields
    old_keys = set(old_data.keys())
    new_keys = set(new_data.keys())

    removed_keys = old_keys - new_keys
    if removed_keys:
        warnings.append(f"Fields removed: {', '.join(removed_keys)}")

    added_keys = new_keys - old_keys
    if added_keys:
        warnings.append(f"Fields added: {', '.join(added_keys)}")

    # Check nested structure changes for common fields
    common_keys = old_keys & new_keys

    for key in common_keys:
        old_val = old_data[key]
        new_val = new_data[key]

        # If both are dicts, check recursively
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            nested_warnings = check_schema_drift(old_val, new_val)
            warnings.extend([f"{key}.{w}" for w in nested_warnings])

        # If both are lists of dicts, check first element
        elif isinstance(old_val, list) and isinstance(new_val, list):
            if len(old_val) > 0 and len(new_val) > 0:
                if isinstance(old_val[0], dict) and isinstance(new_val[0], dict):
                    nested_warnings = check_schema_drift(old_val[0], new_val[0])
                    warnings.extend([f"{key}[].{w}" for w in nested_warnings])

    return warnings


def save_schema_definitions(output_path: str):
    """Save schema definitions to file for documentation.

    Args:
        output_path: Path to save schema definitions
    """
    schemas = {
        "version": SCHEMA_VERSION,
        "updated_at": datetime.now().isoformat(),
        "schemas": {
            "planner": SchemaValidator.PLANNER_SCHEMA,
            "data_agent": SchemaValidator.DATA_AGENT_SCHEMA,
            "insight_agent": SchemaValidator.INSIGHT_AGENT_SCHEMA,
            "evaluator": SchemaValidator.EVALUATOR_SCHEMA,
            "creative_generator": SchemaValidator.CREATIVE_GENERATOR_SCHEMA,
        },
    }

    with open(output_path, "w") as f:
        json.dump(schemas, f, indent=2)

    print(f"Schema definitions saved to {output_path}")
