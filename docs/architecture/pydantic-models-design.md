# Python CDL - Pydantic Models Architecture Design

## Overview

This document defines the Pydantic v2 model architecture for the Python implementation of the Control Description Language (CDL). The design is based on the CDL JSON schema from the modelica-json project (lbl-srg/modelica-json).

## Design Principles

1. **Standard Compliance**: Fully conform to CDL JSON schema specification
2. **Type Safety**: Leverage Pydantic v2 for runtime validation and Pyright for static type checking
3. **Extensibility**: Design for easy addition of new block types and operators
4. **Performance**: Optimize for parsing large CDL models with hundreds of blocks
5. **Immutability**: Use frozen models where appropriate to prevent accidental mutations
6. **Clear Semantics**: Model names and structure reflect CDL domain concepts

## Core Model Hierarchy

### 1. Base Models

```python
# Base class for all CDL objects
class CDLBaseModel(BaseModel):
    """Base model for all CDL constructs with common configuration"""
    model_config = ConfigDict(
        frozen=False,  # Allow mutation for runtime state
        validate_assignment=True,  # Validate on field assignment
        use_enum_values=False,  # Keep enum types for better type safety
        extra="forbid",  # Reject unknown fields
        str_strip_whitespace=True,
    )

# Frozen base for immutable data
class CDLImmutableModel(BaseModel):
    """Base for immutable CDL data structures"""
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra="forbid",
    )
```

### 2. Type System Models

```python
from enum import Enum
from typing import Literal, Annotated
from pydantic import Field, StringConstraints

class CDLTypeKind(str, Enum):
    """CDL primitive type kinds"""
    REAL = "Real"
    INTEGER = "Integer"
    BOOLEAN = "Boolean"
    STRING = "String"
    ENUMERATION = "Enumeration"

class CDLVariability(str, Enum):
    """Variable variability classification"""
    CONSTANT = "constant"
    PARAMETER = "parameter"
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"

class CDLCausality(str, Enum):
    """Variable causality classification"""
    INPUT = "input"
    OUTPUT = "output"
    LOCAL = "local"
    PARAMETER = "parameter"

class TypeSpecifier(CDLImmutableModel):
    """CDL type specification"""
    type_kind: CDLTypeKind
    class_name: str | None = None  # For user-defined types
    dimensions: list[int] = Field(default_factory=list)  # Array dimensions

class Quantity(CDLImmutableModel):
    """Physical quantity with unit"""
    unit: str | None = None
    display_unit: str | None = None
    min_value: float | None = Field(default=None, alias="min")
    max_value: float | None = Field(default=None, alias="max")
    nominal: float | None = None
    start: float | int | bool | str | None = None
```

### 3. Component and Parameter Models

```python
class Modification(CDLBaseModel):
    """Value modification or assignment"""
    name: str
    value: float | int | bool | str | dict[str, Any]
    final: bool = False

class ComponentDeclaration(CDLBaseModel):
    """Component (variable/instance) declaration"""
    name: str
    type_specifier: TypeSpecifier
    variability: CDLVariability = CDLVariability.CONTINUOUS
    causality: CDLCausality = CDLCausality.LOCAL
    quantity: Quantity | None = None
    modifications: list[Modification] = Field(default_factory=list)
    description: str | None = Field(default=None, alias="comment")
    condition: str | None = None  # Conditional declaration

class Parameter(CDLImmutableModel):
    """CDL parameter definition"""
    name: str
    type_kind: CDLTypeKind
    value: float | int | bool | str
    quantity: Quantity | None = None
    description: str | None = None
    final: bool = False

    @field_validator("value")
    @classmethod
    def validate_type_consistency(cls, v: Any, info: ValidationInfo) -> Any:
        """Ensure value type matches type_kind"""
        type_kind = info.data.get("type_kind")
        # Type validation logic
        return v
```

### 4. Connection Models

```python
class ConnectorReference(CDLImmutableModel):
    """Reference to a component connector (input/output)"""
    instance: str  # Instance name or "this" for local
    connector: str  # Connector name within instance

    def __str__(self) -> str:
        return f"{self.instance}.{self.connector}"

class Connection(CDLImmutableModel):
    """Connection between two connectors"""
    from_ref: ConnectorReference = Field(alias="from")
    to_ref: ConnectorReference = Field(alias="to")
    condition: str | None = None  # Conditional connection

    @field_validator("to_ref")
    @classmethod
    def validate_different_connectors(cls, v: ConnectorReference, info: ValidationInfo) -> ConnectorReference:
        """Ensure from and to are different"""
        from_ref = info.data.get("from_ref")
        if from_ref and str(from_ref) == str(v):
            raise ValueError("Cannot connect a connector to itself")
        return v

class Equation(CDLBaseModel):
    """CDL equation (connection or assignment)"""
    connections: list[Connection] = Field(default_factory=list)
    # Future: support algorithmic equations if needed
```

### 5. Graphics and Visualization Models

```python
from typing import Annotated

RGBColor = Annotated[int, Field(ge=0, le=255)]

class Point(CDLImmutableModel):
    """2D point for graphics"""
    x: float
    y: float

class Extent(CDLImmutableModel):
    """Bounding box defined by two points"""
    point1: Point
    point2: Point

class Color(CDLImmutableModel):
    """RGB color"""
    r: RGBColor
    g: RGBColor
    b: RGBColor

class LinePattern(str, Enum):
    """Line drawing patterns"""
    NONE = "LinePattern.None"
    SOLID = "LinePattern.Solid"
    DASH = "LinePattern.Dash"
    DOT = "LinePattern.Dot"
    DASH_DOT = "LinePattern.DashDot"
    DASH_DOT_DOT = "LinePattern.DashDotDot"

class Placement(CDLBaseModel):
    """Visual placement information for component"""
    visible: bool = True
    transformation: dict[str, Any]  # Origin, extent, rotation
    icon_visible: bool = True

class GraphicItem(CDLBaseModel):
    """Base for graphic elements"""
    visible: bool = True
    origin: Point = Field(default_factory=lambda: Point(x=0, y=0))
    rotation: float = 0.0

class Line(GraphicItem):
    """Line graphic element"""
    points: list[Point]
    color: Color = Field(default_factory=lambda: Color(r=0, g=0, b=0))
    pattern: LinePattern = LinePattern.SOLID
    thickness: float = 0.25

class Text(GraphicItem):
    """Text graphic element"""
    extent: Extent
    text_string: str
    font_size: int = 0
    font_name: str = ""
    text_color: Color = Field(default_factory=lambda: Color(r=0, g=0, b=0))

class Icon(CDLBaseModel):
    """Icon graphics for a component"""
    coordinate_system: dict[str, Any] | None = None
    graphics: list[Line | Text | dict[str, Any]] = Field(default_factory=list)

class Diagram(CDLBaseModel):
    """Diagram graphics"""
    coordinate_system: dict[str, Any] | None = None
    graphics: list[Line | Text | dict[str, Any]] = Field(default_factory=list)
```

### 6. Block and Class Models

```python
class ElementaryBlock(CDLBaseModel):
    """CDL elementary (built-in) block reference"""
    class_name: str  # e.g., "Buildings.Controls.OBC.CDL.Reals.Add"
    instance_name: str
    parameters: dict[str, Parameter] = Field(default_factory=dict)
    placement: Placement | None = None
    description: str | None = None

class CompositeBlock(CDLBaseModel):
    """User-defined composite block (contains other blocks)"""
    class_name: str
    instance_name: str
    parameters: dict[str, Parameter] = Field(default_factory=dict)
    placement: Placement | None = None
    description: str | None = None

class ClassDefinition(CDLBaseModel):
    """CDL class/block definition"""
    class_name: str
    within: str | None = None  # Package path
    description: str | None = Field(default=None, alias="comment")

    # Public interface
    public_parameters: dict[str, Parameter] = Field(default_factory=dict)
    inputs: dict[str, ComponentDeclaration] = Field(default_factory=dict)
    outputs: dict[str, ComponentDeclaration] = Field(default_factory=dict)

    # Internal structure
    protected_components: dict[str, ComponentDeclaration] = Field(default_factory=dict)
    instances: list[ElementaryBlock | CompositeBlock] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)

    # Visual representation
    icon: Icon | None = None
    diagram: Diagram | None = None

    # Metadata
    documentation: str | None = None
    version: str | None = None

    @property
    def is_elementary(self) -> bool:
        """Check if this is an elementary block (no internal instances)"""
        return len(self.instances) == 0
```

### 7. Top-Level Model Document

```python
class CDLDocument(CDLBaseModel):
    """Complete CDL model document (parsed from JSON)"""
    within: str | None = None
    modelica_file: str | None = Field(default=None, alias="modelicaFile")
    full_mo_file_path: str | None = Field(default=None, alias="fullMoFilePath")
    checksum: str | None = None

    class_definitions: list[ClassDefinition] = Field(alias="class_definition")

    @property
    def main_class(self) -> ClassDefinition | None:
        """Get the primary class definition"""
        return self.class_definitions[0] if self.class_definitions else None

    def find_class(self, class_name: str) -> ClassDefinition | None:
        """Find class by name"""
        for cls in self.class_definitions:
            if cls.class_name == class_name:
                return cls
        return None
```

## Model Organization in Source Tree

```
src/python_cdl/
├── __init__.py
├── models/
│   ├── __init__.py          # Re-export all public models
│   ├── base.py              # Base model classes
│   ├── types.py             # Type system models
│   ├── components.py        # Component, Parameter models
│   ├── connections.py       # Connection and equation models
│   ├── graphics.py          # Visualization models
│   ├── blocks.py            # Block and class models
│   └── document.py          # Top-level document model
├── parser/
│   ├── __init__.py
│   ├── json_parser.py       # Parse CDL JSON to Pydantic models
│   └── validator.py         # Additional validation logic
├── execution/
│   ├── __init__.py
│   ├── context.py           # Execution context
│   └── evaluator.py         # Block evaluation engine
└── utils/
    ├── __init__.py
    └── type_guards.py       # Type narrowing utilities
```

## Validation Strategy

### Built-in Pydantic Validation
- Field types and constraints
- Required vs optional fields
- Value ranges (min/max)
- String patterns
- Custom validators for cross-field validation

### Additional Semantic Validation
```python
class CDLValidator:
    """Semantic validation for CDL models"""

    @staticmethod
    def validate_connections(model: ClassDefinition) -> list[str]:
        """Validate all connections in a model"""
        errors = []
        # Check all inputs are connected
        # Check no algebraic loops
        # Verify connector types match
        return errors

    @staticmethod
    def validate_parameters(model: ClassDefinition) -> list[str]:
        """Validate parameter constraints"""
        errors = []
        # Check required parameters are set
        # Validate parameter dependencies
        return errors
```

## Performance Optimizations

1. **Lazy Loading**: Load graphics and documentation on demand
2. **Field Caching**: Cache computed properties with `@cached_property`
3. **Validation Modes**: Support strict/lenient modes
4. **Batch Validation**: Validate multiple models in parallel
5. **Index Structures**: Build lookup tables for large models

## Type Safety with Pyright

```python
# Type guards for narrowing
def is_elementary_block(block: ElementaryBlock | CompositeBlock) -> TypeGuard[ElementaryBlock]:
    return isinstance(block, ElementaryBlock)

# Generic typed lookups
T = TypeVar("T", bound=CDLBaseModel)

def find_component(model: ClassDefinition, name: str, component_type: type[T]) -> T | None:
    """Type-safe component lookup"""
    ...
```

## JSON Deserialization Example

```python
from pathlib import Path
import json

def load_cdl_document(file_path: Path) -> CDLDocument:
    """Load and validate CDL JSON document"""
    with open(file_path) as f:
        data = json.load(f)

    # Pydantic v2 deserialization with validation
    return CDLDocument.model_validate(data)

def load_cdl_document_lenient(file_path: Path) -> CDLDocument:
    """Load with lenient validation (skip unknown fields)"""
    with open(file_path) as f:
        data = json.load(f)

    # Context-based validation mode
    return CDLDocument.model_validate(
        data,
        context={"validate_graphics": False}
    )
```

## Serialization to JSON

```python
def save_cdl_document(doc: CDLDocument, file_path: Path) -> None:
    """Serialize CDL document to JSON"""
    json_data = doc.model_dump(
        mode="json",  # Use JSON-compatible types
        by_alias=True,  # Use field aliases
        exclude_none=True,  # Omit null fields
    )

    with open(file_path, "w") as f:
        json.dump(json_data, f, indent=2)
```

## Extension Points

### Custom Block Types
```python
class CustomBlock(CDLBaseModel):
    """Base for user-defined custom blocks"""
    block_type: Literal["custom"] = "custom"
    # Custom fields

# Register with block factory
BlockFactory.register("CustomBlock", CustomBlock)
```

### Custom Validators
```python
from pydantic import model_validator

class ExtendedClassDefinition(ClassDefinition):
    """Extended class with additional validation"""

    @model_validator(mode="after")
    def validate_custom_rules(self) -> Self:
        # Custom validation logic
        return self
```

## Migration Path

For future schema changes:
1. Use Pydantic's `@deprecated` decorator for old fields
2. Provide `@field_serializer` and `@field_validator` for backward compatibility
3. Version the models (e.g., `CDLDocumentV1`, `CDLDocumentV2`)
4. Implement migration functions between versions

## Next Steps

1. Implement base models in `models/base.py`
2. Implement type system in `models/types.py`
3. Build up component and connection models
4. Create JSON parser with comprehensive tests
5. Develop execution context architecture
6. Integrate with validation framework
