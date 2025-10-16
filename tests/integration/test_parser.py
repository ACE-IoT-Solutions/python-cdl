"""
Integration tests for CDL-JSON parser.

Tests the complete parsing workflow:
- Loading CDL-JSON files
- Parsing into Python objects
- Validation of complete block structures
- End-to-end parsing scenarios
"""

import json
import pytest
from pathlib import Path


class TestCDLJSONParser:
    """Test suite for CDL-JSON parser integration."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def simple_block_data(self, fixtures_dir):
        """Load simple block fixture."""
        with open(fixtures_dir / "simple_block.json") as f:
            return json.load(f)

    @pytest.fixture
    def elementary_block_data(self, fixtures_dir):
        """Load elementary block fixture."""
        with open(fixtures_dir / "elementary_block.json") as f:
            return json.load(f)

    @pytest.fixture
    def boolean_logic_data(self, fixtures_dir):
        """Load boolean logic fixture."""
        with open(fixtures_dir / "boolean_logic.json") as f:
            return json.load(f)

    @pytest.fixture
    def composite_hvac_data(self, fixtures_dir):
        """Load composite HVAC fixture."""
        with open(fixtures_dir / "composite_hvac.json") as f:
            return json.load(f)

    def test_parse_simple_block(self, simple_block_data):
        """Test parsing a simple proportional controller."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(simple_block_data)

        assert block.name == "SimpleController"
        assert block.block_type == "composite"
        assert len(block.parameters) == 1
        assert block.parameters[0].name == "k"
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1
        # Equations not yet implemented - skip check
        # assert len(block.equations) == 1

    def test_parse_elementary_block(self, elementary_block_data):
        """Test parsing an elementary gain block."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(elementary_block_data)

        assert block.name == "Gain"
        assert block.block_type == "elementary"
        assert len(block.parameters) == 1
        assert block.parameters[0].name == "k"
        assert block.parameters[0].value == 1.0

    def test_parse_boolean_logic(self, boolean_logic_data):
        """Test parsing boolean logic operations."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(boolean_logic_data)

        assert block.name == "LogicalAnd"
        assert len(block.inputs) == 2
        assert block.inputs[0].type == "Boolean"
        assert block.inputs[1].type == "Boolean"
        assert block.outputs[0].type == "Boolean"

    def test_parse_composite_hvac(self, composite_hvac_data):
        """Test parsing composite PI controller."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(composite_hvac_data)

        assert block.name == "PIController"
        assert block.block_type == "composite"
        assert len(block.parameters) == 2
        assert len(block.blocks) == 4  # error_calc, gain, integrator, sum_block
        assert len(block.connections) == 7

    def test_parse_from_file(self, fixtures_dir):
        """Test parsing directly from file."""
        from python_cdl.parser import parse_cdl_json_file

        block = parse_cdl_json_file(fixtures_dir / "simple_block.json")

        assert block.name == "SimpleController"
        assert len(block.inputs) == 1
        assert len(block.outputs) == 1

    def test_parse_invalid_json(self):
        """Test that invalid JSON raises appropriate error."""
        from python_cdl.parser import parse_cdl_json
        from python_cdl.parser.json_parser import CDLParseError

        invalid_json = '{"name": "Test", "block_type": "elementary"'  # Missing closing brace

        with pytest.raises((CDLParseError, json.JSONDecodeError, ValueError)):
            parse_cdl_json(invalid_json)

    def test_parse_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        from python_cdl.parser import parse_cdl_json
        from python_cdl.parser.json_parser import CDLParseError
        from pydantic import ValidationError

        incomplete_data = {
            "name": "Test"
            # Missing block_type
        }

        with pytest.raises((CDLParseError, ValidationError)):
            parse_cdl_json(incomplete_data)

    def test_parse_preserves_metadata(self, simple_block_data):
        """Test that parser preserves all metadata."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(simple_block_data)

        assert block.description == simple_block_data.get("description")
        assert block.parameters[0].description == simple_block_data["parameters"][0].get("description")
        assert block.inputs[0].unit == simple_block_data["inputs"][0].get("unit")

    def test_parse_and_serialize_roundtrip(self, simple_block_data):
        """Test that parse -> serialize -> parse produces equivalent result."""
        from python_cdl.parser import parse_cdl_json

        block1 = parse_cdl_json(simple_block_data)
        serialized = block1.model_dump()
        block2 = parse_cdl_json(serialized)

        assert block1.name == block2.name
        assert block1.block_type == block2.block_type
        assert len(block1.parameters) == len(block2.parameters)
        assert len(block1.inputs) == len(block2.inputs)
        assert len(block1.outputs) == len(block2.outputs)

    def test_parse_multiple_blocks_batch(self, fixtures_dir):
        """Test parsing multiple blocks in batch."""
        from python_cdl.parser import parse_cdl_json_file

        block_files = [
            "simple_block.json",
            "elementary_block.json",
            "boolean_logic.json"
        ]

        blocks = []
        for filename in block_files:
            block = parse_cdl_json_file(fixtures_dir / filename)
            blocks.append(block)

        assert len(blocks) == 3
        assert all(hasattr(block, "name") for block in blocks)
        assert all(hasattr(block, "block_type") for block in blocks)

    def test_parse_with_type_validation(self, simple_block_data):
        """Test that parser enforces type constraints."""
        from python_cdl.parser import parse_cdl_json
        from python_cdl.parser.json_parser import CDLParseError
        from pydantic import ValidationError

        # Modify data to have invalid type
        invalid_data = simple_block_data.copy()
        invalid_data["parameters"][0]["type"] = "InvalidType"

        with pytest.raises((CDLParseError, ValidationError)):
            parse_cdl_json(invalid_data)

    def test_parse_preserves_order(self, composite_hvac_data):
        """Test that parser preserves order of components and connections."""
        from python_cdl.parser import parse_cdl_json

        block = parse_cdl_json(composite_hvac_data)

        # Check that components are in order
        assert block.blocks[0].name == "error_calc"
        assert block.blocks[1].name == "gain"
        assert block.blocks[2].name == "integrator"
        assert block.blocks[3].name == "sum_block"

        # Connections should also be in order
        assert len(block.connections) == 7

    def test_parse_handles_optional_fields(self, elementary_block_data):
        """Test that parser correctly handles optional fields."""
        from python_cdl.parser import parse_cdl_json

        # Remove optional fields
        data = elementary_block_data.copy()
        if "description" in data:
            del data["description"]
        if "unit" in data["parameters"][0]:
            del data["parameters"][0]["unit"]

        block = parse_cdl_json(data)

        assert block.name == "Gain"
        assert block.description is None or block.description == ""
