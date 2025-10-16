# Python CDL - Module Structure and Integration Points

## Project Structure

```
python-cdl/
├── src/
│   └── python_cdl/
│       ├── __init__.py              # Public API exports
│       ├── models/                  # Pydantic data models
│       │   ├── __init__.py
│       │   ├── base.py             # Base model classes
│       │   ├── types.py            # Type system (Real, Integer, Boolean, etc.)
│       │   ├── components.py       # Components and parameters
│       │   ├── connections.py      # Connection models
│       │   ├── graphics.py         # Visualization models
│       │   ├── blocks.py           # Block definitions
│       │   └── document.py         # Top-level document model
│       ├── parser/                  # CDL-JSON parsing
│       │   ├── __init__.py
│       │   ├── json_parser.py      # Main JSON parser
│       │   ├── schema.py           # Schema definitions
│       │   └── errors.py           # Parse error handling
│       ├── validators/              # Validation layer
│       │   ├── __init__.py
│       │   ├── semantic.py         # Semantic CDL validation
│       │   ├── connections.py      # Connection validation
│       │   ├── types.py            # Type checking
│       │   └── errors.py           # Validation error types
│       ├── execution/               # Runtime execution
│       │   ├── __init__.py
│       │   ├── context.py          # ExecutionContext
│       │   ├── instances.py        # BlockInstance implementations
│       │   ├── signals.py          # SignalGraph
│       │   ├── evaluator.py        # BlockEvaluator
│       │   ├── state.py            # State management
│       │   └── metrics.py          # Performance metrics
│       ├── blocks/                  # Elementary block implementations
│       │   ├── __init__.py
│       │   ├── registry.py         # Block type registry
│       │   ├── base.py             # Base block implementation
│       │   ├── reals/              # Continuous blocks
│       │   │   ├── __init__.py
│       │   │   ├── math.py         # Add, Multiply, etc.
│       │   │   ├── sources.py      # Constant, Ramp, etc.
│       │   │   └── control.py      # PID, Limiter, etc.
│       │   ├── discrete/           # Discrete blocks
│       │   │   ├── __init__.py
│       │   │   └── samplers.py
│       │   ├── logical/            # Logical blocks
│       │   │   ├── __init__.py
│       │   │   └── operators.py    # And, Or, Not, etc.
│       │   ├── integers/           # Integer blocks
│       │   │   ├── __init__.py
│       │   │   └── operators.py
│       │   ├── conversions/        # Type conversions
│       │   │   ├── __init__.py
│       │   │   └── converters.py
│       │   └── routing/            # Signal routing
│       │       ├── __init__.py
│       │       └── multiplex.py
│       ├── io/                      # I/O adapters
│       │   ├── __init__.py
│       │   ├── base.py             # Base I/O adapter
│       │   ├── file.py             # File-based I/O
│       │   ├── mqtt.py             # MQTT integration
│       │   └── bacnet.py           # BACnet integration
│       ├── utils/                   # Utilities
│       │   ├── __init__.py
│       │   ├── type_guards.py      # Type narrowing utilities
│       │   ├── graph.py            # Graph algorithms
│       │   └── logging.py          # Logging helpers
│       └── py.typed                # PEP 561 marker
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── fixtures/                   # Test fixtures
│   │   ├── cdl/                    # CDL-JSON test files
│   │   └── models/                 # Pydantic model examples
│   ├── unit/                       # Unit tests
│   │   ├── models/
│   │   ├── parser/
│   │   ├── validators/
│   │   ├── execution/
│   │   └── blocks/
│   ├── integration/                # Integration tests
│   │   ├── test_full_workflow.py
│   │   └── test_real_models.py
│   └── performance/                # Performance benchmarks
│       └── test_large_models.py
├── docs/                            # Documentation
│   ├── architecture/               # Architecture docs (this folder)
│   ├── api/                        # API documentation
│   ├── examples/                   # Usage examples
│   └── guides/                     # User guides
├── examples/                        # Example CDL models
│   ├── simple/
│   │   ├── pid_controller.json
│   │   └── temperature_control.json
│   └── advanced/
│       └── hvac_sequence.json
├── pyproject.toml                  # Project configuration
├── README.md                       # Project readme
└── uv.lock                         # Dependency lock file
```

## Module Dependencies

### Dependency Graph

```
models/
  └─> (no internal dependencies, only pydantic)

parser/
  └─> models/

validators/
  └─> models/
  └─> utils/graph

execution/
  └─> models/
  └─> validators/
  └─> blocks/registry
  └─> utils/

blocks/
  └─> models/
  └─> execution/ (circular, managed via protocols)

io/
  └─> execution/
  └─> models/

utils/
  └─> (minimal dependencies)
```

### Circular Dependency Management

The `execution` and `blocks` modules have a circular dependency:
- `execution` needs `blocks.registry` to get block implementations
- `blocks` implementations need to interact with `ExecutionContext`

**Solution**: Use Protocol-based interfaces

```python
# In execution/context.py
from typing import Protocol

class BlockImplementation(Protocol):
    """Protocol for block implementations"""
    def evaluate(self, instance: BlockInstance, context: "ExecutionContext") -> None: ...

# In blocks/base.py
from python_cdl.execution.context import ExecutionContext

class BaseBlockImpl:
    """Base implementation following protocol"""
    def evaluate(self, instance: BlockInstance, context: ExecutionContext) -> None:
        raise NotImplementedError
```

## Public API Surface

### `python_cdl/__init__.py`

```python
"""Python CDL - Control Description Language implementation"""

# Version
__version__ = "0.1.0"

# Models - Most commonly used
from python_cdl.models import (
    CDLDocument,
    ClassDefinition,
    ElementaryBlock,
    CompositeBlock,
    Connection,
    Parameter,
    CDLTypeKind,
)

# Parser
from python_cdl.parser import (
    load_cdl_document,
    parse_cdl_json,
    CDLParser,
)

# Execution
from python_cdl.execution import (
    ExecutionContext,
    ExecutionConfig,
    BlockInstance,
)

# Validation
from python_cdl.validators import (
    CDLValidator,
    ValidationResult,
    ValidationError,
)

# Block registry for custom blocks
from python_cdl.blocks import (
    BlockRegistry,
    register_block,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "CDLDocument",
    "ClassDefinition",
    "ElementaryBlock",
    "CompositeBlock",
    "Connection",
    "Parameter",
    "CDLTypeKind",
    # Parser
    "load_cdl_document",
    "parse_cdl_json",
    "CDLParser",
    # Execution
    "ExecutionContext",
    "ExecutionConfig",
    "BlockInstance",
    # Validation
    "CDLValidator",
    "ValidationResult",
    "ValidationError",
    # Blocks
    "BlockRegistry",
    "register_block",
]
```

## Integration Points

### 1. Parser Integration

```python
# Entry point for loading CDL files
from pathlib import Path
from python_cdl import load_cdl_document

# Load and parse
document = load_cdl_document(Path("controller.json"))
model = document.main_class

# Access parsed data
print(f"Model: {model.class_name}")
print(f"Instances: {len(model.instances)}")
print(f"Connections: {len(model.connections)}")
```

### 2. Validation Integration

```python
from python_cdl import CDLValidator

# Validate model
validator = CDLValidator()
result = validator.validate(model)

if not result.is_valid:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error.message} at {error.location}")
else:
    print("Model is valid!")
```

### 3. Execution Integration

```python
from python_cdl import ExecutionContext, ExecutionConfig
from datetime import timedelta

# Create execution context
config = ExecutionConfig(
    step_size=timedelta(seconds=0.1),
    enable_validation=True
)
context = ExecutionContext(model, config)

# Initialize and run
context.initialize()
context.run(steps=100)

# Access results
output = context.get_signal_value("controller", "y")
print(f"Controller output: {output}")
```

### 4. Custom Block Integration

```python
from python_cdl.blocks import register_block, BaseBlockImpl
from python_cdl.execution import BlockInstance, ExecutionContext

class MyCustomBlock(BaseBlockImpl):
    """Custom block implementation"""

    def initialize(self, instance: BlockInstance, context: ExecutionContext) -> None:
        # Initialize custom state
        instance.set_state("counter", 0)

    def evaluate(self, instance: BlockInstance, context: ExecutionContext) -> None:
        # Get inputs
        input_value = instance.get_input("u")

        # Custom logic
        counter = instance.get_state("counter")
        output_value = input_value + counter

        # Set outputs
        instance.set_output("y", output_value)
        instance.set_state("counter", counter + 1)

# Register block
register_block("Custom.MyBlock", MyCustomBlock())
```

### 5. I/O Adapter Integration

```python
from python_cdl.io import MQTTAdapter, BACnetAdapter

# MQTT integration
mqtt = MQTTAdapter(broker="mqtt.example.com", port=1883)
mqtt.connect()

# Map CDL signals to MQTT topics
mqtt.map_input("sensor_input", "u", topic="sensors/temperature")
mqtt.map_output("controller", "y", topic="actuators/valve")

# Run with I/O
context = ExecutionContext(model)
context.add_io_adapter(mqtt)
context.run()  # Will read/write via MQTT
```

### 6. Testing Integration

```python
import pytest
from python_cdl import parse_cdl_json, ExecutionContext

def test_pid_controller():
    """Test PID controller behavior"""
    # Load model
    json_data = """{ ... }"""
    document = parse_cdl_json(json_data)
    model = document.main_class

    # Setup execution
    context = ExecutionContext(model)
    context.initialize()

    # Set test input
    context.set_signal_value("setpoint", "u", 20.0)
    context.set_signal_value("measurement", "u", 15.0)

    # Execute
    context.step()

    # Verify output
    output = context.get_signal_value("pid", "y")
    assert output > 0, "Controller should increase output"
```

## Extension Points

### 1. Custom Validators

```python
from python_cdl.validators import CDLValidator, ValidationResult

class MyCustomValidator(CDLValidator):
    """Custom validation rules"""

    def validate(self, model: ClassDefinition) -> ValidationResult:
        result = super().validate(model)

        # Add custom checks
        self._check_naming_conventions(model, result)
        self._check_documentation(model, result)

        return result

    def _check_naming_conventions(self, model: ClassDefinition, result: ValidationResult) -> None:
        """Enforce naming conventions"""
        for instance in model.instances:
            if not instance.instance_name[0].islower():
                result.add_warning(
                    f"Instance names should start with lowercase: {instance.instance_name}",
                    location=instance.instance_name,
                    rule="naming-conventions"
                )
```

### 2. Custom Block Types

Add new block types by implementing the `BlockImplementation` protocol:

```python
from python_cdl.blocks.base import BaseBlockImpl

class StateMachineBlock(BaseBlockImpl):
    """State machine block implementation"""

    def initialize(self, instance: BlockInstance, context: ExecutionContext) -> None:
        # Load states from parameters
        states = instance.get_parameter("states")
        instance.set_state("current_state", states[0])

    def evaluate(self, instance: BlockInstance, context: ExecutionContext) -> None:
        # State machine logic
        current_state = instance.get_state("current_state")
        input_event = instance.get_input("event")

        # Transition logic
        next_state = self._transition(current_state, input_event)
        instance.set_state("current_state", next_state)
        instance.set_output("state", next_state)
```

### 3. Custom I/O Adapters

```python
from python_cdl.io.base import BaseIOAdapter

class DatabaseAdapter(BaseIOAdapter):
    """Database I/O adapter"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.connection_string = connection_string
        self.db = None

    def connect(self) -> None:
        # Connect to database
        self.db = create_connection(self.connection_string)

    def read_input(self, instance: str, connector: str) -> Any:
        # Read from database
        query = f"SELECT value FROM signals WHERE name = '{instance}.{connector}'"
        return self.db.execute(query).fetchone()[0]

    def write_output(self, instance: str, connector: str, value: Any) -> None:
        # Write to database
        query = f"INSERT INTO signals (name, value, timestamp) VALUES (?, ?, ?)"
        self.db.execute(query, (f"{instance}.{connector}", value, now()))
```

## Configuration Management

### `pyproject.toml`

```toml
[project]
name = "python-cdl"
version = "0.1.0"
description = "Python implementation of Control Description Language (CDL)"
authors = [
    { name = "Andrew Rodgers", email = "andrew@aceiotsolutions.com" }
]
requires-python = ">=3.13"
dependencies = [
    "pydantic>=2.12.2",
    "rdflib>=7.2.1",  # For semantic metadata (future)
]

[project.optional-dependencies]
io = [
    "paho-mqtt>=2.1.0",  # MQTT support
    "bacpypes3>=0.0.96",  # BACnet support
]
dev = [
    "pytest>=8.4.2",
    "pytest-cov>=6.0.0",
    "pyrefly>=0.37.0",  # Type checking
    "ruff>=0.14.0",  # Linting
    "mypy>=1.13.0",  # Type checking backup
]
docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.27.0",
]

[project.scripts]
python-cdl = "python_cdl:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=python_cdl",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.coverage.run]
branch = true
source = ["python_cdl"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]

[tool.pyright]
include = ["src"]
exclude = ["**/__pycache__"]
venvPath = "."
venv = ".venv"
typeCheckingMode = "strict"
pythonVersion = "3.13"

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/**/*.py" = ["ARG"]  # Allow unused arguments in tests
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repo-url>
cd python-cdl

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -e ".[dev,io,docs]"
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/unit/models/test_types.py

# Run with verbose output
pytest -v
```

### 3. Type Checking

```bash
# Run Pyright
pyrefly

# Run mypy (backup)
mypy src/python_cdl
```

### 4. Linting and Formatting

```bash
# Check code style
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### 5. Build Documentation

```bash
# Build docs
mkdocs build

# Serve docs locally
mkdocs serve
# Visit http://127.0.0.1:8000
```

## Summary

The module structure provides:
1. **Clear separation of concerns**: Models, parsing, validation, execution, blocks
2. **Extensibility**: Easy to add custom blocks, validators, I/O adapters
3. **Type safety**: Full Pyright coverage with strict mode
4. **Testing**: Comprehensive unit and integration tests
5. **Documentation**: Architecture docs, API docs, examples
6. **Modern tooling**: uv, pytest, ruff, pyright

All integration points are well-defined and follow consistent patterns for ease of use and maintenance.
