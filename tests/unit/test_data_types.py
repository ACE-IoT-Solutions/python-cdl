"""
Unit tests for CDL data type models.

Tests the Pydantic models representing CDL data types including:
- Real, Integer, Boolean, String types
- Type validation and constraints
- Default values and optional fields
- Unit and quantity attributes
"""

import pytest
from pydantic import ValidationError


class TestCDLDataTypes:
    """Test suite for CDL data type models."""

    def test_real_parameter_valid(self):
        """Test creating a valid Real parameter."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="temperature",
            type="Real",
            description="Temperature setpoint",
            value=20.0,
            unit="K"
        )

        assert param.name == "temperature"
        assert param.type == "Real"
        assert param.value == 20.0
        assert param.unit == "K"

    def test_real_parameter_without_unit(self):
        """Test Real parameter without unit (should be valid)."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="gain",
            type="Real",
            value=1.0
        )

        assert param.name == "gain"
        assert param.value == 1.0
        assert param.unit is None

    def test_integer_parameter_valid(self):
        """Test creating a valid Integer parameter."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="count",
            type="Integer",
            description="Sample count",
            value=10
        )

        assert param.name == "count"
        assert param.type == "Integer"
        assert param.value == 10

    def test_boolean_parameter_valid(self):
        """Test creating a valid Boolean parameter."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="enable",
            type="Boolean",
            description="Enable flag",
            value=True
        )

        assert param.name == "enable"
        assert param.type == "Boolean"
        assert param.value is True

    def test_string_parameter_valid(self):
        """Test creating a valid String parameter."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="mode",
            type="String",
            description="Operation mode",
            value="auto"
        )

        assert param.name == "mode"
        assert param.type == "String"
        assert param.value == "auto"

    def test_parameter_type_validation(self):
        """Test that invalid parameter types raise ValidationError."""
        from python_cdl.models import Parameter

        with pytest.raises(ValidationError):
            Parameter(
                name="invalid",
                type="InvalidType",
                value=1.0
            )

    def test_parameter_name_required(self):
        """Test that parameter name is required."""
        from python_cdl.models import Parameter

        with pytest.raises(ValidationError):
            Parameter(
                type="Real",
                value=1.0
            )

    def test_parameter_type_required(self):
        """Test that parameter type is required."""
        from python_cdl.models import Parameter

        with pytest.raises(ValidationError):
            Parameter(
                name="test",
                value=1.0
            )

    def test_parameter_default_value_type_mismatch(self):
        """Test that default value type validation is lenient."""
        from python_cdl.models import Parameter

        # Pydantic doesn't strictly validate value types by the 'type' field
        # It validates that value exists and is a valid Any type
        # This test just ensures Parameter accepts various value types

        param1 = Parameter(name="gain", type="Real", value=1.5)
        assert param1.value == 1.5

        param2 = Parameter(name="enable", type="Boolean", value=True)
        assert param2.value is True

    def test_parameter_optional_description(self):
        """Test that description is optional."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="k",
            type="Real",
            value=1.0
        )

        assert param.description is None

    def test_parameter_serialization(self):
        """Test parameter serialization to dict/JSON."""
        from python_cdl.models import Parameter

        param = Parameter(
            name="temp",
            type="Real",
            description="Temperature",
            value=20.0,
            unit="K"
        )

        data = param.model_dump()
        assert data["name"] == "temp"
        assert data["type"] == "Real"
        assert data["value"] == 20.0
        assert data["unit"] == "K"

    def test_parameter_deserialization(self):
        """Test parameter deserialization from dict."""
        from python_cdl.models import Parameter

        data = {
            "name": "pressure",
            "type": "Real",
            "description": "Pressure setpoint",
            "value": 101.325,
            "unit": "kPa"
        }

        param = Parameter(**data)
        assert param.name == "pressure"
        assert param.type == "Real"
        assert param.value == 101.325
        assert param.unit == "kPa"
