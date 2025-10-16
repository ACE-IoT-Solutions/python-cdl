"""Pytest configuration for verification tests.

This module provides fixtures for loading reference data, configuring
tolerances, and running simulations for verification testing.
"""

from pathlib import Path

import pytest

from tests.verification.utils import (
    CSVDataLoader,
    JSONDataLoader,
    ReferenceDataLoader,
    SimulationRunner,
    ToleranceSpec,
)


@pytest.fixture
def verification_data_path() -> Path:
    """Return the path to verification reference data directory."""
    return Path(__file__).parent / "reference_data"


@pytest.fixture
def load_reference_data(verification_data_path):
    """Factory fixture to load reference data by name.

    Returns a function that loads reference data from the reference_data directory.
    Automatically detects file format (CSV or JSON) based on extension.

    Usage:
        def test_something(load_reference_data):
            ref_data = load_reference_data("my_test_case")
            # Use ref_data...
    """

    def _load(name: str, format: str | None = None):
        """Load reference data file.

        Args:
            name: Name of reference data file (without extension if format not specified)
            format: Optional file format ('csv' or 'json'), auto-detected if not provided

        Returns:
            ReferenceData object
        """
        if format:
            filepath = verification_data_path / f"{name}.{format}"
            if format == "csv":
                return CSVDataLoader.load(filepath)
            elif format == "json":
                return JSONDataLoader.load(filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
        else:
            # Try to auto-detect
            return ReferenceDataLoader.load(verification_data_path / name)

    return _load


@pytest.fixture
def default_tolerance() -> ToleranceSpec:
    """Default tolerance specification for verification tests.

    Returns a moderate tolerance suitable for most comparisons.
    Individual tests can override this as needed.
    """
    return ToleranceSpec(absolute=1e-6, relative=1e-4, mode="or")


@pytest.fixture
def strict_tolerance() -> ToleranceSpec:
    """Strict tolerance specification for high-precision tests."""
    return ToleranceSpec(absolute=1e-9, relative=1e-6, mode="and")


@pytest.fixture
def relaxed_tolerance() -> ToleranceSpec:
    """Relaxed tolerance specification for less critical comparisons."""
    return ToleranceSpec(absolute=1e-3, relative=1e-2, mode="or")


@pytest.fixture
def tolerance_spec():
    """Factory fixture to create custom tolerance specifications.

    Usage:
        def test_something(tolerance_spec):
            tol = tolerance_spec(absolute=1e-6, relative=1e-4)
            # Use tolerance...
    """

    def _create(**kwargs) -> ToleranceSpec:
        return ToleranceSpec(**kwargs)

    return _create


@pytest.fixture
def simulation_runner():
    """Factory fixture to create SimulationRunner instances.

    Usage:
        def test_something(simulation_runner):
            runner = simulation_runner(my_block)
            result = runner.run_time_series(...)
    """

    def _create(block) -> SimulationRunner:
        return SimulationRunner(block)

    return _create


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers for verification tests."""
    config.addinivalue_line(
        "markers",
        "verification: Verification tests comparing against reference implementations",
    )
    config.addinivalue_line(
        "markers",
        "modelica: Verification tests using Modelica reference data",
    )
    config.addinivalue_line(
        "markers",
        "tolerance_sensitive: Tests sensitive to tolerance settings",
    )
    config.addinivalue_line(
        "markers",
        "time_series: Tests involving time-series comparisons",
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark verification tests."""
    for item in items:
        # Mark all tests in verification directory
        if "verification" in str(item.fspath):
            item.add_marker(pytest.mark.verification)

        # Mark time-series tests
        if "time_series" in item.name.lower() or "simulation" in item.name.lower():
            item.add_marker(pytest.mark.time_series)
