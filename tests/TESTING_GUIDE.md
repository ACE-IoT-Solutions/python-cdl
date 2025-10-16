# Testing Guide for Python CDL

## Overview

This guide provides complete instructions for testing the Python CDL implementation.

## Test Suite Summary

- **93 tests** across 7 test files
- **2,058 lines** of test code
- **6 fixtures** (4 valid, 2 invalid)
- **3 categories**: Unit, Integration, Compliance
- **Coverage goal**: 90%+ overall

## Quick Commands

```bash
# Run all tests
uv run pytest tests/

# Run with coverage (recommended)
uv run pytest tests/ --cov=python_cdl --cov-report=html --cov-report=term-missing

# Run fast tests only (skip slow)
uv run pytest tests/ -m "not slow"

# Run specific category
uv run pytest -m unit      # Unit tests
uv run pytest -m integration  # Integration tests
uv run pytest -m compliance   # Compliance tests
```

## Test Categories Explained

### Unit Tests (57 tests)
Tests individual components in isolation:
- **Data Types**: Parameter validation and serialization
- **Connectors**: Input/Output models and validation
- **Blocks**: Block models and structure
- **Edge Cases**: Boundary conditions and error handling

### Integration Tests (25 tests)
Tests complete workflows:
- **Parser**: CDL-JSON parsing and validation
- **Runtime**: Block execution and computation

### Compliance Tests (11 tests)
Validates CDL specification compliance:
- Synchronous data flow
- Single assignment rule
- Type system
- Acyclic dependencies
- Connection rules
- Metadata handling

## Test Fixtures

Located in `tests/fixtures/`:

### Valid Examples
1. **simple_block.json** - Basic proportional controller
2. **elementary_block.json** - Elementary gain block
3. **boolean_logic.json** - Boolean operations
4. **composite_hvac.json** - Complex PI controller

### Invalid Examples (Negative Testing)
5. **invalid_circular.json** - Tests circular dependency detection
6. **invalid_type_mismatch.json** - Tests type validation

## Understanding Test Output

### Success
```
tests/unit/test_data_types.py::TestCDLDataTypes::test_real_parameter_valid PASSED
```

### Failure
```
tests/unit/test_data_types.py::TestCDLDataTypes::test_real_parameter_valid FAILED
    AssertionError: assert 1.0 == 2.0
```

### Skip
```
tests/unit/test_edge_cases.py::TestEdgeCases::test_array_bounds SKIPPED
    Reason: Array support not implemented
```

## Coverage Report

After running with `--cov`, check:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Coverage metrics to monitor:
- **Lines**: Percentage of code lines executed
- **Branches**: Percentage of conditional branches taken
- **Missing**: Lines not covered by tests

## Debugging Failed Tests

### 1. Get more details
```bash
uv run pytest tests/unit/test_data_types.py::TestCDLDataTypes::test_real_parameter_valid -vv
```

### 2. Show local variables
```bash
uv run pytest tests/ -l
```

### 3. Enter debugger
```bash
uv run pytest tests/ --pdb
```

### 4. Full traceback
```bash
uv run pytest tests/ --tb=long
```

## Adding New Tests

### 1. Choose location
- `tests/unit/` - Testing individual functions/classes
- `tests/integration/` - Testing complete workflows
- `tests/compliance/` - Testing specification compliance

### 2. Follow naming convention
- File: `test_<feature>.py`
- Class: `Test<Feature>`
- Method: `test_<what>_<when>_<expected>`

### 3. Use fixtures
```python
def test_with_fixture(simple_block_json):
    """Test using shared fixture."""
    block = parse_cdl_json(simple_block_json)
    assert block.modelName == "SimpleController"
```

### 4. Add markers
```python
@pytest.mark.slow
def test_large_model():
    """Test with large CDL model."""
    pass
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --group dev
      - run: uv run pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Common Issues

### Import Errors
**Problem**: `ImportError: cannot import name 'CDLBlock'`
**Solution**: Check actual implementation names (may be `Block` not `CDLBlock`)

### Fixture Not Found
**Problem**: `fixture 'simple_block_json' not found`
**Solution**: Ensure `conftest.py` is in the same directory or parent

### Pydantic Validation Errors
**Problem**: `ValidationError: 1 validation error for Parameter`
**Solution**: Check required fields and types match Pydantic model

## Performance

### Test Execution Time
- Unit tests: < 5 seconds
- Integration tests: < 10 seconds
- Compliance tests: < 5 seconds
- **Total**: ~20 seconds

### Parallel Execution
```bash
# Install pytest-xdist
uv add --group dev pytest-xdist

# Run in parallel
uv run pytest tests/ -n auto
```

## Test Maintenance

### Weekly
- Run full test suite with coverage
- Review any skipped tests
- Update fixtures if spec changes

### Per PR
- Run affected tests
- Ensure new features have tests
- Maintain >90% coverage

### Monthly
- Review test execution times
- Refactor slow tests
- Update test documentation

## Best Practices

1. **Write tests first** (TDD) - Define expected behavior
2. **Keep tests focused** - One concept per test
3. **Use descriptive names** - Clear intent from name
4. **Test edge cases** - Not just happy path
5. **Mock external deps** - Fast, reliable tests
6. **Keep tests independent** - No execution order dependency
7. **Maintain fixtures** - Keep test data realistic
8. **Document complex tests** - Explain why, not what

## Resources

- **CDL Specification**: https://obc.lbl.gov/specification/cdl.html
- **Pytest Documentation**: https://docs.pytest.org/
- **Pydantic Testing**: https://docs.pydantic.dev/latest/testing/
- **Test Reports**: See `TEST_REPORT.md` and `TEST_INVENTORY.md`

## Getting Help

1. Check test documentation in this directory
2. Review CDL specification
3. Examine existing test examples
4. Check implementation code comments
5. Open an issue with test output

## Summary

This comprehensive test suite ensures:
- ✅ Correct implementation of CDL specification
- ✅ Type safety through Pydantic validation
- ✅ Robust error handling
- ✅ Edge case coverage
- ✅ Integration correctness
- ✅ Backward compatibility

Run tests regularly and maintain high coverage!
