"""CDL-JSON parser for converting JSON to CDL models."""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from python_cdl.models.blocks import (
    Block,
    CompositeBlock,
    ElementaryBlock,
    ExtensionBlock,
    IfBlock,
    ParallelBlock,
    SequenceBlock,
    WhileBlock,
)
from python_cdl.models.connections import Connection
from python_cdl.models.equations import Equation
from python_cdl.models.connectors import (
    BooleanInput,
    BooleanOutput,
    InputConnector,
    IntegerInput,
    IntegerOutput,
    OutputConnector,
    RealInput,
    RealOutput,
    StringInput,
    StringOutput,
)
from python_cdl.models.parameters import Constant, Parameter
from python_cdl.models.semantic import SemanticMetadata


class CDLParseError(Exception):
    """Exception raised when CDL-JSON parsing fails."""

    pass


class CDLParser:
    """Parser for CDL-JSON format."""

    def __init__(self):
        """Initialize the parser."""
        self._connector_type_map = {
            "RealInput": RealInput,
            "RealOutput": RealOutput,
            "IntegerInput": IntegerInput,
            "IntegerOutput": IntegerOutput,
            "BooleanInput": BooleanInput,
            "BooleanOutput": BooleanOutput,
            "StringInput": StringInput,
            "StringOutput": StringOutput,
        }

        self._block_type_map = {
            "Sequence": SequenceBlock,
            "Parallel": ParallelBlock,
            "If": IfBlock,
            "While": WhileBlock,
        }

    def parse_connector(
        self, data: dict[str, Any], direction: str
    ) -> InputConnector | OutputConnector:
        """Parse a connector from JSON data."""
        connector_type = data.get("type")
        if not connector_type:
            raise CDLParseError("Connector must have a 'type' field")

        # Construct full type name with direction
        full_type = f"{connector_type}{direction.capitalize()}"
        connector_class = self._connector_type_map.get(full_type)

        if not connector_class:
            raise CDLParseError(f"Unknown connector type: {full_type}")

        try:
            return connector_class(**data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid connector data: {e}") from e

    def parse_parameter(self, data: dict[str, Any]) -> Parameter:
        """Parse a parameter from JSON data."""
        try:
            return Parameter(**data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid parameter data: {e}") from e

    def parse_constant(self, data: dict[str, Any]) -> Constant:
        """Parse a constant from JSON data."""
        try:
            return Constant(**data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid constant data: {e}") from e

    def parse_connection(self, data: dict[str, Any]) -> Connection:
        """Parse a connection from JSON data."""
        # Make a copy to avoid modifying original
        conn_data = data.copy()

        # Support both explicit field names and dot notation
        if "from" in conn_data:
            from_parts = conn_data["from"].split(".", 1)
            conn_data["from_block"] = from_parts[0]
            conn_data["from_output"] = from_parts[1] if len(from_parts) > 1 else ""
            del conn_data["from"]  # Remove to avoid extra field error

        if "to" in conn_data:
            to_parts = conn_data["to"].split(".", 1)
            conn_data["to_block"] = to_parts[0]
            conn_data["to_input"] = to_parts[1] if len(to_parts) > 1 else ""
            del conn_data["to"]  # Remove to avoid extra field error

        try:
            return Connection(**conn_data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid connection data: {e}") from e

    def parse_semantic(self, data: dict[str, Any]) -> SemanticMetadata:
        """Parse semantic metadata from JSON data."""
        try:
            return SemanticMetadata(**data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid semantic metadata: {e}") from e

    def parse_equation(self, data: dict[str, Any]) -> Equation:
        """Parse an equation from JSON data."""
        try:
            return Equation(**data)
        except ValidationError as e:
            raise CDLParseError(f"Invalid equation: {e}") from e

    def parse_block(self, data: dict[str, Any]) -> Block:
        """Parse a block from JSON data."""
        block_type = data.get("block_type", data.get("type"))
        if not block_type:
            raise CDLParseError("Block must have a 'block_type' or 'type' field")

        # Determine category from 'category' field or infer from block_type
        category = data.get("category")
        if not category:
            # If block_type is 'composite', 'elementary', or 'extension', use it as category
            if block_type in ("composite", "elementary", "extension"):
                category = block_type
            else:
                category = "elementary"

        # Parse common fields
        name = data.get("name", "")
        if not name:
            raise CDLParseError("Block must have a 'name' field")

        # Handle parameters as list or dict (parameter bindings)
        params_data = data.get("parameters", [])
        if isinstance(params_data, dict):
            # Parameters as bindings (e.g., {"k": "parentK"}) - convert to simple parameters
            parameters = [
                Parameter(name=k, type="Real", value=v if not isinstance(v, str) else 0.0)
                for k, v in params_data.items()
            ]
        else:
            parameters = [
                self.parse_parameter(p) for p in params_data
            ]
        constants = [
            self.parse_constant(c) for c in data.get("constants", [])
        ]
        inputs = [
            self.parse_connector(i, "input") for i in data.get("inputs", [])
        ]
        outputs = [
            self.parse_connector(o, "output") for o in data.get("outputs", [])
        ]
        equations = [
            self.parse_equation(eq) for eq in data.get("equations", [])
        ]

        semantic = None
        if "semantic" in data and data["semantic"] is not None:
            semantic = self.parse_semantic(data["semantic"])

        # Determine block class based on type and category
        if category == "composite":
            # Parse child blocks and connections
            child_blocks_data = data.get("blocks", [])
            blocks = []
            for b in child_blocks_data:
                # If block doesn't have block_type, use 'type' field or default to elementary
                if "block_type" not in b and "type" in b:
                    b = b.copy()
                    b["block_type"] = b["type"]
                elif "block_type" not in b and "type" not in b:
                    b = b.copy()
                    b["block_type"] = "elementary"
                blocks.append(self.parse_block(b))

            connections = [
                self.parse_connection(c) for c in data.get("connections", [])
            ]

            # Check for specialized composite block types
            block_class = self._block_type_map.get(block_type, CompositeBlock)

            try:
                return block_class(
                    name=name,
                    block_type=block_type,
                    parameters=parameters,
                    constants=constants,
                    inputs=inputs,
                    outputs=outputs,
                    equations=equations,
                    semantic=semantic,
                    description=data.get("description"),
                    blocks=blocks,
                    connections=connections,
                    **{
                        k: v
                        for k, v in data.items()
                        if k
                        not in [
                            "name",
                            "block_type",
                            "type",
                            "category",
                            "parameters",
                            "constants",
                            "inputs",
                            "outputs",
                            "equations",
                            "semantic",
                            "description",
                            "blocks",
                            "connections",
                        ]
                    },
                )
            except ValidationError as e:
                raise CDLParseError(f"Invalid composite block data: {e}") from e

        elif category == "extension":
            try:
                return ExtensionBlock(
                    name=name,
                    block_type=block_type,
                    parameters=parameters,
                    constants=constants,
                    inputs=inputs,
                    outputs=outputs,
                    equations=equations,
                    semantic=semantic,
                    description=data.get("description"),
                    extension_data=data.get("extension_data", {}),
                    implementation_language=data.get("implementation_language"),
                    implementation_code=data.get("implementation_code"),
                )
            except ValidationError as e:
                raise CDLParseError(f"Invalid extension block data: {e}") from e

        else:  # elementary
            try:
                return ElementaryBlock(
                    name=name,
                    block_type=block_type,
                    parameters=parameters,
                    constants=constants,
                    inputs=inputs,
                    outputs=outputs,
                    equations=equations,
                    semantic=semantic,
                    description=data.get("description"),
                    implementation=data.get("implementation"),
                )
            except ValidationError as e:
                raise CDLParseError(f"Invalid elementary block data: {e}") from e

    def parse(self, json_data: dict[str, Any]) -> Block:
        """Parse CDL-JSON data into a Block."""
        return self.parse_block(json_data)


def parse_cdl_json(json_str: str | dict) -> Block:
    """Parse CDL-JSON string or dict into a Block.

    Args:
        json_str: JSON string or dict containing CDL data

    Returns:
        Parsed Block object

    Raises:
        CDLParseError: If parsing fails
    """
    if isinstance(json_str, dict):
        data = json_str
    else:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise CDLParseError(f"Invalid JSON: {e}") from e

    parser = CDLParser()
    return parser.parse(data)


def load_cdl_file(file_path: str | Path) -> Block:
    """Load and parse a CDL-JSON file.

    Args:
        file_path: Path to the CDL-JSON file

    Returns:
        Parsed Block object

    Raises:
        CDLParseError: If parsing fails
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        json_str = f.read()

    return parse_cdl_json(json_str)


# Alias for compatibility
parse_cdl_json_file = load_cdl_file
