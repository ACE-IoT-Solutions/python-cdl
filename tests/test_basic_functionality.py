"""
Basic functionality tests using actual implementation API.

This test file demonstrates the correct usage of the Python CDL library
and serves as a reference for updating other tests.
"""

import pytest
from pathlib import Path


class TestBasicFunctionality:
    """Test basic CDL library functionality with actual API."""

    def test_create_parameter(self):
        """Test creating a Parameter with the actual model."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="gain",
            type="Real",
            value=1.5,
            unit="1",
            description="Proportional gain"
        )

        assert param.name == "gain"
        assert param.type == "Real"
        assert param.value == 1.5
        assert param.unit == "1"
        assert param.description == "Proportional gain"

    def test_create_connectors(self):
        """Test creating Input/Output connectors."""
        from python_cdl.models import RealInput, RealOutput

        input_conn = RealInput(
            name="u",
            description="Input signal"
        )

        output_conn = RealOutput(
            name="y",
            description="Output signal"
        )

        assert input_conn.name == "u"
        assert input_conn.type == "Real"
        assert output_conn.name == "y"
        assert output_conn.type == "Real"

    def test_create_elementary_block(self):
        """Test creating an ElementaryBlock."""
        from python_cdl.models import ElementaryBlock, RealInput, RealOutput, Parameter

        block = ElementaryBlock(
            name="GainBlock",
            block_type="Continuous.Gain",
            description="Simple gain block",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")],
            parameters=[Parameter(name="k", type="Real", value=2.0)]
        )

        assert block.name == "GainBlock"
        assert block.block_type == "Continuous.Gain"
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1
        assert len(block.parameters) == 1
        assert block.parameters[0].value == 2.0

    def test_create_composite_block(self):
        """Test creating a CompositeBlock with components."""
        from python_cdl.models import (
            CompositeBlock,
            ElementaryBlock,
            RealInput,
            RealOutput,
            Parameter,
            Connection
        )

        # Create component blocks
        gain = ElementaryBlock(
            name="gain",
            block_type="Continuous.Gain",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")],
            parameters=[Parameter(name="k", type="Real", value=2.0)]
        )

        limiter = ElementaryBlock(
            name="limiter",
            block_type="Continuous.Min",
            inputs=[RealInput(name="u1"), RealInput(name="u2")],
            outputs=[RealOutput(name="y")]
        )

        # Create composite
        composite = CompositeBlock(
            name="LimitedGain",
            block_type="LimitedGain",
            inputs=[RealInput(name="input"), RealInput(name="max_value")],
            outputs=[RealOutput(name="output")],
            blocks=[gain, limiter],
            connections=[
                Connection(from_block="input", from_output="", to_block="gain", to_input="u"),
                Connection(from_block="gain", from_output="y", to_block="limiter", to_input="u1"),
                Connection(from_block="max_value", from_output="", to_block="limiter", to_input="u2"),
                Connection(from_block="limiter", from_output="y", to_block="output", to_input="")
            ]
        )

        assert composite.name == "LimitedGain"
        assert len(composite.blocks) == 2
        assert len(composite.connections) == 4

    def test_load_cdl_file(self):
        """Test loading a CDL-JSON file."""
        from python_cdl import load_cdl_file

        # Use the working example file
        cdl_file = Path(__file__).parent.parent / "examples" / "p_controller_limiter.json"

        if cdl_file.exists():
            controller = load_cdl_file(str(cdl_file))

            assert controller.name == "CustomPWithLimiter"
            assert controller.block_type == "CustomPWithLimiter"
            assert len(controller.inputs) == 2
            assert len(controller.outputs) == 1
            assert len(controller.blocks) == 2
            assert len(controller.connections) == 4
        else:
            pytest.skip(f"Example file not found: {cdl_file}")

    def test_block_validator(self):
        """Test BlockValidator with actual API."""
        from python_cdl import BlockValidator
        from python_cdl.models import ElementaryBlock, RealInput, RealOutput

        validator = BlockValidator()

        block = ElementaryBlock(
            name="TestBlock",
            block_type="Test.Block",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")]
        )

        result = validator.validate(block)

        # Should be valid (minimal block structure)
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')

    def test_execution_context(self):
        """Test ExecutionContext with actual API."""
        from python_cdl import ExecutionContext
        from python_cdl.models import ElementaryBlock, RealInput, RealOutput, Parameter

        block = ElementaryBlock(
            name="GainBlock",
            block_type="Continuous.Gain",
            inputs=[RealInput(name="u")],
            outputs=[RealOutput(name="y")],
            parameters=[Parameter(name="k", type="Real", value=3.0)]
        )

        context = ExecutionContext(block)

        # Test setting inputs
        context.set_input("u", 5.0)

        # Test getting state
        assert hasattr(context, 'current_time')
        assert hasattr(context, 'step_count')

    def test_parse_cdl_json_string(self):
        """Test parsing CDL-JSON from string."""
        from python_cdl import parse_cdl_json

        json_str = """{
            "name": "SimpleBlock",
            "block_type": "Simple.Block",
            "category": "elementary",
            "inputs": [
                {"name": "u", "type": "Real"}
            ],
            "outputs": [
                {"name": "y", "type": "Real"}
            ]
        }"""

        block = parse_cdl_json(json_str)

        assert block.name == "SimpleBlock"
        assert block.block_type == "Simple.Block"
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1

    def test_connection_model(self):
        """Test Connection model."""
        from python_cdl.models import Connection

        conn = Connection(
            from_block="block1",
            from_output="y",
            to_block="block2",
            to_input="u",
            description="Connect output to input"
        )

        assert conn.from_block == "block1"
        assert conn.from_output == "y"
        assert conn.to_block == "block2"
        assert conn.to_input == "u"

    def test_semantic_metadata(self):
        """Test SemanticMetadata model."""
        from python_cdl.models import SemanticMetadata

        metadata = SemanticMetadata(
            brick_class="brick:Temperature_Sensor",
            haystack_tags=["temp", "sensor", "zone"],
            s223p_type="s223:TemperatureSensor"
        )

        assert metadata.brick_class == "brick:Temperature_Sensor"
        assert "temp" in metadata.haystack_tags
        assert metadata.s223p_type == "s223:TemperatureSensor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
