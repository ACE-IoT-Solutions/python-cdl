# Python CDL Test Suite

Comprehensive test suite for the Python CDL (Controls Description Language) implementation.

## Quick Start

```bash
# Install dev dependencies
uv sync --group dev

# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=python_cdl --cov-report=html
```

## Test Organization

```
tests/
├── unit/           # Unit tests (57 tests)
├── integration/    # Integration tests (25 tests)
├── compliance/     # CDL spec compliance (11 tests)
└── fixtures/       # Test data (6 JSON files)
```

## Running Tests

### By Category
```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Compliance tests only
uv run pytest tests/compliance/ -v
```

### By Marker
```bash
# Run unit tests
uv run pytest -m unit

# Run integration tests
uv run pytest -m integration

# Run compliance tests
uv run pytest -m compliance

# Run edge case tests
uv run pytest -m edge_case
```

### Specific Tests
```bash
# Single file
uv run pytest tests/unit/test_data_types.py -v

# Single test
uv run pytest tests/unit/test_data_types.py::TestCDLDataTypes::test_real_parameter_valid -v

# Pattern matching
uv run pytest tests/ -k "parameter" -v
```

### Coverage Reports
```bash
# HTML report (opens in browser)
uv run pytest tests/ --cov=python_cdl --cov-report=html
open htmlcov/index.html

# Terminal report
uv run pytest tests/ --cov=python_cdl --cov-report=term-missing

# Both
uv run pytest tests/ --cov=python_cdl --cov-report=html --cov-report=term-missing
```

### Debugging
```bash
# Stop on first failure
uv run pytest tests/ -x

# Show local variables
uv run pytest tests/ -l

# Full traceback
uv run pytest tests/ --tb=long

# Enter debugger on failure
uv run pytest tests/ --pdb
```

## Test Statistics

- **Total Tests**: 93
- **Unit Tests**: 57 (61%)
- **Integration Tests**: 25 (27%)
- **Compliance Tests**: 11 (12%)
- **Test Fixtures**: 6 (4 valid, 2 invalid)

## Test Categories

### Unit Tests
- **test_data_types.py** (12 tests) - Parameter models
- **test_connectors.py** (14 tests) - Input/Output connectors
- **test_blocks.py** (13 tests) - Block models
- **test_edge_cases.py** (18 tests) - Edge cases and errors

### Integration Tests
- **test_parser.py** (13 tests) - CDL-JSON parsing
- **test_runtime.py** (12 tests) - Execution runtime

### Compliance Tests
- **test_cdl_standard.py** (11 tests) - CDL specification compliance

## Test Fixtures

Located in `tests/fixtures/`:

**Valid Fixtures**:
- `simple_block.json` - Simple proportional controller
- `elementary_block.json` - Elementary gain block
- `boolean_logic.json` - Boolean AND operation
- `composite_hvac.json` - PI controller with components

**Invalid Fixtures** (for negative testing):
- `invalid_circular.json` - Circular dependency
- `invalid_type_mismatch.json` - Type mismatch

## Configuration

### pytest.ini
Main pytest configuration with:
- Test discovery patterns
- Output formatting
- Markers definition
- Logging configuration

### conftest.py
Shared fixtures including:
- `fixtures_path` - Path to fixtures directory
- `load_fixture` - Factory for loading JSON fixtures
- Pre-loaded fixtures for common test data

## Writing New Tests

### Template
```python
import pytest
from pydantic import ValidationError

class TestNewFeature:
    """Test suite for new feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        from python_cdl.models import SomeModel

        instance = SomeModel(param="value")
        assert instance.param == "value"

    def test_validation_error(self):
        """Test that invalid input raises error."""
        from python_cdl.models import SomeModel

        with pytest.raises(ValidationError):
            SomeModel(param="invalid")
```

### Best Practices
1. Use descriptive test names (`test_what_when_expected`)
2. Include docstrings for all tests
3. Use appropriate markers
4. Test both success and failure paths
5. Use fixtures for common test data
6. Keep tests focused and independent
7. Aim for high coverage

## Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: |
    uv sync --group dev
    uv run pytest tests/ --cov=python_cdl --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Coverage Goals

| Module | Target | Status |
|--------|--------|--------|
| models/* | 100% | ⏳ Pending |
| parser/* | 95% | ⏳ Pending |
| runtime/* | 90% | ⏳ Pending |
| validators/* | 95% | ⏳ Pending |

## Documentation

- **TEST_REPORT.md** - Comprehensive test suite report
- **TEST_INVENTORY.md** - Complete listing of all tests
- **README.md** - This file

## Support

For issues or questions:
1. Check test documentation
2. Review CDL specification: https://obc.lbl.gov/specification/cdl.html
3. Check implementation code
4. Open an issue

## License

Same as parent project.
