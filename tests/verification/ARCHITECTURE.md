# Verification Framework Architecture

## Overview

The verification test framework provides comprehensive utilities for comparing python-cdl simulation results against reference implementations (e.g., Modelica). It supports time-series comparison with configurable tolerances, detailed diagnostics, and flexible data loading.

## Directory Structure

```
tests/verification/
├── ARCHITECTURE.md          # This file - framework documentation
├── conftest.py              # Pytest fixtures and configuration
├── utils/                   # Core verification utilities
│   ├── __init__.py         # Public API exports
│   ├── time_series.py      # Time-series comparison engine
│   ├── simulation.py       # CDL block simulation runner
│   ├── data_loaders.py     # Reference data loaders (CSV, JSON)
│   └── metrics.py          # Statistical comparison metrics
├── reference_data/          # Reference time-series data
│   ├── README.md           # Data format documentation
│   ├── elementary/         # Elementary block reference data
│   ├── composite/          # Composite block reference data
│   └── control_flow/       # Control flow block reference data
└── scenarios/               # Scenario-based verification tests
    └── __init__.py
```

## Core Components

### 1. Time-Series Comparison (`time_series.py`)

**Purpose**: Compare simulation outputs with reference data using configurable tolerances.

**Key Classes**:

- `ToleranceSpec`: Defines absolute and relative tolerances with AND/OR combination modes
- `TimeSeriesComparison`: Result object with detailed diagnostics
- `compare_time_series()`: Main comparison function

**Features**:
- Absolute and relative tolerance checking
- Point-by-point comparison with detailed error tracking
- Statistical metrics (MAE, RMSE, max error)
- Failed point diagnostics for debugging
- Flexible tolerance combination (AND/OR modes)

**Usage Example**:
```python
from tests.verification.utils import compare_time_series, ToleranceSpec
import numpy as np

# Define tolerance
tolerance = ToleranceSpec(absolute=1e-6, relative=1e-4, mode="or")

# Compare time series
result = compare_time_series(
    time=time_array,
    actual=simulation_output,
    expected=reference_output,
    tolerance=tolerance,
    variable_name="y"
)

# Check results
assert result.passed, result.summary()
```

### 2. Simulation Runner (`simulation.py`)

**Purpose**: Execute CDL blocks over time series for verification testing.

**Key Classes**:

- `SimulationConfig`: Configuration for time-series simulation
- `SimulationResult`: Container for simulation outputs
- `SimulationRunner`: Executes blocks with time-varying inputs

**Features**:
- Time-series execution with configurable step size
- Support for input functions of time
- Support for pre-defined input arrays
- Steady-state execution
- Metadata collection

**Usage Example**:
```python
from tests.verification.utils import SimulationRunner, SimulationConfig
import numpy as np

# Create runner
runner = SimulationRunner(my_block)

# Configure simulation
config = SimulationConfig(
    start_time=0.0,
    end_time=10.0,
    time_step=0.1
)

# Define inputs as functions of time
inputs = {
    "u": lambda t: np.sin(t),
    "setpoint": lambda t: 1.0
}

# Run simulation
result = runner.run_time_series(config, inputs, output_names=["y"])

# Access outputs
time = result.time
output = result.get_output("y")
```

### 3. Data Loaders (`data_loaders.py`)

**Purpose**: Load reference data from various file formats.

**Key Classes**:

- `ReferenceData`: Container for time-series data
- `CSVDataLoader`: Load from CSV files
- `JSONDataLoader`: Load from JSON files
- `ReferenceDataLoader`: Auto-detect format

**Supported Formats**:

**CSV Format**:
```csv
time,input_u,output_y
0.0,0.0,0.0
0.1,1.0,0.5
0.2,2.0,1.0
```

**JSON Format**:
```json
{
  "time": [0.0, 0.1, 0.2],
  "variables": {
    "input_u": [0.0, 1.0, 2.0],
    "output_y": [0.0, 0.5, 1.0]
  },
  "metadata": {
    "source": "Modelica",
    "tool": "OpenModelica"
  }
}
```

**Usage Example**:
```python
from tests.verification.utils import ReferenceDataLoader

# Load reference data (auto-detect format)
ref_data = ReferenceDataLoader.load("reference_data/limiter_test.csv")

# Access data
time, variables = ref_data.to_numpy()
output_y = ref_data.get_variable("output_y")
```

### 4. Metrics (`metrics.py`)

**Purpose**: Statistical metrics for quantifying comparison quality.

**Key Classes**:

- `ComparisonMetrics`: Comprehensive comparison statistics
- `StatisticalMetrics`: Descriptive statistics
- `calculate_metrics()`: Compute all metrics
- `detect_outliers()`: Identify anomalous points
- `sliding_window_metrics()`: Time-localized analysis

**Available Metrics**:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R-squared (coefficient of determination)
- Correlation coefficient
- MAPE (Mean Absolute Percentage Error)
- Error bands and confidence intervals

**Usage Example**:
```python
from tests.verification.utils.metrics import calculate_metrics

metrics = calculate_metrics(actual, expected)
print(f"MAE: {metrics.mae:.6e}")
print(f"RMSE: {metrics.rmse:.6e}")
print(f"R²: {metrics.r_squared:.4f}")
```

## Pytest Integration

### Fixtures

The framework provides several pytest fixtures in `conftest.py`:

- `verification_data_path`: Path to reference data directory
- `load_reference_data`: Factory to load reference data by name
- `default_tolerance`: Standard tolerance specification
- `strict_tolerance`: High-precision tolerance
- `relaxed_tolerance`: Less stringent tolerance
- `tolerance_spec`: Factory to create custom tolerances
- `simulation_runner`: Factory to create SimulationRunner instances

### Custom Markers

- `@pytest.mark.verification`: Verification tests
- `@pytest.mark.modelica`: Tests using Modelica reference data
- `@pytest.mark.tolerance_sensitive`: Tests sensitive to tolerance settings
- `@pytest.mark.time_series`: Tests involving time-series comparisons

### Test Example

```python
import pytest
import numpy as np

@pytest.mark.verification
@pytest.mark.time_series
def test_limiter_verification(load_reference_data, simulation_runner, default_tolerance):
    """Verify Limiter block against Modelica reference."""
    # Load block
    from python_cdl.parser import load_from_json
    block = load_from_json("blocks/limiter.json")

    # Load reference data
    ref_data = load_reference_data("elementary/limiter_basic.csv")
    ref_time, ref_vars = ref_data.to_numpy()

    # Run simulation
    runner = simulation_runner(block)
    inputs = {"u": ref_vars["input_u"]}
    result = runner.run_from_arrays(ref_time, inputs, ["y"])

    # Compare results
    from tests.verification.utils import compare_time_series
    comparison = compare_time_series(
        time=ref_time,
        actual=result.get_output("y"),
        expected=ref_vars["output_y"],
        tolerance=default_tolerance,
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()
```

## Design Principles

### 1. Pydantic-Based Data Models

All data structures use Pydantic for:
- Type validation
- Serialization/deserialization
- Clear API contracts
- IDE autocomplete support

### 2. Composability

Utilities are designed to be composed:
```python
# Load data
ref_data = ReferenceDataLoader.load("test.csv")

# Run simulation
runner = SimulationRunner(block)
result = runner.run_from_arrays(ref_data.time, ref_data.variables)

# Compare results
comparison = compare_time_series(
    result.time,
    result.get_output("y"),
    ref_data.get_variable("y"),
    tolerance
)
```

### 3. Detailed Diagnostics

All comparison results include:
- Pass/fail status
- Statistical metrics
- Failed point details
- Human-readable summaries

### 4. Flexible Tolerances

Support for multiple tolerance modes:
- Absolute only: `ToleranceSpec(absolute=1e-6)`
- Relative only: `ToleranceSpec(relative=1e-4)`
- Combined (OR): `ToleranceSpec(absolute=1e-6, relative=1e-4, mode="or")`
- Combined (AND): `ToleranceSpec(absolute=1e-6, relative=1e-4, mode="and")`

## Integration with Existing Tests

The framework integrates seamlessly with existing python-cdl test infrastructure:

1. **Follows patterns from** `tests/conftest.py`:
   - Factory fixtures
   - JSON fixture loading
   - Pytest markers

2. **Uses existing runtime components**:
   - `ExecutionContext`
   - `BlockExecutor`
   - `Block` models

3. **Compatible with existing blocks**:
   - Works with any `Block` subclass
   - Supports elementary and composite blocks
   - Handles control flow blocks

## Dependencies

New dependencies added to `pyproject.toml`:
- `pandas>=2.2.0`: CSV data loading
- `scipy>=1.14.0`: Statistical functions

Existing dependencies used:
- `numpy`: Numerical operations
- `pydantic`: Data models
- `pytest`: Testing framework

## Future Enhancements

Potential extensions:
1. **Visualization**: Plot comparison results with matplotlib
2. **Parallel testing**: Run multiple scenarios concurrently
3. **Fuzzing**: Generate test cases automatically
4. **Regression detection**: Track metrics over time
5. **Benchmark suite**: Performance comparison tests
6. **Continuous integration**: Automated verification on PRs

## Related Patterns

This framework was inspired by:
- **Funnel tool**: Modelica verification testing tool
- **pytest-benchmark**: Performance testing patterns
- **numpy.testing**: Array comparison utilities
- **scipy.stats**: Statistical testing methods
