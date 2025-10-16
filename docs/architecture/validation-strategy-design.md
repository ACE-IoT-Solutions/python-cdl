# Python CDL - Validation and Type Checking Strategy

## Overview

This document defines the comprehensive validation and type checking strategy for the Python CDL implementation. We employ a multi-layered approach combining Pydantic runtime validation, Pyright static analysis, and semantic CDL validation.

## Validation Layers

### Layer 1: Pydantic Runtime Validation (Data Integrity)

**Purpose**: Ensure JSON data conforms to schema structure and type constraints

**Scope**:
- Field types (str, int, float, bool, etc.)
- Required vs optional fields
- Value ranges and constraints
- String patterns
- Nested object structure
- Array element validation

**Implementation**: Built into Pydantic models with validators

```python
from pydantic import Field, field_validator, model_validator
from typing import Annotated

class Parameter(CDLImmutableModel):
    """Parameter with built-in validation"""
    name: Annotated[str, Field(min_length=1, pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$')]
    type_kind: CDLTypeKind
    value: float | int | bool | str

    @field_validator("value")
    @classmethod
    def validate_value_type(cls, v: Any, info: ValidationInfo) -> Any:
        """Ensure value matches type_kind"""
        type_kind = info.data.get("type_kind")

        if type_kind == CDLTypeKind.REAL and not isinstance(v, (float, int)):
            raise ValueError(f"REAL parameter requires numeric value, got {type(v)}")
        elif type_kind == CDLTypeKind.INTEGER and not isinstance(v, int):
            raise ValueError(f"INTEGER parameter requires int value, got {type(v)}")
        elif type_kind == CDLTypeKind.BOOLEAN and not isinstance(v, bool):
            raise ValueError(f"BOOLEAN parameter requires bool value, got {type(v)}")
        elif type_kind == CDLTypeKind.STRING and not isinstance(v, str):
            raise ValueError(f"STRING parameter requires str value, got {type(v)}")

        return v

class Quantity(CDLImmutableModel):
    """Quantity with range validation"""
    min_value: float | None = Field(default=None, alias="min")
    max_value: float | None = Field(default=None, alias="max")
    nominal: float | None = None

    @model_validator(mode="after")
    def validate_min_max(self) -> Self:
        """Ensure min <= max"""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"min ({self.min_value}) must be <= max ({self.max_value})")
        return self
```

### Layer 2: Pyright Static Type Checking (Code Quality)

**Purpose**: Catch type errors at development time, ensure type safety in Python code

**Scope**:
- Function parameter types
- Return value types
- Variable assignments
- Type narrowing with type guards
- Generic type parameters
- Protocol compliance

**Configuration** (`pyproject.toml`):

```toml
[tool.pyright]
include = ["src"]
exclude = ["**/__pycache__"]
venvPath = "."
venv = ".venv"

# Type checking strictness
typeCheckingMode = "strict"
strictListInference = true
strictDictionaryInference = true
strictSetInference = true
strictParameterNoneValue = true

# Specific checks
reportMissingImports = "error"
reportMissingTypeStubs = "warning"
reportUnusedImport = "warning"
reportUnusedVariable = "warning"
reportDuplicateImport = "error"
reportPrivateUsage = "error"
reportConstantRedefinition = "error"
reportIncompatibleMethodOverride = "error"
reportIncompatibleVariableOverride = "error"
reportInconsistentConstructor = "error"
reportUnknownParameterType = "warning"
reportUnknownArgumentType = "warning"
reportUnknownVariableType = "warning"
reportUnknownMemberType = "warning"
reportMissingParameterType = "error"
reportMissingTypeArgument = "error"
reportUnnecessaryIsInstance = "warning"
reportUnnecessaryCast = "warning"
reportUnnecessaryComparison = "warning"
reportUnnecessaryContains = "warning"
reportImplicitStringConcatenation = "warning"

# Python version
pythonVersion = "3.13"
pythonPlatform = "All"
```

**Type Guards and Narrowing**:

```python
from typing import TypeGuard, TypeVar, Literal

def is_elementary_block(
    block: ElementaryBlock | CompositeBlock
) -> TypeGuard[ElementaryBlock]:
    """Type guard for elementary blocks"""
    return isinstance(block, ElementaryBlock)

def is_real_type(type_kind: CDLTypeKind) -> TypeGuard[Literal[CDLTypeKind.REAL]]:
    """Type guard for real type"""
    return type_kind == CDLTypeKind.REAL

# Usage with type narrowing
block: ElementaryBlock | CompositeBlock = get_block()
if is_elementary_block(block):
    # Pyright knows block is ElementaryBlock here
    class_name: str = block.class_name  # OK
```

**Generic Types**:

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar("T", bound=CDLBaseModel)

class ModelRepository(Generic[T]):
    """Type-safe repository for CDL models"""

    def __init__(self, model_type: type[T]) -> None:
        self._model_type = model_type
        self._models: dict[str, T] = {}

    def add(self, name: str, model: T) -> None:
        """Add model to repository"""
        self._models[name] = model

    def get(self, name: str) -> T | None:
        """Get model by name"""
        return self._models.get(name)

# Usage - Pyright infers correct types
block_repo = ModelRepository(ClassDefinition)
block_repo.add("controller", my_class_def)  # OK
result: ClassDefinition | None = block_repo.get("controller")  # Correctly typed
```

**Protocol-based Design**:

```python
from typing import Protocol

class Evaluable(Protocol):
    """Protocol for evaluable objects"""

    def evaluate(self, context: ExecutionContext) -> None:
        """Evaluate the object"""
        ...

class Initializable(Protocol):
    """Protocol for initializable objects"""

    def initialize(self, context: ExecutionContext) -> None:
        """Initialize the object"""
        ...

def run_block(block: Evaluable & Initializable, context: ExecutionContext) -> None:
    """Run a block that is both initializable and evaluable"""
    block.initialize(context)
    block.evaluate(context)
    # Pyright verifies block has both methods
```

### Layer 3: Semantic CDL Validation (Domain Rules)

**Purpose**: Enforce CDL language semantics and control sequence rules

**Scope**:
- Connection validity (type compatibility, no loops)
- Input/output coverage (all inputs connected, all outputs used)
- Parameter constraints (required parameters set, values in range)
- Block compatibility (valid block types, proper nesting)
- Hierarchical consistency (composite blocks match definitions)

**Implementation**: Custom validator classes

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class ValidationError:
    """Validation error record"""
    severity: Literal["error", "warning", "info"]
    message: str
    location: str | None = None  # Instance/component path
    rule: str | None = None  # Validation rule identifier

class ValidationResult:
    """Result of validation"""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.info: list[ValidationError] = []

    def add_error(self, message: str, location: str | None = None, rule: str | None = None) -> None:
        """Add error"""
        self.errors.append(ValidationError("error", message, location, rule))

    def add_warning(self, message: str, location: str | None = None, rule: str | None = None) -> None:
        """Add warning"""
        self.warnings.append(ValidationError("warning", message, location, rule))

    def add_info(self, message: str, location: str | None = None, rule: str | None = None) -> None:
        """Add info"""
        self.info.append(ValidationError("info", message, location, rule))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings"""
        return len(self.warnings) > 0

    def __str__(self) -> str:
        """Format validation result"""
        lines = []
        for error in self.errors:
            lines.append(f"ERROR: {error.message}" + (f" at {error.location}" if error.location else ""))
        for warning in self.warnings:
            lines.append(f"WARNING: {warning.message}" + (f" at {warning.location}" if warning.location else ""))
        return "\n".join(lines)

class CDLValidator:
    """Semantic validator for CDL models"""

    def __init__(self) -> None:
        # Registry of validation rules
        self._rules: list[Callable[[ClassDefinition, ValidationResult], None]] = [
            self._validate_all_inputs_connected,
            self._validate_no_algebraic_loops,
            self._validate_type_compatibility,
            self._validate_required_parameters,
            self._validate_parameter_constraints,
            self._validate_block_types,
        ]

    def validate(self, model: ClassDefinition) -> ValidationResult:
        """Validate CDL model"""
        result = ValidationResult()

        # Run all validation rules
        for rule in self._rules:
            rule(model, result)

        return result

    # Validation Rules

    def _validate_all_inputs_connected(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Ensure all inputs are connected"""
        # Build connection map
        connected_inputs: set[tuple[str, str]] = set()
        for conn in model.connections:
            connected_inputs.add((conn.to_ref.instance, conn.to_ref.connector))

        # Check each instance
        for instance in model.instances:
            # Get input connectors for this instance
            inputs = self._get_instance_inputs(instance, model)

            for input_name in inputs:
                if (instance.instance_name, input_name) not in connected_inputs:
                    result.add_error(
                        f"Input '{input_name}' is not connected",
                        location=f"{instance.instance_name}.{input_name}",
                        rule="all-inputs-connected"
                    )

    def _validate_no_algebraic_loops(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Check for algebraic loops in connections"""
        # Build dependency graph
        graph: dict[str, set[str]] = defaultdict(set)
        for conn in model.connections:
            graph[conn.to_ref.instance].add(conn.from_ref.instance)

        # Detect cycles using DFS
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    result.add_error(
                        f"Algebraic loop detected: {' -> '.join(cycle)}",
                        rule="no-algebraic-loops"
                    )
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for instance in model.instances:
            if instance.instance_name not in visited:
                has_cycle(instance.instance_name)

    def _validate_type_compatibility(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Ensure connected signals have compatible types"""
        for conn in model.connections:
            # Get types of source and destination
            source_type = self._get_connector_type(conn.from_ref, model)
            dest_type = self._get_connector_type(conn.to_ref, model)

            if not self._types_compatible(source_type, dest_type):
                result.add_error(
                    f"Type mismatch: cannot connect {source_type} to {dest_type}",
                    location=f"{conn.from_ref} -> {conn.to_ref}",
                    rule="type-compatibility"
                )

    def _validate_required_parameters(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Check required parameters are set"""
        for instance in model.instances:
            # Get required parameters for this block type
            required_params = self._get_required_parameters(instance, model)

            for param_name in required_params:
                if param_name not in instance.parameters:
                    result.add_error(
                        f"Required parameter '{param_name}' not set",
                        location=f"{instance.instance_name}.{param_name}",
                        rule="required-parameters"
                    )

    def _validate_parameter_constraints(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Validate parameter value constraints"""
        for instance in model.instances:
            for param_name, param in instance.parameters.items():
                # Check against quantity constraints
                if param.quantity:
                    qty = param.quantity
                    if isinstance(param.value, (int, float)):
                        if qty.min_value is not None and param.value < qty.min_value:
                            result.add_error(
                                f"Parameter value {param.value} below minimum {qty.min_value}",
                                location=f"{instance.instance_name}.{param_name}",
                                rule="parameter-constraints"
                            )
                        if qty.max_value is not None and param.value > qty.max_value:
                            result.add_error(
                                f"Parameter value {param.value} above maximum {qty.max_value}",
                                location=f"{instance.instance_name}.{param_name}",
                                rule="parameter-constraints"
                            )

    def _validate_block_types(
        self,
        model: ClassDefinition,
        result: ValidationResult
    ) -> None:
        """Validate block types are known/valid"""
        for instance in model.instances:
            if isinstance(instance, ElementaryBlock):
                # Check if block type is registered
                if not BlockRegistry.is_registered(instance.class_name):
                    result.add_warning(
                        f"Unknown block type: {instance.class_name}",
                        location=instance.instance_name,
                        rule="known-block-types"
                    )

    # Helper methods

    def _get_instance_inputs(
        self,
        instance: ElementaryBlock | CompositeBlock,
        model: ClassDefinition
    ) -> list[str]:
        """Get list of input connector names for instance"""
        # This would query block metadata or class definition
        # Implementation depends on block registry
        return []

    def _get_connector_type(
        self,
        ref: ConnectorReference,
        model: ClassDefinition
    ) -> CDLTypeKind:
        """Get type of a connector"""
        # Look up connector type in instance/class definition
        return CDLTypeKind.REAL  # Placeholder

    def _types_compatible(self, type1: CDLTypeKind, type2: CDLTypeKind) -> bool:
        """Check if two types are compatible for connection"""
        # Exact match or compatible conversion
        return type1 == type2

    def _get_required_parameters(
        self,
        instance: ElementaryBlock | CompositeBlock,
        model: ClassDefinition
    ) -> list[str]:
        """Get list of required parameter names for instance"""
        return []
```

### Layer 4: Runtime Validation (Execution Checks)

**Purpose**: Validate runtime conditions during execution

**Scope**:
- Signal value ranges
- Numerical stability
- Resource constraints (memory, time)
- State consistency

**Implementation**: Runtime assertions and monitoring

```python
class RuntimeValidator:
    """Runtime validation during execution"""

    def __init__(self, config: ExecutionConfig) -> None:
        self.config = config
        self.enabled = config.enable_validation

    def validate_signal_value(
        self,
        instance: str,
        connector: str,
        value: Any,
        expected_type: CDLTypeKind
    ) -> None:
        """Validate signal value at runtime"""
        if not self.enabled:
            return

        # Type check
        if expected_type == CDLTypeKind.REAL and not isinstance(value, (int, float)):
            raise TypeError(f"Expected Real for {instance}.{connector}, got {type(value)}")

        # Range check (if bounds known)
        if isinstance(value, (int, float)):
            if not (-1e10 < value < 1e10):  # Reasonable bounds
                warnings.warn(f"Signal value {value} at {instance}.{connector} may be unbounded")

    def validate_no_nan_inf(self, value: float, location: str) -> None:
        """Check for NaN or Inf values"""
        if not self.enabled:
            return

        import math
        if math.isnan(value):
            raise ValueError(f"NaN value detected at {location}")
        if math.isinf(value):
            raise ValueError(f"Infinite value detected at {location}")
```

## Validation Integration

### At Parse Time

```python
def load_and_validate_cdl(file_path: Path, strict: bool = True) -> ClassDefinition:
    """Load CDL document with full validation"""
    # Layer 1: Pydantic validation (automatic)
    doc = load_cdl_document(file_path)

    if doc.main_class is None:
        raise ValueError("No class definition found in document")

    model = doc.main_class

    # Layer 3: Semantic validation
    validator = CDLValidator()
    result = validator.validate(model)

    if not result.is_valid:
        if strict:
            raise ValueError(f"Model validation failed:\n{result}")
        else:
            warnings.warn(f"Model validation warnings:\n{result}")

    return model
```

### At Execution Time

```python
def create_validated_context(
    model: ClassDefinition,
    config: ExecutionConfig
) -> ExecutionContext:
    """Create execution context with validation"""
    # Validate model before execution
    validator = CDLValidator()
    result = validator.validate(model)

    if not result.is_valid:
        raise ValueError(f"Cannot execute invalid model:\n{result}")

    # Create context with runtime validation
    context = ExecutionContext(model, config)
    context._runtime_validator = RuntimeValidator(config)

    return context
```

## Testing Strategy

### Unit Tests for Validators

```python
def test_algebraic_loop_detection():
    """Test detection of algebraic loops"""
    # Create model with loop
    model = ClassDefinition(
        class_name="LoopTest",
        instances=[...],
        connections=[
            Connection(
                from_ref=ConnectorReference(instance="a", connector="y"),
                to_ref=ConnectorReference(instance="b", connector="u")
            ),
            Connection(
                from_ref=ConnectorReference(instance="b", connector="y"),
                to_ref=ConnectorReference(instance="a", connector="u")
            ),
        ]
    )

    validator = CDLValidator()
    result = validator.validate(model)

    assert not result.is_valid
    assert any("loop" in err.message.lower() for err in result.errors)
```

### Integration Tests with Real Models

```python
def test_validate_real_cdl_models():
    """Test validation on real CDL examples"""
    test_files = Path("tests/fixtures/cdl").glob("*.json")

    for file_path in test_files:
        model = load_and_validate_cdl(file_path, strict=True)
        assert model is not None
```

## Validation Performance

- Pydantic validation: O(n) in model size, fast (built-in)
- Semantic validation: O(n + e) where n=instances, e=connections
- Type checking: Compile-time (zero runtime cost)
- Runtime validation: O(1) per signal (can be disabled)

## Error Reporting

Validation errors include:
1. **Severity**: error, warning, info
2. **Message**: Human-readable description
3. **Location**: Path to problematic element
4. **Rule**: Which validation rule failed
5. **Suggestion**: How to fix (when possible)

Example error output:
```
ERROR: Input 'u' is not connected at controller.u (rule: all-inputs-connected)
  Suggestion: Connect an output signal to this input

WARNING: Unknown block type: Custom.Controllers.MyController at myController (rule: known-block-types)
  Suggestion: Register custom block type or check spelling
```

## Summary

Multi-layered validation approach ensures:
1. **Data integrity** through Pydantic
2. **Code quality** through Pyright
3. **Semantic correctness** through custom validators
4. **Runtime safety** through execution checks

This comprehensive strategy catches errors early and provides clear feedback for troubleshooting.
