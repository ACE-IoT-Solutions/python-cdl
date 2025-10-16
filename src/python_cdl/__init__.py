"""Python CDL - Controls Description Language processor.

This package provides a complete implementation for processing CDL-JSON
into executable Python objects, following the CDL specification from
https://obc.lbl.gov/specification/cdl.html

Key features:
- Pydantic models for type-safe CDL constructs
- CDL-JSON parser with validation
- Execution context and runtime engine
- Graph validators for acyclic dependency checking
- Support for all CDL block types (Elementary, Composite, Extension)
- Support for control flow (Sequence, Parallel, If, While)
"""

from python_cdl.models import (
    Block,
    Boolean,
    BooleanInput,
    BooleanOutput,
    CDLType,
    CompositeBlock,
    Connection,
    Constant,
    ElementaryBlock,
    Enumeration,
    ExtensionBlock,
    IfBlock,
    InputConnector,
    Integer,
    IntegerInput,
    IntegerOutput,
    OutputConnector,
    ParallelBlock,
    Parameter,
    Real,
    RealInput,
    RealOutput,
    SemanticMetadata,
    SequenceBlock,
    String,
    StringInput,
    StringOutput,
    WhileBlock,
)
from python_cdl.parser import CDLParser, load_cdl_file, parse_cdl_json
from python_cdl.runtime import (
    BlockExecutor,
    ExecutionContext,
    ExecutionEvent,
    ExecutionResult,
)
from python_cdl.validators import (
    BlockValidator,
    GraphValidator,
    ValidationError,
    ValidationResult,
    detect_cycles,
    validate_connections,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Models - Types
    "CDLType",
    "Real",
    "Integer",
    "Boolean",
    "String",
    "Enumeration",
    # Models - Connectors
    "InputConnector",
    "OutputConnector",
    "RealInput",
    "RealOutput",
    "IntegerInput",
    "IntegerOutput",
    "BooleanInput",
    "BooleanOutput",
    "StringInput",
    "StringOutput",
    # Models - Parameters
    "Parameter",
    "Constant",
    # Models - Connections
    "Connection",
    # Models - Blocks
    "Block",
    "ElementaryBlock",
    "CompositeBlock",
    "ExtensionBlock",
    "SequenceBlock",
    "ParallelBlock",
    "IfBlock",
    "WhileBlock",
    # Models - Semantic
    "SemanticMetadata",
    # Parser
    "CDLParser",
    "parse_cdl_json",
    "load_cdl_file",
    # Runtime
    "ExecutionContext",
    "ExecutionEvent",
    "BlockExecutor",
    "ExecutionResult",
    # Validators
    "BlockValidator",
    "GraphValidator",
    "ValidationError",
    "ValidationResult",
    "detect_cycles",
    "validate_connections",
]


def main() -> None:
    """CLI entry point for python-cdl."""
    print("Python CDL - Controls Description Language Processor")
    print(f"Version: {__version__}")
    print()
    print("Usage:")
    print("  from python_cdl import parse_cdl_json, BlockExecutor")
    print()
    print("  # Parse CDL-JSON")
    print('  block = parse_cdl_json(json_string)')
    print()
    print("  # Execute block")
    print("  executor = BlockExecutor()")
    print("  result = executor.execute(block, inputs={'input1': 42})")
    print()
    print("For more information, visit:")
    print("  https://obc.lbl.gov/specification/cdl.html")
