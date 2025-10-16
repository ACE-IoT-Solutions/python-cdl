"""CDL equation models."""

from pydantic import BaseModel, Field


class Equation(BaseModel):
    """Equation model for CDL blocks.

    Represents an assignment equation: lhs = rhs
    """

    lhs: str = Field(description="Left-hand side (variable being assigned)")
    rhs: str = Field(description="Right-hand side (expression to evaluate)")
    description: str | None = Field(default=None, description="Optional description")

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"
