"""Logger utility for structured logging."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import traceback


class Logger:
    """Structured JSON logger for agent execution traces."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize logger.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logs_dir = Path(config["outputs"]["logs_dir"])
        self.logs_dir.mkdir(exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"execution_{self.session_id}.json"
        self.logs = []
        self.event_start_times = {}  # Track event start times for duration calculation

    def log(
        self,
        agent: str,
        event: str,
        data: Dict[str, Any],
        level: str = "INFO",
        error: Optional[Exception] = None,
    ):
        """Log an event with enhanced metadata.

        Args:
            agent: Agent name
            event: Event type (start, complete, error, etc.)
            data: Event data
            level: Log level (INFO, WARNING, ERROR)
            error: Optional exception object for error events
        """
        timestamp = self.get_timestamp()

        # Calculate duration if this is a completion event
        duration_ms = None
        event_key = f"{agent}:{event.replace('_complete', '').replace('complete', '')}"

        if event in ["start", "analysis_start"]:
            self.event_start_times[event_key] = datetime.now()
        elif (
            event in ["complete", "analysis_complete"]
            and event_key in self.event_start_times
        ):
            duration = datetime.now() - self.event_start_times[event_key]
            duration_ms = duration.total_seconds() * 1000
            del self.event_start_times[event_key]

        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "agent": agent,
            "event": event,
            "level": level,
            "data": data,
        }

        # Add duration if available
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)

        # Add error details if present
        if error is not None:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

        # Add metadata
        log_entry["metadata"] = {
            "agent_name": agent,
            "event_type": event,
            "has_error": error is not None,
            "data_keys": list(data.keys()) if data else [],
        }

        self.logs.append(log_entry)

        # Write to file
        with open(self.log_file, "w") as f:
            json.dump(self.logs, f, indent=2)

        # Console output with color coding
        self._print_to_console(log_entry)

    def _print_to_console(self, log_entry: Dict[str, Any]):
        """Print log entry to console with formatting.

        Args:
            log_entry: Log entry dictionary
        """
        if self.config["logging"]["level"] not in ["INFO", "DEBUG"]:
            return

        level = log_entry["level"]
        agent = log_entry["agent"]
        event = log_entry["event"]
        timestamp = log_entry["timestamp"]

        # Format duration if available
        duration_str = ""
        if "duration_ms" in log_entry:
            duration_str = f" ({log_entry['duration_ms']:.2f}ms)"

        # Format data summary
        data = log_entry.get("data", {})
        data_summary = self._format_data_summary(data)

        # Color codes for terminal
        colors = {
            "INFO": "\033[94m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m",
        }  # Blue  # Yellow  # Red

        color = colors.get(level, colors["RESET"])
        reset = colors["RESET"]

        print(f"{color}[{timestamp}] {level}: {agent}.{event}{duration_str}{reset}")
        if data_summary:
            print(f"  → {data_summary}")

        # Print error details if present
        if "error" in log_entry:
            error_info = log_entry["error"]
            print(f"  ✗ {error_info['type']}: {error_info['message']}")

    def _format_data_summary(self, data: Dict[str, Any]) -> str:
        """Format data dictionary for console output.

        Args:
            data: Data dictionary

        Returns:
            Formatted string summary
        """
        if not data:
            return ""

        # Create summary of important fields
        summary_parts = []

        # Common fields to highlight
        highlight_fields = [
            "subtasks",
            "hypotheses",
            "validated",
            "total",
            "findings",
            "recommendations",
            "confidence_score",
            "summary_length",
            "query",
        ]

        for field in highlight_fields:
            if field in data:
                value = data[field]
                if isinstance(value, (list, str)):
                    if len(value) > 50:
                        summary_parts.append(f"{field}: {len(value)} items")
                    else:
                        summary_parts.append(f"{field}: {value}")
                else:
                    summary_parts.append(f"{field}: {value}")

        return (
            ", ".join(summary_parts) if summary_parts else json.dumps(data, indent=None)
        )

    def log_metric(
        self,
        agent: str,
        metric_name: str,
        metric_value: Any,
        unit: Optional[str] = None,
    ):
        """Log a specific metric value.

        Args:
            agent: Agent name
            metric_name: Name of the metric
            metric_value: Value of the metric
            unit: Optional unit (e.g., 'ms', 'count', '%')
        """
        data = {"metric_name": metric_name, "value": metric_value}
        if unit:
            data["unit"] = unit

        self.log(agent, "metric", data, level="INFO")

    def log_error(self, agent: str, error: Exception, context: Optional[Dict] = None):
        """Log an error with full context.

        Args:
            agent: Agent name
            error: Exception object
            context: Optional context dictionary
        """
        data = context or {}
        self.log(agent, "error", data, level="ERROR", error=error)

    def log_warning(self, agent: str, message: str, data: Optional[Dict] = None):
        """Log a warning.

        Args:
            agent: Agent name
            message: Warning message
            data: Optional additional data
        """
        warning_data = {"message": message}
        if data:
            warning_data.update(data)

        self.log(agent, "warning", warning_data, level="WARNING")

    def get_timestamp(self) -> str:
        """Get current timestamp.

        Returns:
            ISO format timestamp
        """
        return datetime.now().isoformat()

    def get_logs(self) -> list:
        """Get all logs.

        Returns:
            List of log entries
        """
        return self.logs

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for this session.

        Returns:
            Dictionary with summary statistics
        """
        stats = {
            "session_id": self.session_id,
            "total_events": len(self.logs),
            "agents": list(set(log["agent"] for log in self.logs)),
            "errors": [log for log in self.logs if log.get("level") == "ERROR"],
            "warnings": [log for log in self.logs if log.get("level") == "WARNING"],
            "total_duration_ms": sum(log.get("duration_ms", 0) for log in self.logs),
        }

        # Add event counts by agent
        stats["events_by_agent"] = {}
        for log in self.logs:
            agent = log["agent"]
            stats["events_by_agent"][agent] = stats["events_by_agent"].get(agent, 0) + 1

        return stats
