"""Statistical metrics for time-series comparison.

This module provides common statistical metrics used in verification testing
to quantify the difference between simulation results and reference data.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field


class ComparisonMetrics(BaseModel):
    """Statistical metrics for comparing two time series."""

    mae: float = Field(description="Mean Absolute Error")
    rmse: float = Field(description="Root Mean Squared Error")
    max_error: float = Field(description="Maximum absolute error")
    mean_error: float = Field(description="Mean signed error (bias)")
    std_error: float = Field(description="Standard deviation of error")
    r_squared: float | None = Field(
        default=None,
        description="R-squared (coefficient of determination)",
    )
    correlation: float | None = Field(
        default=None,
        description="Pearson correlation coefficient",
    )
    mape: float | None = Field(
        default=None,
        description="Mean Absolute Percentage Error (if no zero values)",
    )

    class Config:
        """Pydantic config."""

        frozen = True  # Make immutable


@dataclass
class StatisticalMetrics:
    """Statistical analysis of time series."""

    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float  # 25th percentile
    q75: float  # 75th percentile
    n_points: int


def calculate_metrics(
    actual: np.ndarray,
    expected: np.ndarray,
    mask: np.ndarray | None = None,
) -> ComparisonMetrics:
    """Calculate comprehensive comparison metrics.

    Args:
        actual: Actual values from simulation
        expected: Expected values from reference
        mask: Optional boolean mask to exclude certain points

    Returns:
        ComparisonMetrics object with all statistics

    Raises:
        ValueError: If arrays have different shapes
    """
    if actual.shape != expected.shape:
        raise ValueError(
            f"Array shapes must match: actual={actual.shape}, expected={expected.shape}"
        )

    # Apply mask if provided
    if mask is not None:
        actual = actual[mask]
        expected = expected[mask]

    # Calculate errors
    errors = actual - expected
    abs_errors = np.abs(errors)
    squared_errors = errors**2

    # Basic metrics
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(squared_errors)))
    max_error = float(np.max(abs_errors))
    mean_error = float(np.mean(errors))
    std_error = float(np.std(errors))

    # R-squared
    ss_res = np.sum(squared_errors)
    ss_tot = np.sum((expected - np.mean(expected)) ** 2)
    r_squared = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else None

    # Correlation coefficient
    if np.std(actual) > 0 and np.std(expected) > 0:
        correlation = float(np.corrcoef(actual, expected)[0, 1])
    else:
        correlation = None

    # MAPE (only if no zero values in expected)
    if not np.any(expected == 0):
        mape = float(np.mean(np.abs((actual - expected) / expected)) * 100)
    else:
        mape = None

    return ComparisonMetrics(
        mae=mae,
        rmse=rmse,
        max_error=max_error,
        mean_error=mean_error,
        std_error=std_error,
        r_squared=r_squared,
        correlation=correlation,
        mape=mape,
    )


def calculate_statistics(data: np.ndarray) -> StatisticalMetrics:
    """Calculate descriptive statistics for a time series.

    Args:
        data: Time series data

    Returns:
        StatisticalMetrics object
    """
    return StatisticalMetrics(
        mean=float(np.mean(data)),
        std=float(np.std(data)),
        min=float(np.min(data)),
        max=float(np.max(data)),
        median=float(np.median(data)),
        q25=float(np.percentile(data, 25)),
        q75=float(np.percentile(data, 75)),
        n_points=len(data),
    )


def compute_error_bands(
    actual: np.ndarray,
    expected: np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute confidence bands for errors.

    Args:
        actual: Actual values
        expected: Expected values
        confidence: Confidence level (default: 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound) scalars
    """
    errors = actual - expected
    mean_error = np.mean(errors)
    std_error = np.std(errors)

    # Calculate z-score for confidence level using standard normal distribution
    # For 95% confidence, z ≈ 1.96
    z = 1.96 if confidence == 0.95 else (
        2.576 if confidence == 0.99 else
        1.645  # 90% confidence
    )

    lower_bound = float(mean_error - z * std_error)
    upper_bound = float(mean_error + z * std_error)

    return lower_bound, upper_bound


def detect_outliers(
    actual: np.ndarray,
    expected: np.ndarray,
    method: Literal["iqr", "zscore"] = "iqr",
    threshold: float = 1.5,
) -> np.ndarray:
    """Detect outlier points in the comparison.

    Args:
        actual: Actual values
        expected: Expected values
        method: Outlier detection method ('iqr' or 'zscore')
        threshold: Threshold for outlier detection (1.5 for IQR, 3.0 for z-score)

    Returns:
        Boolean array where True indicates outliers
    """
    errors = np.abs(actual - expected)
    outliers: np.ndarray

    if method == "iqr":
        q25, q75 = np.percentile(errors, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - threshold * iqr
        upper_bound = q75 + threshold * iqr
        outliers = (errors < lower_bound) | (errors > upper_bound)
    elif method == "zscore":
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        z_scores = np.abs((errors - mean_error) / std_error)
        outliers = z_scores > threshold
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

    return outliers


def sliding_window_metrics(
    actual: np.ndarray,
    expected: np.ndarray,
    window_size: int,
    stride: int = 1,
) -> list[ComparisonMetrics]:
    """Calculate metrics over sliding windows.

    Useful for analyzing how error varies over time.

    Args:
        actual: Actual values
        expected: Expected values
        window_size: Size of sliding window
        stride: Stride between windows

    Returns:
        List of ComparisonMetrics for each window
    """
    metrics_list = []
    n_points = len(actual)

    for start in range(0, n_points - window_size + 1, stride):
        end = start + window_size
        window_actual = actual[start:end]
        window_expected = expected[start:end]

        metrics = calculate_metrics(window_actual, window_expected)
        metrics_list.append(metrics)

    return metrics_list
