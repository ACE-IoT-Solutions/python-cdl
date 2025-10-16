"""Utility functions for programmatic CDL composition examples."""

import json
from pathlib import Path
from typing import Any

from python_cdl.models.blocks import Block, CompositeBlock
from python_cdl.parser import CDLParser
from python_cdl.validators import BlockValidator, GraphValidator


def export_block_to_json(block: Block, output_path: Path) -> dict[str, Any]:
    """Export a block to CDL-JSON format.

    Args:
        block: Block to export
        output_path: Path to save JSON file

    Returns:
        Dictionary containing the exported JSON data
    """
    # Use Pydantic's model_dump for JSON serialization
    cdl_json = block.model_dump(mode='json', exclude_none=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file with pretty formatting
    with open(output_path, 'w') as f:
        json.dump(cdl_json, f, indent=2, sort_keys=False)

    return cdl_json


def validate_block(block: Block, check_graph: bool = True) -> tuple[bool, list[str]]:
    """Validate a block's structure and optionally its connection graph.

    Args:
        block: Block to validate
        check_graph: Whether to also validate the connection graph

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    all_errors = []

    # Validate block structure
    block_validator = BlockValidator()
    is_valid, errors = block_validator.validate(block)

    if not is_valid:
        all_errors.extend([f"Block: {e}" for e in errors])

    # Validate connection graph if it's a composite block
    if check_graph and isinstance(block, CompositeBlock):
        graph_validator = GraphValidator()
        is_valid, errors = graph_validator.validate(block)

        if not is_valid:
            all_errors.extend([f"Graph: {e}" for e in errors])

    return len(all_errors) == 0, all_errors


def test_roundtrip(block: Block, json_path: Path) -> bool:
    """Test that a block can be exported and re-imported correctly.

    Args:
        block: Original block
        json_path: Path where JSON was saved

    Returns:
        True if round-trip was successful
    """
    try:
        # Parse the exported file
        parser = CDLParser()
        reimported = parser.parse_file(json_path)

        # Basic checks
        assert reimported.name == block.name, "Name mismatch"
        assert reimported.block_type == block.block_type, "Type mismatch"
        assert len(reimported.inputs) == len(block.inputs), "Input count mismatch"
        assert len(reimported.outputs) == len(block.outputs), "Output count mismatch"

        if isinstance(block, CompositeBlock):
            assert len(reimported.blocks) == len(block.blocks), "Block count mismatch"
            assert len(reimported.connections) == len(block.connections), "Connection count mismatch"

        return True

    except Exception as e:
        print(f"Round-trip test failed: {e}")
        return False


def print_block_summary(block: Block, indent: int = 0) -> None:
    """Print a formatted summary of a block's structure.

    Args:
        block: Block to summarize
        indent: Indentation level for nested blocks
    """
    prefix = "  " * indent

    print(f"{prefix}📦 {block.name} ({block.block_type})")

    if block.description:
        print(f"{prefix}   Description: {block.description}")

    # Inputs
    if block.inputs:
        print(f"{prefix}   Inputs ({len(block.inputs)}):")
        for inp in block.inputs:
            unit_str = f" [{inp.unit}]" if inp.unit else ""
            print(f"{prefix}     • {inp.name}: {inp.type}{unit_str}")

    # Outputs
    if block.outputs:
        print(f"{prefix}   Outputs ({len(block.outputs)}):")
        for out in block.outputs:
            unit_str = f" [{out.unit}]" if out.unit else ""
            print(f"{prefix}     • {out.name}: {out.type}{unit_str}")

    # Parameters
    if block.parameters:
        print(f"{prefix}   Parameters ({len(block.parameters)}):")
        for param in block.parameters[:3]:  # Show first 3
            unit_str = f" {param.unit}" if param.unit else ""
            print(f"{prefix}     • {param.name} = {param.value}{unit_str}")
        if len(block.parameters) > 3:
            print(f"{prefix}     ... and {len(block.parameters) - 3} more")

    # Nested blocks for composite
    if isinstance(block, CompositeBlock) and block.blocks:
        print(f"{prefix}   Internal Blocks ({len(block.blocks)}):")
        for child in block.blocks:
            print(f"{prefix}     • {child.name} ({child.block_type})")


def generate_graphviz(block: CompositeBlock, output_path: Path | None = None) -> str:
    """Generate a Graphviz DOT representation of a composite block.

    Args:
        block: Composite block to visualize
        output_path: Optional path to save .dot file

    Returns:
        DOT format string
    """
    lines = [
        "digraph ControlSystem {",
        "  rankdir=LR;",
        "  node [shape=box, style=rounded];",
        ""
    ]

    # Add nodes
    lines.append("  // External interfaces")
    for inp in block.inputs:
        lines.append(f'  "{inp.name}" [shape=circle, style=filled, fillcolor=lightblue];')

    for out in block.outputs:
        lines.append(f'  "{out.name}" [shape=circle, style=filled, fillcolor=lightgreen];')

    lines.append("\n  // Internal blocks")
    for child in block.blocks:
        label = f"{child.name}\\n({child.block_type})"
        lines.append(f'  "{child.name}" [label="{label}"];')

    # Add connections
    lines.append("\n  // Connections")
    for conn in block.connections:
        label = f' [label="{conn.from_port}→{conn.to_port}"]' if conn.from_port != conn.to_port else ""
        lines.append(f'  "{conn.from_block}" -> "{conn.to_block}"{label};')

    lines.append("}")

    dot_string = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(dot_string)

    return dot_string


def compare_blocks(block1: Block, block2: Block) -> dict[str, Any]:
    """Compare two blocks and return differences.

    Args:
        block1: First block
        block2: Second block

    Returns:
        Dictionary describing differences
    """
    differences = {
        "name": block1.name == block2.name,
        "type": block1.block_type == block2.block_type,
        "input_count": len(block1.inputs) == len(block2.inputs),
        "output_count": len(block1.outputs) == len(block2.outputs),
        "parameter_count": len(block1.parameters) == len(block2.parameters),
    }

    if isinstance(block1, CompositeBlock) and isinstance(block2, CompositeBlock):
        differences["block_count"] = len(block1.blocks) == len(block2.blocks)
        differences["connection_count"] = len(block1.connections) == len(block2.connections)

    return differences
