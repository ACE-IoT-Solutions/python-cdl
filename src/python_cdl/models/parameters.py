"""CDL parameter and constant models."""

from typing import Any

from pydantic import BaseModel, Field

from python_cdl.models.types import CDLTypeEnum


class Parameter(BaseModel):
    """Time-invariant parameter value."""

    name: str = Field(description="Parameter name")
    type: CDLTypeEnum = Field(description="Data type")
    value: Any = Field(description="Parameter value")
    quantity: str | None = Field(default=None, description="Physical quantity")
    unit: str | None = Field(default=None, description="Unit of measurement")
    min: float | int | None = Field(default=None, description="Minimum value")
    max: float | int | None = Field(default=None, description="Maximum value")
    description: str | None = Field(default=None, description="Natural language description")

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"


class Constant(BaseModel):
    """Constant value fixed at compilation."""

    name: str = Field(description="Constant name")
    type: CDLTypeEnum = Field(description="Data type")
    value: Any = Field(description="Constant value")
    quantity: str | None = Field(default=None, description="Physical quantity")
    unit: str | None = Field(default=None, description="Unit of measurement")
    description: str | None = Field(default=None, description="Natural language description")

    class Config:
        """Pydantic configuration."""

        frozen = True
        extra = "forbid"
