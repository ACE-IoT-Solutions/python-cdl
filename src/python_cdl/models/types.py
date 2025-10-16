"""CDL data types with validation."""

from enum import Enum as PyEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CDLTypeEnum(str, PyEnum):
    """Enumeration of CDL data types."""

    REAL = "Real"
    INTEGER = "Integer"
    BOOLEAN = "Boolean"
    STRING = "String"
    ENUMERATION = "Enumeration"


class CDLType(BaseModel):
    """Base class for all CDL data types."""

    type: CDLTypeEnum
    description: str | None = Field(default=None, description="Natural language description")

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"


class Real(CDLType):
    """Real number type with optional quantity, unit, and bounds."""

    type: Literal[CDLTypeEnum.REAL] = CDLTypeEnum.REAL
    value: float | None = None
    quantity: str | None = Field(default=None, description="Physical quantity (e.g., 'Temperature')")
    unit: str | None = Field(default=None, description="Unit of measurement (e.g., 'degC')")
    min: float | None = Field(default=None, description="Minimum value")
    max: float | None = Field(default=None, description="Maximum value")

    @field_validator("value")
    @classmethod
    def validate_bounds(cls, v: float | None, info) -> float | None:
        """Validate value is within bounds if specified."""
        if v is None:
            return v

        min_val = info.data.get("min")
        max_val = info.data.get("max")

        if min_val is not None and v < min_val:
            raise ValueError(f"Value {v} is less than minimum {min_val}")
        if max_val is not None and v > max_val:
            raise ValueError(f"Value {v} is greater than maximum {max_val}")

        return v


class Integer(CDLType):
    """Integer type with optional bounds."""

    type: Literal[CDLTypeEnum.INTEGER] = CDLTypeEnum.INTEGER
    value: int | None = None
    min: int | None = Field(default=None, description="Minimum value")
    max: int | None = Field(default=None, description="Maximum value")

    @field_validator("value")
    @classmethod
    def validate_bounds(cls, v: int | None, info) -> int | None:
        """Validate value is within bounds if specified."""
        if v is None:
            return v

        min_val = info.data.get("min")
        max_val = info.data.get("max")

        if min_val is not None and v < min_val:
            raise ValueError(f"Value {v} is less than minimum {min_val}")
        if max_val is not None and v > max_val:
            raise ValueError(f"Value {v} is greater than maximum {max_val}")

        return v


class Boolean(CDLType):
    """Boolean type."""

    type: Literal[CDLTypeEnum.BOOLEAN] = CDLTypeEnum.BOOLEAN
    value: bool | None = None


class String(CDLType):
    """String type."""

    type: Literal[CDLTypeEnum.STRING] = CDLTypeEnum.STRING
    value: str | None = None


class Enumeration(CDLType):
    """Enumeration type with allowed values."""

    type: Literal[CDLTypeEnum.ENUMERATION] = CDLTypeEnum.ENUMERATION
    value: str | None = None
    allowed_values: list[str] = Field(description="List of allowed enumeration values")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str | None, info) -> str | None:
        """Validate value is in allowed values."""
        if v is None:
            return v

        allowed = info.data.get("allowed_values", [])
        if v not in allowed:
            raise ValueError(f"Value {v} not in allowed values: {allowed}")

        return v
