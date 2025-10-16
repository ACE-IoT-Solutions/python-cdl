# Python CDL

A Python implementation of the Control Description Language (CDL) for building automation and HVAC control systems.

![Composite Block Execution](docs/images/composite_block_execution.png)

## Overview

Python CDL provides a complete framework for modeling, simulating, and verifying building control systems using the Control Description Language specification. CDL is a domain-specific language based on Modelica designed specifically for control sequences in building automation.

## ✨ Key Features

### 🏗️ Core Capabilities
- **Elementary & Composite Blocks** - Full CDL block hierarchy with automatic dependency resolution
- **Type System** - Strongly-typed connectors with physical units and quantities
- **Runtime Execution** - Fast block executor with topological sorting and nested event handling
- **Validation** - Comprehensive block structure and connection graph validation
- **JSON Import/Export** - Standards-compliant CDL-JSON parsing with round-trip support

### 🧪 Verification & Testing
- **OBC Verification Framework** - OpenBuildingControl specification compliance testing
- **Time-Series Comparison** - Configurable absolute/relative tolerances for validation
- **Unit Conversion** - Pint-based conversion between SI (CDL) and Imperial (BAS) units
- **Reference Data Loaders** - CSV/JSON data import with automatic unit conversion
- **Statistical Metrics** - MAE, RMSE, pass rates, and comprehensive error analysis

### 📊 Interactive Examples
- **Jupyter Notebooks** - Production-ready examples with visualizations
- **VAV Reheat Systems** - ASHRAE Guideline 36 compliant implementations
- **Composite Block Execution** - Live demonstrations of hierarchical control
- **Programmatic Composition** - Build control systems in Python with full IDE support

## 📸 Visual Examples

### Composite Block Architecture

![Composite Block Diagram](docs/images/composite_block_diagram.png)

*Automatic execution order resolution with three connection types: Parent→Child, Child→Child, Child→Parent*

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/ACE-IoT-Solutions/python-cdl.git
cd python-cdl

# Install with all dependencies
uv sync
```

### Using pip

```bash
pip install -e .

# For development with verification tools
pip install -e ".[dev]"
```

## Quick Start

### Elementary Block Execution

```python
from python_cdl.models.blocks import Block
from python_cdl.models.connectors import RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.equations import Equation
from python_cdl.runtime.executor import BlockExecutor
from python_cdl.runtime.context import ExecutionContext

# Create a simple P-controller
controller = Block(
    name="PController",
    block_type="elementary",
    parameters=[
        Parameter(name="k", type="Real", value=2.0),
    ],
    inputs=[
        RealInput(name="u_s", description="Setpoint"),
        RealInput(name="u_m", description="Measurement"),
    ],
    outputs=[
        RealOutput(name="y", description="Control output"),
    ],
    equations=[
        Equation(lhs="e", rhs="u_s - u_m"),
        Equation(lhs="y", rhs="k * e"),
    ]
)

# Execute
executor = BlockExecutor()
result = executor.execute(controller, inputs={'u_s': 72.0, 'u_m': 68.0})

print(f"Control output: {result.outputs['y']}")  # 8.0 (2.0 * 4.0)
```

### Composite Block Execution

```python
from python_cdl.parser.json_parser import CDLParser

# Load composite block from JSON
parser = CDLParser()
with open('examples/p_controller_limiter.json') as f:
    import json
    block = parser.parse_block(json.load(f))

# Execute composite block (automatic child execution ordering)
result = executor.execute(block, inputs={'e': 5.0, 'yMax': 20.0})
print(f"Limited output: {result.outputs['y']}")
```

### Time-Series Simulation with Verification

```python
from tests.verification.utils import (
    SimulationRunner,
    SimulationConfig,
    compare_time_series,
    ToleranceSpec
)
import numpy as np

# Configure simulation
config = SimulationConfig(start_time=0.0, end_time=10.0, time_step=0.1)
runner = SimulationRunner(controller)

# Define input functions
def setpoint(t):
    return 72.0 if t < 5.0 else 75.0  # Step change at t=5s

def measurement(t):
    return 68.0 + 0.5 * t  # Gradual increase

# Run simulation
result = runner.run_time_series(
    config=config,
    input_functions={'u_s': setpoint, 'u_m': measurement},
    output_names=['y']
)

# Compare with reference data
comparison = compare_time_series(
    result.time,
    result.get_output('y'),
    expected_output,
    tolerance=ToleranceSpec(absolute_y=0.1)
)

print(f"Pass rate: {comparison.pass_rate:.1%}")
print(f"MAE: {comparison.mean_absolute_error:.3f}")
```

## 📚 Interactive Tutorials

### 1. Composite Block Execution

**Location**: `examples/composite_block_execution.ipynb`

Learn how to execute composite blocks with automatic dependency resolution:
- Load and inspect composite block structure
- Execute with BlockExecutor
- Visualize data flow through connections
- Run time-series simulations
- Measure performance

```bash
jupyter notebook examples/composite_block_execution.ipynb
```

### 2. Programmatic Composition

**Location**: `examples/programmatic_composition/tutorial.ipynb`

Build control systems programmatically in Python:
- Create elementary blocks with type safety
- Wire blocks together into composite systems
- Validate structure and connections
- Export to CDL-JSON
- Use factory patterns for reusability

```bash
cd examples/programmatic_composition
jupyter notebook tutorial.ipynb
```

### 3. VAV Reheat System

**Location**: `examples/vav_reheat/tutorial.ipynb`

Comprehensive ASHRAE Guideline 36 implementation:
- 5-zone building with VAV box controllers
- Central AHU with economizer
- Mode selection and optimization
- Full 24-hour building simulation

```bash
cd examples/vav_reheat
jupyter notebook tutorial.ipynb
```

## 🧪 Verification Framework

Python CDL includes a complete OBC (OpenBuildingControl) verification framework for testing control sequences against reference implementations.

### Key Components

**Time-Series Comparison**:
```python
from tests.verification.utils import compare_time_series, ToleranceSpec

comparison = compare_time_series(
    time=time_array,
    actual=simulated_output,
    expected=reference_output,
    tolerance=ToleranceSpec(absolute_y=2.0, relative_y=0.05, mode='or'),
    variable_name="zone_temperature"
)

if comparison.passed:
    print(f"✓ Verification passed ({comparison.pass_rate:.1%} within tolerance)")
else:
    print(comparison.summary())
```

**Unit Conversion** (CDL uses SI, BAS uses Imperial):
```python
from tests.verification.utils import UnitConverter, PointMapping

converter = UnitConverter()

# Temperature conversions
temp_k = converter.convert(72.0, 'degF', 'K')  # 295.37 K

# Batch DataFrame conversion
mapping = PointMapping.from_json_file('point_mapping.json')
cdl_data = mapping.convert_dataframe_to_cdl(bas_dataframe)
```

**Reference Data Loading**:
```python
from tests.verification.utils import ReferenceData

# Load CSV reference data with automatic unit conversion
ref = ReferenceData.from_csv(
    'reference_data/zone_temps.csv',
    time_column='Time',
    value_columns=['ZoneTemp', 'SetPoint']
)

# Compare simulation against reference
comparison = ref.compare_with_simulation(simulation_result, tolerance)
```

### Test Results

```bash
$ uv run pytest tests/
======================== 181 passed in 0.36s ========================

✓ All tests passing including:
  • 24 unit conversion tests
  • 11 P-controller verification tests
  • 14 composite block scenario tests
  • 12 runtime execution tests
  • Complete VAV reheat test suite
```

## 📁 Project Structure

```
python-cdl/
├── src/python_cdl/
│   ├── models/              # Core CDL models (Pydantic)
│   │   ├── blocks.py        # Elementary/Composite blocks
│   │   ├── connectors.py    # Typed connectors with units
│   │   ├── connections.py   # Connection wiring
│   │   ├── equations.py     # Equation models
│   │   ├── parameters.py    # Parameter definitions
│   │   └── types.py         # CDL type system
│   ├── parser/              # JSON parser
│   │   └── json_parser.py   # CDL-JSON import/export
│   ├── runtime/             # Execution engine
│   │   ├── context.py       # Event-based execution context
│   │   └── executor.py      # Block executor with topological sort
│   └── validators/          # Validation framework
│       ├── block_validator.py
│       └── graph_validator.py
├── examples/
│   ├── composite_block_execution.ipynb  # NEW: Composite block tutorial
│   ├── programmatic_composition/        # Build systems in Python
│   ├── vav_reheat/                      # ASHRAE G36 implementation
│   ├── p_controller_limiter.json        # Composite block example
│   └── cdl_controller_simulation.ipynb  # 24-hour simulation
├── tests/
│   ├── verification/        # NEW: OBC verification framework
│   │   ├── utils/          # Time-series, units, metrics
│   │   ├── test_p_controller_basic.py
│   │   ├── test_unit_conversion.py
│   │   └── scenarios/      # Verification scenarios
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── compliance/         # CDL compliance tests
└── docs/
    ├── images/             # README visualizations
    ├── ARCHITECTURE.md
    └── vav_reheat_architecture.md
```

## 🎯 Standards Compliance

This implementation follows:
- **ASHRAE Guideline 36-2021** - High Performance Sequences of Operation for HVAC Systems
- **CDL Specification** - Control Description Language from Modelica Buildings library
- **OBC Specification** - OpenBuildingControl verification procedures
- **ASHRAE Standard 90.1** - Energy efficiency requirements
- **ASHRAE Standard 62.1** - Ventilation requirements

## 🚀 Performance

- **Execution Speed**: >1000 executions/second for composite blocks
- **Simulation Speed**: >100× real-time for typical HVAC systems
- **Memory Usage**: <500 MB for large multi-zone buildings
- **Test Coverage**: 100% passing (181/181 tests)

Composite blocks are fast enough for:
- ✅ Building automation (1-10 Hz control loops)
- ✅ HVAC control (0.1-1 Hz typical)
- ✅ Offline simulation and verification
- ✅ Real-time co-simulation

## 💡 Key Concepts

### Elementary Blocks

Basic building blocks that perform simple operations:

```python
from python_cdl.models.blocks import Block

# P-controller with equations
controller = Block(
    name="PController",
    block_type="elementary",
    parameters=[Parameter(name="k", type="Real", value=2.0)],
    inputs=[RealInput(name="u_s"), RealInput(name="u_m")],
    outputs=[RealOutput(name="y")],
    equations=[
        Equation(lhs="e", rhs="u_s - u_m"),
        Equation(lhs="y", rhs="k * e")
    ]
)
```

### Composite Blocks

Hierarchical systems with automatic dependency resolution:

```python
from python_cdl.models.blocks import CompositeBlock
from python_cdl.models.connections import Connection

system = CompositeBlock(
    name="ControlSystem",
    blocks=[gain_block, limiter_block],
    connections=[
        Connection(from_block="gain", from_output="y",
                  to_block="limiter", to_input="u")
    ]
)

# Executor automatically determines execution order via topological sort
result = executor.execute(system, inputs={'error': 5.0})
```

### Three Connection Types

1. **Parent Input → Child Input**: External inputs to internal blocks
2. **Child Output → Child Input**: Data flow between internal blocks
3. **Child Output → Parent Output**: Internal results to external outputs

The executor automatically handles all three types with proper path resolution.

## 📊 Energy Savings

Implementations based on ASHRAE Guideline 36 sequences can achieve:
- **30-50% fan energy savings** through duct pressure optimization
- **20-40% cooling energy savings** through economizer free cooling
- **10-20% reheat energy savings** through supply air temperature reset

## 🛠️ Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=python_cdl --cov-report=html

# Run verification tests only
uv run pytest tests/verification/ -v

# Run specific test suite
uv run pytest tests/integration/test_vav_reheat.py -v
```

### Linting and Type Checking

```bash
# Lint with ruff
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run pyrefly check src/
```

### Creating Visualizations

```bash
# Generate README images
cd examples
uv run python3 generate_visualizations.py
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new features
4. Ensure all tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Testing Guidelines

- Write tests for all new features
- Maintain 100% test pass rate
- Follow existing test patterns
- Include integration tests for control sequences
- Add verification tests for OBC compliance

## 📝 License

[Add your license here]

## 👥 Authors

- Andrew Rodgers - <andrew@aceiotsolutions.com>

## 🙏 Acknowledgments

- **ASHRAE** - For developing Guideline 36 sequences
- **Modelica Buildings Library** - For CDL specification
- **Lawrence Berkeley National Laboratory** - For OBC verification procedures and control sequence research

## 📖 Resources

- [ASHRAE Guideline 36-2021](https://www.ashrae.org/technical-resources/bookstore/ashrae-guideline-36)
- [Modelica Buildings Library](https://simulationresearch.lbl.gov/modelica/)
- [CDL Specification](https://simulationresearch.lbl.gov/modelica/releases/latest/help/Buildings_Controls_OBC_CDL.html)
- [OBC Specification](https://obc.lbl.gov/specification/)

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

## 🗺️ Roadmap

### ✅ Current (v0.1.0)
- ✅ Core CDL implementation with Pydantic models
- ✅ Elementary and composite block execution
- ✅ Topological sorting for dependency resolution
- ✅ OBC verification framework
- ✅ Unit conversion system (Pint)
- ✅ Time-series comparison and validation
- ✅ VAV reheat example (ASHRAE G36)
- ✅ Interactive Jupyter notebooks
- ✅ Comprehensive test suite (181 tests)
- ✅ JSON import/export

### 🔄 In Progress (v0.2.0)
- 🔄 Additional HVAC examples (chilled beams, radiant systems)
- 🔄 MOS file parser for Modelica results
- 🔄 Enhanced visualization tools
- 🔄 Performance optimization
- 🔄 Documentation website

### 📋 Planned (v0.3.0)
- 📋 Real-time execution mode
- 📋 BACnet/Modbus integration
- 📋 State machine blocks
- 📋 Advanced control sequences (multi-zone, plant optimization)

### 🔮 Future (v1.0.0)
- 🔮 Complete CDL elementary block library
- 🔮 Fault detection and diagnostics (FDD)
- 🔮 Model-predictive control (MPC) integration
- 🔮 Cloud deployment capabilities
- 🔮 Building simulation coupling (EnergyPlus, Modelica)

---

**Status**: Active Development
**Version**: 0.1.0
**Last Updated**: October 2025
**Test Status**: ✅ 181/181 passing (100%)
