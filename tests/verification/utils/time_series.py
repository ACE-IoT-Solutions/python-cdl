"""Time-series comparison utilities for verification testing.

This module provides functionality for comparing time-series data from simulations
against reference data, supporting configurable tolerances and detailed diagnostics.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator


class ToleranceSpec(BaseModel):
    """Specification for time-series comparison tolerances.

    Supports both absolute and relative tolerances, with configurable
    comparison modes for flexible verification testing.
    """

    absolute: float | None = Field(
        default=None,
        description="Absolute tolerance for comparison (e.g., 0.001)",
        ge=0.0,
    )
    relative: float | None = Field(
        default=None,
        description="Relative tolerance as a fraction (e.g., 0.01 for 1%)",
        ge=0.0,
        le=1.0,
    )
    mode: Literal["and", "or"] = Field(
        default="or",
        description="How to combine tolerances: 'and' requires both, 'or' requires either",
    )

    @field_validator("absolute", "relative")
    @classmethod
    def at_least_one_tolerance(cls, v: float | None, info) -> float | None:
        """Ensure at least one tolerance is specified."""
        # This validator will be called for both fields
        # We validate the complete object in model_validator below
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that at least one tolerance is specified."""
        if self.absolute is None and self.relative is None:
            raise ValueError("At least one of 'absolute' or 'relative' tolerance must be specified")

    @classmethod
    def from_absolute(cls, tolerance: float) -> "ToleranceSpec":
        """Create a tolerance spec with only absolute tolerance."""
        return cls(absolute=tolerance)

    @classmethod
    def from_relative(cls, tolerance: float) -> "ToleranceSpec":
        """Create a tolerance spec with only relative tolerance."""
        return cls(relative=tolerance)

    def check(self, actual: float, expected: float) -> bool:
        """Check if actual value is within tolerance of expected.

        Args:
            actual: Actual value from simulation
            expected: Expected value from reference

        Returns:
            True if within tolerance, False otherwise
        """
        if np.isnan(actual) or np.isnan(expected):
            # Handle NaN values - both must be NaN to pass
            return np.isnan(actual) and np.isnan(expected)

        checks = []

        if self.absolute is not None:
            abs_diff = abs(actual - expected)
            checks.append(abs_diff <= self.absolute)

        if self.relative is not None:
            # Avoid division by zero
            if expected == 0:
                # If expected is zero, use absolute difference
                rel_check = abs(actual - expected) <= self.relative
            else:
                rel_diff = abs((actual - expected) / expected)
                rel_check = rel_diff <= self.relative
            checks.append(rel_check)

        # Apply combination mode
        if self.mode == "and":
            return all(checks)
        else:  # mode == "or"
            return any(checks)


@dataclass
class ComparisonPoint:
    """Single point comparison result."""

    time: float
    actual: float
    expected: float
    absolute_error: float
    relative_error: float | None
    within_tolerance: bool


@dataclass
class TimeSeriesComparison:
    """Result of time-series comparison.

    Contains detailed diagnostics about the comparison including
    statistics and points that failed tolerance checks.
    """

    variable_name: str
    passed: bool
    tolerance: ToleranceSpec
    points_compared: int
    points_passed: int
    points_failed: int
    max_absolute_error: float
    max_relative_error: float | None
    mean_absolute_error: float
    mean_relative_error: float | None
    rmse: float
    failed_points: list[ComparisonPoint] = field(default_factory=list)
    statistics: dict[str, float] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """Calculate percentage of points that passed."""
        if self.points_compared == 0:
            return 0.0
        return (self.points_passed / self.points_compared) * 100.0

    def summary(self) -> str:
        """Generate a human-readable summary of the comparison."""
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"Variable: {self.variable_name}",
            f"Status: {status}",
            f"Points compared: {self.points_compared}",
            f"Pass rate: {self.pass_rate:.2f}%",
            f"Max absolute error: {self.max_absolute_error:.6e}",
            f"Mean absolute error (MAE): {self.mean_absolute_error:.6e}",
            f"Root mean squared error (RMSE): {self.rmse:.6e}",
        ]

        if self.max_relative_error is not None:
            lines.append(f"Max relative error: {self.max_relative_error:.6e}")
        if self.mean_relative_error is not None:
            lines.append(f"Mean relative error: {self.mean_relative_error:.6e}")

        if not self.passed and self.failed_points:
            lines.append(f"\nFirst {min(5, len(self.failed_points))} failed points:")
            for point in self.failed_points[:5]:
                lines.append(
                    f"  t={point.time:.3f}: actual={point.actual:.6e}, "
                    f"expected={point.expected:.6e}, "
                    f"abs_err={point.absolute_error:.6e}"
                )

        return "\n".join(lines)


def compare_time_series(
    time: np.ndarray,
    actual: np.ndarray,
    expected: np.ndarray,
    tolerance: ToleranceSpec,
    variable_name: str = "value",
    max_failed_points: int = 100,
) -> TimeSeriesComparison:
    """Compare two time series with configurable tolerances.

    Args:
        time: Time points (must match for both series)
        actual: Actual values from simulation
        expected: Expected values from reference
        tolerance: Tolerance specification
        variable_name: Name of variable being compared
        max_failed_points: Maximum number of failed points to store in result

    Returns:
        TimeSeriesComparison object with detailed results

    Raises:
        ValueError: If array shapes don't match
    """
    # Validate inputs
    if time.shape != actual.shape or time.shape != expected.shape:
        raise ValueError(
            f"Array shapes must match: time={time.shape}, "
            f"actual={actual.shape}, expected={expected.shape}"
        )

    n_points = len(time)
    if n_points == 0:
        raise ValueError("Cannot compare empty time series")

    # Calculate errors
    absolute_errors = np.abs(actual - expected)

    # Calculate relative errors (handle division by zero)
    with np.errstate(divide="ignore", invalid="ignore"):
        relative_errors = np.abs((actual - expected) / expected)
        # Replace inf/nan from division by zero
        relative_errors = np.where(
            expected == 0,
            np.where(actual == 0, 0.0, np.inf),
            relative_errors,
        )

    # Check each point against tolerance
    passed_mask = np.array(
        [tolerance.check(a, e) for a, e in zip(actual, expected, strict=False)]
    )

    points_passed = int(np.sum(passed_mask))
    points_failed = n_points - points_passed

    # Calculate statistics
    mae = float(np.mean(absolute_errors))
    rmse = float(np.sqrt(np.mean(absolute_errors**2)))
    max_abs_error = float(np.max(absolute_errors))

    # Calculate relative error stats (excluding inf values)
    valid_rel_errors = relative_errors[np.isfinite(relative_errors)]
    if len(valid_rel_errors) > 0:
        max_rel_error = float(np.max(valid_rel_errors))
        mean_rel_error = float(np.mean(valid_rel_errors))
    else:
        max_rel_error = None
        mean_rel_error = None

    # Collect failed points for diagnostics
    failed_indices = np.where(~passed_mask)[0]
    failed_points = []

    for idx in failed_indices[:max_failed_points]:
        point = ComparisonPoint(
            time=float(time[idx]),
            actual=float(actual[idx]),
            expected=float(expected[idx]),
            absolute_error=float(absolute_errors[idx]),
            relative_error=float(relative_errors[idx])
            if np.isfinite(relative_errors[idx])
            else None,
            within_tolerance=False,
        )
        failed_points.append(point)

    # Additional statistics
    statistics = {
        "min_actual": float(np.min(actual)),
        "max_actual": float(np.max(actual)),
        "mean_actual": float(np.mean(actual)),
        "std_actual": float(np.std(actual)),
        "min_expected": float(np.min(expected)),
        "max_expected": float(np.max(expected)),
        "mean_expected": float(np.mean(expected)),
        "std_expected": float(np.std(expected)),
    }

    return TimeSeriesComparison(
        variable_name=variable_name,
        passed=points_failed == 0,
        tolerance=tolerance,
        points_compared=n_points,
        points_passed=points_passed,
        points_failed=points_failed,
        max_absolute_error=max_abs_error,
        max_relative_error=max_rel_error,
        mean_absolute_error=mae,
        mean_relative_error=mean_rel_error,
        rmse=rmse,
        failed_points=failed_points,
        statistics=statistics,
    )
