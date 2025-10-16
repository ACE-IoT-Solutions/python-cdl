# Python CDL Implementation Strategy

## Executive Summary

This document outlines the recommended strategy for implementing a Python library for Controls Description Language (CDL) parsing, execution, and translation. The implementation prioritizes standards compliance, type safety, and practical usability.

## Implementation Philosophy

### Core Principles
1. **Standards First**: Strict adherence to ASHRAE 231P and CDL specification
2. **Type Safety**: Leverage Python type hints and Pydantic for runtime validation
3. **Pythonic API**: Natural, intuitive interfaces for Python developers
4. **Performance**: Efficient execution for production building automation
5. **Extensibility**: Support custom blocks and vendor-specific extensions

### Strategic Approach: Hybrid Model

**RECOMMENDATION**: Hybrid approach combining existing tools with native Python implementation

**Rationale**:
- Leverage proven modelica-json parser for CDL syntax
- Focus Python effort on object model, execution, and integration
- Faster time to market with standards compliance guaranteed
- Option to replace parser later with pure Python implementation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│  (User API, Control Sequence Design, Deployment)        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              High-Level API Layer                        │
│  - CDLSequence (builder pattern)                        │
│  - Block registry and discovery                         │
│  - Validation and verification                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Translation Layer                           │
│  - CDL-JSON import/export                               │
│  - CXF (JSON-LD) generation                             │
│  - Schema validation                                     │
│  - Documentation generation                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Execution Engine                            │
│  - Dependency graph construction                        │
│  - Topological sort and cycle detection                 │
│  - Event-based execution                                │
│  - State management                                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Object Model Layer                          │
│  - Block hierarchy (Elementary, Composite, Extension)   │
│  - Connectors (Input/Output)                            │
│  - Parameters and Constants                             │
│  - Type system (Real, Boolean, Integer)                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Parser Layer                                │
│  Phase 1: Wrapper for modelica-json (Node.js)          │
│  Phase 2: Native Python parser (optional future)        │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
python-cdl/
├── src/
│   └── python_cdl/
│       ├── __init__.py
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── modelica_json_wrapper.py  # Wrapper for modelica-json
│       │   ├── json_loader.py            # CDL-JSON parser
│       │   └── native_parser.py          # Future: Native Python parser
│       ├── model/
│       │   ├── __init__.py
│       │   ├── types.py                  # CDL type system
│       │   ├── connector.py              # Input/Output connectors
│       │   ├── parameter.py              # Parameters and constants
│       │   ├── block.py                  # Block base classes
│       │   ├── elementary.py             # Elementary blocks
│       │   ├── composite.py              # Composite blocks
│       │   └── extension.py              # Extension blocks
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── graph.py                  # Dependency graph
│       │   ├── executor.py               # Execution engine
│       │   ├── validator.py              # Validation logic
│       │   └── state.py                  # State management
│       ├── translation/
│       │   ├── __init__.py
│       │   ├── json_serializer.py        # CDL to JSON
│       │   ├── json_deserializer.py      # JSON to CDL
│       │   ├── cxf_exporter.py           # CXF generation
│       │   └── schema_validator.py       # Schema validation
│       ├── stdlib/
│       │   ├── __init__.py
│       │   ├── continuous.py             # Continuous blocks
│       │   ├── discrete.py               # Discrete blocks
│       │   ├── logical.py                # Logical blocks
│       │   ├── routing.py                # Routing blocks
│       │   └── conversion.py             # Type conversion blocks
│       └── api/
│           ├── __init__.py
│           ├── builder.py                # High-level builder API
│           └── registry.py               # Block registry
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── examples/
│   ├── simple_gain.py
│   ├── pid_controller.py
│   └── hvac_sequence.py
├── docs/
│   ├── research-cdl-specification.md
│   ├── cdl-json-format-details.md
│   └── python-implementation-strategy.md
├── pyproject.toml
├── README.md
└── uv.lock
```

## Technology Stack

### Core Dependencies

#### Required
- **Python**: 3.10+ (for modern type hints)
- **pydantic**: 2.0+ (data validation and serialization)
- **typing-extensions**: Extended type hint support
- **jsonschema**: JSON schema validation
- **networkx**: Graph operations for dependency analysis

#### Optional for Phase 1 (Hybrid Approach)
- **Node.js**: 18+ (runtime for modelica-json)
- **subprocess**: Python standard library for process management

#### Optional for Advanced Features
- **rdflib**: RDF/JSON-LD support for CXF
- **graphviz**: Visualization of dependency graphs
- **numpy**: Numerical operations for advanced blocks
- **lark**: Modern parsing library (for future native parser)

#### Development Tools
- **uv**: Modern Python package manager
- **ruff**: Fast Python linter
- **pyright**: Static type checker
- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **hypothesis**: Property-based testing

### pyproject.toml Configuration

```toml
[project]
name = "python-cdl"
version = "0.1.0"
description = "Python implementation of Controls Description Language (CDL) for building automation"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "typing-extensions>=4.0",
    "jsonschema>=4.0",
    "networkx>=3.0",
]

[project.optional-dependencies]
cxf = ["rdflib>=6.0"]
viz = ["graphviz>=0.20"]
numerical = ["numpy>=1.24"]
all = ["python-cdl[cxf,viz,numerical]"]

[tool.uv]
dev-dependencies = [
    "ruff>=0.1.0",
    "pyright>=1.1.0",
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "hypothesis>=6.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.10"
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

#### Goals
- Project setup and structure
- Core type system
- Basic object model
- CDL-JSON parsing

#### Deliverables
1. **Project Setup**
   - Initialize with uv
   - Configure ruff and pyright
   - Setup pytest framework
   - Create basic documentation

2. **Type System** (`model/types.py`)
   ```python
   from pydantic import BaseModel, Field
   from typing import Union, Literal, Optional

   CDLDataType = Literal["Real", "Boolean", "Integer"]
   CDLValue = Union[float, bool, int]

   class CDLType(BaseModel):
       """Base class for CDL types"""
       data_type: CDLDataType
       min_value: Optional[float] = None
       max_value: Optional[float] = None

   class RealType(CDLType):
       data_type: Literal["Real"] = "Real"
       unit: Optional[str] = None
       quantity: Optional[str] = None
       nominal: Optional[float] = None

   class BooleanType(CDLType):
       data_type: Literal["Boolean"] = "Boolean"

   class IntegerType(CDLType):
       data_type: Literal["Integer"] = "Integer"
   ```

3. **Connector Model** (`model/connector.py`)
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional
   from .types import CDLValue, RealType, BooleanType, IntegerType

   class Connector(BaseModel):
       name: str
       type_spec: Union[RealType, BooleanType, IntegerType]
       description: Optional[str] = None
       value: Optional[CDLValue] = None

   class InputConnector(Connector):
       """Input connector - must be connected to exactly one output"""
       connected_to: Optional[str] = None  # Reference to output

   class OutputConnector(Connector):
       """Output connector - can connect to multiple inputs"""
       connected_to: list[str] = Field(default_factory=list)
   ```

4. **Parameter Model** (`model/parameter.py`)
   ```python
   from pydantic import BaseModel, validator
   from typing import Optional
   from .types import CDLValue, RealType, BooleanType, IntegerType

   class Parameter(BaseModel):
       name: str
       type_spec: Union[RealType, BooleanType, IntegerType]
       value: CDLValue
       description: Optional[str] = None
       fixed: bool = True
       final: bool = False

       @validator('value')
       def validate_value(cls, v, values):
           """Validate value against type constraints"""
           type_spec = values.get('type_spec')
           if type_spec.min_value is not None and v < type_spec.min_value:
               raise ValueError(f"Value {v} below minimum {type_spec.min_value}")
           if type_spec.max_value is not None and v > type_spec.max_value:
               raise ValueError(f"Value {v} above maximum {type_spec.max_value}")
           return v
   ```

5. **Basic Block Model** (`model/block.py`)
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional
   from .connector import InputConnector, OutputConnector
   from .parameter import Parameter

   class CDLBlock(BaseModel):
       """Base class for all CDL blocks"""
       name: str
       description: Optional[str] = None
       parameters: list[Parameter] = Field(default_factory=list)
       inputs: list[InputConnector] = Field(default_factory=list)
       outputs: list[OutputConnector] = Field(default_factory=list)

       def get_parameter(self, name: str) -> Optional[Parameter]:
           """Get parameter by name"""
           return next((p for p in self.parameters if p.name == name), None)

       def get_input(self, name: str) -> Optional[InputConnector]:
           """Get input connector by name"""
           return next((i for i in self.inputs if i.name == name), None)

       def get_output(self, name: str) -> Optional[OutputConnector]:
           """Get output connector by name"""
           return next((o for o in self.outputs if o.name == name), None)
   ```

### Phase 2: Parser Integration (Weeks 3-4)

#### Goals
- Integrate modelica-json via subprocess
- Implement CDL-JSON to Python object mapping
- Handle CDL file parsing

#### Deliverables
1. **modelica-json Wrapper** (`parser/modelica_json_wrapper.py`)
   ```python
   import subprocess
   import json
   from pathlib import Path
   from typing import Optional

   class ModelicaJsonWrapper:
       """Wrapper for modelica-json Node.js tool"""

       def __init__(self, modelica_json_path: Optional[Path] = None):
           self.modelica_json_path = modelica_json_path or self._find_modelica_json()

       def _find_modelica_json(self) -> Path:
           """Locate modelica-json installation"""
           # Try common locations or use npx
           return Path("npx")  # Use npx for now

       def parse_cdl(self, mo_file: Path, output_format: str = "json-simplified") -> dict:
           """Parse CDL file to JSON"""
           cmd = [
               "npx", "modelica-json",
               "-f", str(mo_file),
               "-o", output_format
           ]

           result = subprocess.run(
               cmd,
               capture_output=True,
               text=True,
               check=True
           )

           return json.loads(result.stdout)

       def validate_json(self, json_file: Path) -> bool:
           """Validate JSON against schema"""
           cmd = [
               "npx", "modelica-json",
               "validate",
               "-f", str(json_file)
           ]

           result = subprocess.run(cmd, capture_output=True)
           return result.returncode == 0
   ```

2. **JSON to Object Mapper** (`parser/json_loader.py`)
   ```python
   from pathlib import Path
   import json
   from typing import Union
   from ..model.block import CDLBlock
   from ..model.elementary import ElementaryBlock
   from ..model.composite import CompositeBlock
   from ..model.connector import InputConnector, OutputConnector
   from ..model.parameter import Parameter

   class CDLJsonLoader:
       """Load CDL objects from JSON representation"""

       def load_from_file(self, json_file: Path) -> CDLBlock:
           """Load CDL block from JSON file"""
           with open(json_file, 'r') as f:
               data = json.load(f)
           return self.load_from_dict(data)

       def load_from_dict(self, data: dict) -> CDLBlock:
           """Load CDL block from dictionary"""
           # Determine block type
           if "instances" in data.get("public", {}):
               return self._load_composite_block(data)
           else:
               return self._load_elementary_block(data)

       def _load_elementary_block(self, data: dict) -> ElementaryBlock:
           """Load elementary block from JSON"""
           public = data.get("public", {})

           parameters = [
               self._load_parameter(p)
               for p in public.get("parameters", [])
           ]

           inputs = [
               self._load_input(i)
               for i in public.get("inputs", [])
           ]

           outputs = [
               self._load_output(o)
               for o in public.get("outputs", [])
           ]

           return ElementaryBlock(
               name=data.get("topClassName"),
               description=data.get("comment"),
               parameters=parameters,
               inputs=inputs,
               outputs=outputs
           )

       # Additional methods for composite blocks, parameters, etc.
   ```

### Phase 3: Object Model (Weeks 5-6)

#### Goals
- Implement all block types
- Connection management
- Validation logic

#### Deliverables
1. **Elementary Blocks** (`model/elementary.py`)
2. **Composite Blocks** (`model/composite.py`)
3. **Extension Blocks** (`model/extension.py`)
4. **Standard Library** (`stdlib/`)
   - Continuous blocks (Add, Multiply, PID, etc.)
   - Discrete blocks (Sampler, Hold, etc.)
   - Logical blocks (And, Or, Not, etc.)
   - Routing blocks (Switch, Multiplex, etc.)

### Phase 4: Execution Engine (Weeks 7-8)

#### Goals
- Dependency graph construction
- Execution ordering
- Event-based computation
- State management

#### Deliverables
1. **Dependency Graph** (`engine/graph.py`)
   ```python
   import networkx as nx
   from ..model.block import CDLBlock
   from ..model.composite import CompositeBlock

   class DependencyGraph:
       """Construct and analyze dependency graph"""

       def __init__(self, root_block: CompositeBlock):
           self.root = root_block
           self.graph = nx.DiGraph()
           self._build_graph()

       def _build_graph(self):
           """Build dependency graph from connections"""
           for connection in self.root.connections:
               self.graph.add_edge(connection.source, connection.target)

       def validate(self) -> bool:
           """Validate graph is acyclic"""
           try:
               cycles = list(nx.simple_cycles(self.graph))
               if cycles:
                   raise ValueError(f"Algebraic loops detected: {cycles}")
               return True
           except nx.NetworkXNoCycle:
               return True

       def execution_order(self) -> list[str]:
           """Get topologically sorted execution order"""
           return list(nx.topological_sort(self.graph))
   ```

2. **Execution Engine** (`engine/executor.py`)
   ```python
   from typing import Dict, Any
   from ..model.composite import CompositeBlock
   from .graph import DependencyGraph

   class ExecutionEngine:
       """Execute CDL control sequences"""

       def __init__(self, sequence: CompositeBlock):
           self.sequence = sequence
           self.graph = DependencyGraph(sequence)
           self.execution_order = self.graph.execution_order()
           self.state: Dict[str, Any] = {}

       def initialize(self):
           """Initialize state with start values"""
           for block in self.sequence.instances:
               for output in block.outputs:
                   if output.value is not None:
                       self.state[f"{block.name}.{output.name}"] = output.value

       def step(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           """Execute one computation step"""
           # Update inputs
           self.state.update(inputs)

           # Execute blocks in topological order
           for block_ref in self.execution_order:
               block = self.sequence.get_instance(block_ref)
               self._execute_block(block)

           # Return outputs
           return self._get_outputs()

       def _execute_block(self, block):
           """Execute single block computation"""
           # Get input values from state
           input_values = {
               inp.name: self.state.get(inp.connected_to)
               for inp in block.inputs
           }

           # Compute outputs
           output_values = block.compute(input_values)

           # Update state
           for name, value in output_values.items():
               self.state[f"{block.name}.{name}"] = value
   ```

### Phase 5: Translation (Weeks 9-10)

#### Goals
- CDL-JSON export
- CXF generation
- Schema validation

#### Deliverables
1. **JSON Serializer** (`translation/json_serializer.py`)
2. **CXF Exporter** (`translation/cxf_exporter.py`)
3. **Schema Validator** (`translation/schema_validator.py`)

### Phase 6: Testing & Documentation (Weeks 11-12)

#### Goals
- Comprehensive test coverage (>90%)
- Integration tests
- Documentation
- Examples

#### Deliverables
1. **Unit Tests** (`tests/unit/`)
2. **Integration Tests** (`tests/integration/`)
3. **Examples** (`examples/`)
4. **Documentation** (API reference, guides, tutorials)

## API Design

### High-Level Builder API

```python
from python_cdl import CDLSequence, blocks

# Create a PID controller with limiter
sequence = CDLSequence("PIDWithLimiter")

# Add parameters
sequence.add_parameter("k", 1.0, description="Proportional gain")
sequence.add_parameter("Ti", 1.0, description="Integral time")
sequence.add_parameter("yMax", 1.0, description="Max output")
sequence.add_parameter("yMin", 0.0, description="Min output")

# Add inputs/outputs
sequence.add_input("u_s", description="Setpoint")
sequence.add_input("u_m", description="Measured value")
sequence.add_output("y", description="Control signal")

# Add blocks
pid = sequence.add_block(blocks.PID(name="pid", k="k", Ti="Ti"))
limiter = sequence.add_block(blocks.Limiter(name="limiter", uMax="yMax", uMin="yMin"))

# Connect
sequence.connect("u_s", "pid.u_s")
sequence.connect("u_m", "pid.u_m")
sequence.connect("pid.y", "limiter.u")
sequence.connect("limiter.y", "y")

# Validate
sequence.validate()

# Export to CDL-JSON
sequence.export_json("pid_limiter.json")

# Export to CXF
sequence.export_cxf("pid_limiter_cxf.jsonld")
```

### Execution API

```python
from python_cdl import load_sequence, ExecutionEngine

# Load from CDL file
sequence = load_sequence("pid_limiter.mo")

# Create execution engine
engine = ExecutionEngine(sequence)
engine.initialize()

# Run simulation
for t in range(100):
    inputs = {
        "u_s": 23.0,  # Setpoint temperature
        "u_m": 20.0 + t * 0.1  # Measured temperature
    }

    outputs = engine.step(inputs)
    print(f"t={t}, y={outputs['y']}")
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock dependencies
- Property-based testing with hypothesis
- Edge cases and error conditions

### Integration Tests
- Full workflow tests (parse → execute → export)
- Validate against reference implementation
- Test with real CDL examples from Buildings library

### Validation Tests
- Compare outputs with OpenModelica simulation
- Verify JSON schema compliance
- Test CXF generation against specification

### Performance Tests
- Benchmark execution speed
- Profile memory usage
- Test with large control sequences (100+ blocks)

## Quality Assurance

### Code Quality
- **Linting**: ruff with strict rules
- **Type Checking**: pyright in strict mode
- **Coverage**: >90% code coverage required
- **Documentation**: Docstrings for all public APIs

### Continuous Integration
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install uv
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run pyright .
      - run: uv run pytest --cov
```

## Performance Considerations

### Optimization Targets
- Parse time: <100ms for typical sequences
- Execution: <1ms per step for 10-block sequence
- Memory: <10MB for typical sequence

### Strategies
1. **Lazy loading**: Load blocks on demand
2. **Caching**: Cache dependency graph computation
3. **Vectorization**: Use numpy for array operations
4. **JIT compilation**: Consider numba for hot paths

## Risk Mitigation

### Technical Risks
1. **Modelica parsing complexity**
   - Mitigation: Use modelica-json initially
   - Future: Incremental native parser development

2. **Performance requirements**
   - Mitigation: Profile early and optimize hot paths
   - Fallback: Consider Cython for critical sections

3. **Standards evolution**
   - Mitigation: Abstract schema validation
   - Version compatibility layer

### Project Risks
1. **Scope creep**
   - Mitigation: Strict phase boundaries
   - MVP focus on core functionality

2. **Resource constraints**
   - Mitigation: Hybrid approach reduces effort
   - Prioritize essential features

## Success Metrics

### Functionality
- [ ] Parse all CDL examples from Buildings library
- [ ] Execute control sequences correctly
- [ ] Generate valid CDL-JSON and CXF
- [ ] Pass schema validation

### Performance
- [ ] Parse time <100ms for typical sequence
- [ ] Execution time <1ms per step
- [ ] Memory usage <10MB per sequence

### Quality
- [ ] >90% test coverage
- [ ] Zero linting errors
- [ ] Zero type checking errors
- [ ] Comprehensive documentation

### Usability
- [ ] Intuitive API for common tasks
- [ ] Clear error messages
- [ ] Good documentation with examples
- [ ] Active community engagement

## Future Enhancements

### Phase 2+ Features
1. **Native Modelica parser** in Python
2. **FMU export** for simulation integration
3. **Visual editor** for control sequences
4. **Code generation** for target platforms
5. **Optimization** tools for control logic
6. **Runtime monitoring** and debugging
7. **Cloud deployment** support

## Conclusion

The hybrid implementation strategy provides the fastest path to a production-ready Python CDL library while maintaining standards compliance and type safety. By leveraging modelica-json for parsing and focusing Python development on the object model, execution engine, and API design, we can deliver value quickly while building toward a comprehensive solution.

The phased approach allows for early validation, risk mitigation, and incremental delivery of functionality. The emphasis on testing, type safety, and documentation ensures long-term maintainability and adoption by the building automation community.
