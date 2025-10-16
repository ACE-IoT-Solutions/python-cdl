"""
Pytest configuration and shared fixtures for CDL tests.

This file contains shared fixtures and configuration used across all test modules.
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict


@pytest.fixture
def fixtures_path() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixtures_path):
    """Factory fixture to load JSON fixtures by name."""
    def _load(filename: str) -> Dict[str, Any]:
        filepath = fixtures_path / filename
        with open(filepath) as f:
            return json.load(f)
    return _load


@pytest.fixture
def simple_block_json(load_fixture):
    """Load simple block fixture."""
    return load_fixture("simple_block.json")


@pytest.fixture
def elementary_block_json(load_fixture):
    """Load elementary block fixture."""
    return load_fixture("elementary_block.json")


@pytest.fixture
def boolean_logic_json(load_fixture):
    """Load boolean logic fixture."""
    return load_fixture("boolean_logic.json")


@pytest.fixture
def composite_hvac_json(load_fixture):
    """Load composite HVAC fixture."""
    return load_fixture("composite_hvac.json")


@pytest.fixture
def invalid_circular_json(load_fixture):
    """Load invalid circular dependency fixture."""
    return load_fixture("invalid_circular.json")


@pytest.fixture
def invalid_type_mismatch_json(load_fixture):
    """Load invalid type mismatch fixture."""
    return load_fixture("invalid_type_mismatch.json")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for complete workflows")
    config.addinivalue_line("markers", "compliance: CDL specification compliance tests")
    config.addinivalue_line("markers", "slow: Tests that take significant time to run")
    config.addinivalue_line("markers", "edge_case: Edge case and error handling tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "compliance" in str(item.fspath):
            item.add_marker(pytest.mark.compliance)

        # Mark edge case tests
        if "edge_case" in item.name.lower():
            item.add_marker(pytest.mark.edge_case)
