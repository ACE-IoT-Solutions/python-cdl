"""Verification test utilities for python-cdl.

This module provides utilities for time-series comparison and verification testing
against reference implementations (e.g., Modelica).
"""

from .data_loaders import CSVDataLoader, JSONDataLoader, ReferenceData, ReferenceDataLoader
from .metrics import (
    ComparisonMetrics,
    StatisticalMetrics,
    calculate_metrics,
    calculate_statistics,
)
from .simulation import SimulationConfig, SimulationResult, SimulationRunner
from .time_series import TimeSeriesComparison, ToleranceSpec, compare_time_series
from .unit_conversion import (
    UnitConverter,
    VariableMapping,
    PointMapping,
    kelvin_to_fahrenheit,
    fahrenheit_to_kelvin,
    kelvin_to_celsius,
    celsius_to_kelvin,
    fraction_to_percent,
    percent_to_fraction,
    pascal_to_inches_water,
    inches_water_to_pascal,
)

__all__ = [
    # Time-series comparison
    "TimeSeriesComparison",
    "ToleranceSpec",
    "compare_time_series",
    # Simulation
    "SimulationConfig",
    "SimulationResult",
    "SimulationRunner",
    # Data loaders
    "CSVDataLoader",
    "JSONDataLoader",
    "ReferenceData",
    "ReferenceDataLoader",
    # Metrics
    "ComparisonMetrics",
    "StatisticalMetrics",
    "calculate_metrics",
    "calculate_statistics",
    # Unit conversion
    "UnitConverter",
    "VariableMapping",
    "PointMapping",
    "kelvin_to_fahrenheit",
    "fahrenheit_to_kelvin",
    "kelvin_to_celsius",
    "celsius_to_kelvin",
    "fraction_to_percent",
    "percent_to_fraction",
    "pascal_to_inches_water",
    "inches_water_to_pascal",
]
