"""Data validation and resilience layer for production-level data handling."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and cleans data with comprehensive error handling."""

    # Required schema columns
    REQUIRED_COLUMNS = [
        "campaign_name",
        "date",
        "spend",
        "impressions",
        "clicks",
        "revenue",
    ]

    # Optional columns with defaults
    OPTIONAL_COLUMNS = {
        "ctr": None,
        "roas": None,
        "purchases": 0,
        "creative_type": "unknown",
        "creative_message": "unknown",
        "platform": "unknown",
        "country": "unknown",
        "adset_name": "unknown",
        "audience_type": "unknown",
    }

    # Computed columns
    COMPUTED_COLUMNS = ["ctr", "roas"]

    @staticmethod
    def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate DataFrame schema against required structure.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required columns
        missing_required = set(DataValidator.REQUIRED_COLUMNS) - set(df.columns)
        if missing_required:
            errors.append(f"Missing required columns: {', '.join(missing_required)}")

        # Check for empty DataFrame
        if len(df) == 0:
            errors.append("DataFrame is empty (0 rows)")

        # Check date column can be parsed
        if "date" in df.columns:
            try:
                pd.to_datetime(df["date"])
            except Exception as e:
                errors.append(f"Cannot parse 'date' column: {str(e)}")

        # Check numeric columns
        numeric_cols = ["spend", "impressions", "clicks", "revenue", "purchases"]
        for col in numeric_cols:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors="coerce")
                except Exception as e:
                    errors.append(f"Cannot convert '{col}' to numeric: {str(e)}")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def clean_data(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Clean and prepare data with comprehensive error handling.

        Args:
            df: Raw DataFrame
            config: Configuration dictionary

        Returns:
            Cleaned DataFrame

        Raises:
            ValueError: If data cannot be cleaned
        """
        logger.info(f"Starting data cleaning. Shape: {df.shape}")

        try:
            # Make a copy to avoid modifying original
            df = df.copy()

            # 1. Handle missing columns
            df = DataValidator._handle_missing_columns(df)

            # 2. Clean column names
            df.columns = df.columns.str.strip().str.lower()

            # 3. Parse dates
            df = DataValidator._parse_dates(df)

            # 4. Convert numeric columns
            df = DataValidator._convert_numeric_columns(df)

            # 5. Handle missing values
            df = DataValidator._handle_missing_values(df)

            # 6. Handle infinities and extreme values
            df = DataValidator._handle_infinities(df)

            # 7. Compute derived metrics
            df = DataValidator._compute_derived_metrics(df)

            # 8. Validate ranges
            df = DataValidator._validate_ranges(df)

            # 9. Remove invalid rows
            initial_rows = len(df)
            df = DataValidator._remove_invalid_rows(df)
            removed_rows = initial_rows - len(df)

            if removed_rows > 0:
                logger.warning(f"Removed {removed_rows} invalid rows ({removed_rows/initial_rows*100:.1f}%)")

            logger.info(f"Data cleaning complete. Final shape: {df.shape}")

            # Final validation
            is_valid, errors = DataValidator.validate_schema(df)
            if not is_valid:
                raise ValueError(f"Data validation failed after cleaning: {', '.join(errors)}")

            return df

        except Exception as e:
            logger.error(f"Error during data cleaning: {str(e)}")
            raise

    @staticmethod
    def _handle_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Add missing optional columns with defaults."""
        for col, default_value in DataValidator.OPTIONAL_COLUMNS.items():
            if col not in df.columns and col not in DataValidator.COMPUTED_COLUMNS:
                logger.warning(f"Missing column '{col}', adding with default: {default_value}")
                df[col] = default_value
        return df

    @staticmethod
    def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
        """Parse date column with error handling."""
        try:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # Check for unparseable dates
            null_dates = df["date"].isna().sum()
            if null_dates > 0:
                logger.warning(f"Found {null_dates} unparseable dates, will remove these rows")

        except Exception as e:
            logger.error(f"Error parsing dates: {str(e)}")
            raise ValueError(f"Cannot parse date column: {str(e)}")

        return df

    @staticmethod
    def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Convert numeric columns with error handling."""
        numeric_cols = [
            "spend",
            "impressions",
            "clicks",
            "revenue",
            "purchases",
            "ctr",
            "roas",
        ]

        for col in numeric_cols:
            if col in df.columns:
                # Convert to numeric, coercing errors to NaN
                original_nulls = df[col].isna().sum()
                df[col] = pd.to_numeric(df[col], errors="coerce")
                new_nulls = df[col].isna().sum()

                if new_nulls > original_nulls:
                    logger.warning(
                        f"Column '{col}': {new_nulls - original_nulls} values could not be converted to numeric"
                    )

        return df

    @staticmethod
    def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with sensible defaults."""
        # Fill numeric columns
        numeric_defaults = {
            "purchases": 0,
            "revenue": 0,
            "spend": 0,
            "impressions": 0,
            "clicks": 0,
        }

        for col, default in numeric_defaults.items():
            if col in df.columns:
                nulls = df[col].isna().sum()
                if nulls > 0:
                    logger.warning(f"Filling {nulls} missing values in '{col}' with {default}")
                    df[col] = df[col].fillna(default)

        # Fill categorical columns
        categorical_defaults = {
            "campaign_name": "Unknown Campaign",
            "adset_name": "Unknown Adset",
            "creative_type": "unknown",
            "creative_message": "unknown",
            "platform": "unknown",
            "country": "unknown",
            "audience_type": "unknown",
        }

        for col, default in categorical_defaults.items():
            if col in df.columns:
                nulls = df[col].isna().sum()
                if nulls > 0:
                    logger.warning(f"Filling {nulls} missing values in '{col}' with '{default}'")
                    df[col] = df[col].fillna(default)

        return df

    @staticmethod
    def _handle_infinities(df: pd.DataFrame) -> pd.DataFrame:
        """Replace infinities with NaN."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                logger.warning(f"Column '{col}': Replacing {inf_count} infinity values with NaN")
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)

        return df

    @staticmethod
    def _compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Compute CTR and ROAS if not present or invalid."""
        # Compute CTR if missing or invalid
        if "ctr" not in df.columns or df["ctr"].isna().any():
            logger.info("Computing CTR from clicks and impressions")
            df["ctr"] = np.where(
                df["impressions"] > 0, df["clicks"] / df["impressions"], 0
            )

        # Compute ROAS if missing or invalid
        if "roas" not in df.columns or df["roas"].isna().any():
            logger.info("Computing ROAS from revenue and spend")
            df["roas"] = np.where(df["spend"] > 0, df["revenue"] / df["spend"], 0)

        return df

    @staticmethod
    def _validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
        """Validate that values are in sensible ranges."""
        # CTR should be between 0 and 1
        if "ctr" in df.columns:
            invalid_ctr = ((df["ctr"] < 0) | (df["ctr"] > 1)).sum()
            if invalid_ctr > 0:
                logger.warning(f"Found {invalid_ctr} rows with CTR outside [0, 1], clamping")
                df["ctr"] = df["ctr"].clip(0, 1)

        # Negative spend/revenue/clicks/impressions don't make sense
        non_negative_cols = ["spend", "revenue", "clicks", "impressions", "purchases"]
        for col in non_negative_cols:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    logger.warning(f"Found {negative_count} negative values in '{col}', setting to 0")
                    df[col] = df[col].clip(lower=0)

        # ROAS > 100 is suspicious (100x return is extremely unlikely)
        if "roas" in df.columns:
            suspicious_roas = (df["roas"] > 100).sum()
            if suspicious_roas > 0:
                logger.warning(f"Found {suspicious_roas} rows with ROAS > 100 (suspicious)")

        return df

    @staticmethod
    def _remove_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that are invalid after cleaning."""
        initial_len = len(df)

        # Remove rows with invalid dates
        df = df[df["date"].notna()]

        # Remove rows where all key metrics are 0 or missing
        key_metrics = ["spend", "impressions", "clicks", "revenue"]
        valid_mask = df[key_metrics].sum(axis=1) > 0
        df = df[valid_mask]

        removed = initial_len - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} invalid rows")

        return df

    @staticmethod
    def get_data_quality_report(df: pd.DataFrame) -> Dict:
        """Generate data quality report.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with quality metrics
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": {},
            "zero_values": {},
            "date_range": None,
            "data_quality_score": 0.0,
        }

        # Missing values per column
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                report["missing_values"][col] = {
                    "count": int(null_count),
                    "percentage": float(null_count / len(df) * 100),
                }

        # Zero values for key metrics
        key_metrics = ["spend", "impressions", "clicks", "revenue"]
        for col in key_metrics:
            if col in df.columns:
                zero_count = (df[col] == 0).sum()
                if zero_count > 0:
                    report["zero_values"][col] = {
                        "count": int(zero_count),
                        "percentage": float(zero_count / len(df) * 100),
                    }

        # Date range
        if "date" in df.columns:
            report["date_range"] = {
                "min": str(df["date"].min()),
                "max": str(df["date"].max()),
                "days": int((df["date"].max() - df["date"].min()).days),
            }

        # Calculate overall quality score (0-100)
        completeness = 1.0 - (df.isna().sum().sum() / (len(df) * len(df.columns)))
        report["data_quality_score"] = float(completeness * 100)

        return report
