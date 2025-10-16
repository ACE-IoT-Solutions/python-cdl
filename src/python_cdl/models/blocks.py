"""CDL block models for elementary, composite, and extension blocks."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from python_cdl.models.connectors import InputConnector, OutputConnector
from python_cdl.models.connections import Connection
from python_cdl.models.equations import Equation
from python_cdl.models.parameters import Constant, Parameter
from python_cdl.models.semantic import SemanticMetadata


class Block(BaseModel):
    """Base class for all CDL blocks."""

    name: str = Field(description="Block name")
    block_type: str = Field(description="Type identifier for the block")
    parameters: list[Parameter] = Field(default_factory=list, description="Block parameters")
    constants: list[Constant] = Field(default_factory=list, description="Block constants")
    inputs: list[InputConnector] = Field(default_factory=list, description="Input connectors")
    outputs: list[OutputConnector] = Field(default_factory=list, description="Output connectors")
    equations: list[Equation] = Field(default_factory=list, description="Block equations")
    semantic: SemanticMetadata | None = Field(default=None, description="Semantic metadata")
    description: str | None = Field(default=None, description="Natural language description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate block name is not empty."""
        if not v or not v.strip():
            raise ValueError("Block name cannot be empty")
        return v.strip()

    def get_input(self, name: str) -> InputConnector | None:
        """Get input connector by name."""
        return next((inp for inp in self.inputs if inp.name == name), None)

    def get_output(self, name: str) -> OutputConnector | None:
        """Get output connector by name."""
        return next((out for out in self.outputs if out.name == name), None)

    def get_parameter(self, name: str) -> Parameter | None:
        """Get parameter by name."""
        return next((p for p in self.parameters if p.name == name), None)

    def get_constant(self, name: str) -> Constant | None:
        """Get constant by name."""
        return next((c for c in self.constants if c.name == name), None)

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"


class ElementaryBlock(Block):
    """Elementary block with built-in functionality."""

    category: Literal["elementary"] = "elementary"
    implementation: str | None = Field(
        default=None,
        description="Implementation identifier or reference",
    )


class CompositeBlock(Block):
    """Composite block composed of other blocks."""

    category: Literal["composite"] = "composite"
    blocks: list[Block] = Field(default_factory=list, description="Child blocks")
    connections: list[Connection] = Field(default_factory=list, description="Internal connections")

    @field_validator("connections")
    @classmethod
    def validate_connections(cls, v: list[Connection], info) -> list[Connection]:
        """Validate all connections reference valid blocks and connectors."""
        blocks = info.data.get("blocks", [])
        block_names = {block.name for block in blocks}

        # Add composite block's own inputs and outputs as valid connection endpoints
        inputs = info.data.get("inputs", [])
        outputs = info.data.get("outputs", [])
        boundary_names = {inp.name for inp in inputs} | {out.name for out in outputs}

        for conn in v:
            # Allow connections from internal blocks or from composite boundary
            if conn.from_block not in block_names and conn.from_block not in boundary_names:
                raise ValueError(f"Connection source block '{conn.from_block}' not found")
            # Allow connections to internal blocks or to composite boundary
            if conn.to_block not in block_names and conn.to_block not in boundary_names:
                raise ValueError(f"Connection target block '{conn.to_block}' not found")

        return v


class ExtensionBlock(Block):
    """Extension block allowing custom implementations."""

    category: Literal["extension"] = "extension"
    extension_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom extension data",
    )
    implementation_language: str | None = Field(
        default=None,
        description="Implementation language (e.g., 'Python', 'JavaScript')",
    )
    implementation_code: str | None = Field(
        default=None,
        description="Implementation code or reference",
    )


class SequenceBlock(CompositeBlock):
    """Sequential execution block - blocks execute in order."""

    block_type: Literal["Sequence"] = "Sequence"
    execution_order: list[str] = Field(
        default_factory=list,
        description="Ordered list of block names to execute",
    )

    @field_validator("execution_order")
    @classmethod
    def validate_execution_order(cls, v: list[str], info) -> list[str]:
        """Validate all blocks in execution order exist."""
        blocks = info.data.get("blocks", [])
        block_names = {block.name for block in blocks}

        for block_name in v:
            if block_name not in block_names:
                raise ValueError(f"Block '{block_name}' in execution_order not found")

        return v


class ParallelBlock(CompositeBlock):
    """Parallel execution block - blocks execute concurrently."""

    block_type: Literal["Parallel"] = "Parallel"
    parallel_groups: list[list[str]] = Field(
        default_factory=list,
        description="Groups of block names that can execute in parallel",
    )


class IfBlock(CompositeBlock):
    """Conditional execution block."""

    block_type: Literal["If"] = "If"
    condition_input: str = Field(description="Name of boolean input for condition")
    then_blocks: list[str] = Field(
        default_factory=list,
        description="Block names to execute when condition is true",
    )
    else_blocks: list[str] = Field(
        default_factory=list,
        description="Block names to execute when condition is false",
    )


class WhileBlock(CompositeBlock):
    """Loop execution block."""

    block_type: Literal["While"] = "While"
    condition_input: str = Field(description="Name of boolean input for loop condition")
    loop_blocks: list[str] = Field(
        default_factory=list,
        description="Block names to execute in loop body",
    )
    max_iterations: int | None = Field(
        default=None,
        description="Maximum number of iterations to prevent infinite loops",
    )
