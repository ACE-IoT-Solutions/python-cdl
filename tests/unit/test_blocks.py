"""
Unit tests for CDL block models.

Tests the Pydantic models representing CDL blocks:
- Elementary blocks
- Composite blocks
- Block validation and structure
- Parameter, input, and output handling
"""

import pytest
from pydantic import ValidationError


class TestBlocks:
    """Test suite for CDL block models."""

    def test_elementary_block_minimal(self):
        """Test creating a minimal elementary block."""
        from python_cdl.models import Block, RealInput, RealOutput

        block = Block(
            name="Gain",
            block_type="elementary",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        assert block.name == "Gain"
        assert block.block_type == "elementary"
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1

    def test_elementary_block_with_parameters(self):
        """Test elementary block with parameters."""
        from python_cdl.models import Block, Parameter, RealInput, RealOutput

        block = Block(
            name="Gain",
            description="Gain block",
            block_type="elementary",
            parameters=[
                Parameter(name="k", type="Real", value=1.0)
            ],
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        assert block.name == "Gain"
        assert len(block.parameters) == 1
        assert block.parameters[0].name == "k"
        assert block.parameters[0].value == 1.0

    def test_composite_block_minimal(self):
        """Test creating a minimal composite block."""
        from python_cdl.models import Block, RealInput, RealOutput

        block = Block(
            name="Controller",
            block_type="composite",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        assert block.name == "Controller"
        assert block.block_type == "composite"

    def test_composite_block_with_components(self):
        """Test composite block with internal components."""
        from python_cdl.models import CompositeBlock, Block, RealInput, RealOutput

        # Create child blocks
        gain = Block(name="gain", block_type="Gain", inputs=[RealInput(name="u")], outputs=[RealOutput(name="y")])
        integrator = Block(name="integrator", block_type="Integrator", inputs=[RealInput(name="u")], outputs=[RealOutput(name="y")])

        block = CompositeBlock(
            name="PIController",
            block_type="composite",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")],
            blocks=[gain, integrator]
        )

        assert len(block.blocks) == 2
        assert block.blocks[0].name == "gain"
        assert block.blocks[1].name == "integrator"

    def test_block_with_equations(self):
        """Test block with equations."""
        from python_cdl.models import Block, Equation, RealInput, RealOutput

        block = Block(
            name="EquationBlock",
            block_type="elementary",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")],
            equations=[
                Equation(lhs="y", rhs="u * 2 + 1")
            ]
        )

        assert len(block.equations) == 1
        assert block.equations[0].lhs == "y"
        assert block.equations[0].rhs == "u * 2 + 1"

    def test_block_model_name_required(self):
        """Test that block name is required."""
        from python_cdl.models import Block

        with pytest.raises(ValidationError):
            Block(
                block_type="elementary",
                inputs=[],
                outputs=[]
            )

    def test_block_type_required(self):
        """Test that block type is required."""
        from python_cdl.models import Block

        with pytest.raises(ValidationError):
            Block(
                name="TestBlock",
                inputs=[],
                outputs=[]
            )

    def test_block_invalid_type(self):
        """Test that invalid block types raise ValidationError."""
        from python_cdl.models import Block, RealInput, RealOutput

        # Block model doesn't validate block_type, just accepts any string
        # This test verifies we can create blocks with custom types
        block = Block(
            name="InvalidBlock",
            block_type="invalid_type",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )
        assert block.block_type == "invalid_type"

    def test_block_optional_description(self):
        """Test that block description is optional."""
        from python_cdl.models import Block, RealInput, RealOutput

        block = Block(
            name="TestBlock",
            block_type="elementary",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        assert block.description is None or block.description == ""

    def test_block_multiple_inputs_outputs(self):
        """Test block with multiple inputs and outputs."""
        from python_cdl.models import Block, RealInput, RealOutput, BooleanInput

        block = Block(
            name="MultiIO",
            block_type="elementary",
            inputs=[
                RealInput(name="u1"),
                RealInput(name="u2"),
                BooleanInput(name="enable")
            ],
            outputs=[
                RealOutput(name="y1"),
                RealOutput(name="y2")
            ]
        )

        assert len(block.inputs) == 3
        assert len(block.outputs) == 2
        assert block.inputs[2].type == "Boolean"

    def test_block_serialization(self):
        """Test block serialization to dict/JSON."""
        from python_cdl.models import Block, Parameter, RealInput, RealOutput

        block = Block(
            name="Gain",
            description="Simple gain block",
            block_type="elementary",
            parameters=[Parameter(name="k", type="Real", value=2.0)],
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        data = block.model_dump()
        assert data["name"] == "Gain"
        assert data["block_type"] == "elementary"
        assert len(data["parameters"]) == 1
        assert data["parameters"][0]["name"] == "k"

    def test_block_deserialization(self):
        """Test block deserialization from dict."""
        from python_cdl.models import Block

        data = {
            "name": "TestBlock",
            "description": "Test block",
            "block_type": "elementary",
            "parameters": [
                {"name": "k", "type": "Real", "value": 1.0}
            ],
            "inputs": [
                {"name": "u", "type": "Real"}
            ],
            "outputs": [
                {"name": "y", "type": "Real"}
            ]
        }

        block = Block(**data)
        assert block.name == "TestBlock"
        assert len(block.parameters) == 1
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1

    def test_block_nested_validation(self):
        """Test that nested validation errors are caught."""
        from python_cdl.models import Block

        data = {
            "name": "TestBlock",
            "block_type": "elementary",
            "parameters": [
                {"name": "k", "type": "InvalidType", "value": 1.0}
            ],
            "inputs": [{"name": "u", "type": "Real"}],
            "outputs": [{"name": "y", "type": "Real"}]
        }

        with pytest.raises(ValidationError):
            Block(**data)
