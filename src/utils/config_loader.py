"""Configuration loader utility."""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid

    Raises:
        ValueError: If config is invalid
    """
    required_keys = ["data", "thresholds", "llm", "outputs"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    # Validate data paths
    if config.get("data", {}).get("use_sample_data"):
        data_path = Path(config["data"]["sample_csv"])
    else:
        data_path = Path(config["data"]["full_csv"])

    if not data_path.exists():
        raise ValueError(f"Data file not found: {data_path}")

    return True
