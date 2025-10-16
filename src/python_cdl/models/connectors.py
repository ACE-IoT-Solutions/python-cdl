"""CDL connector models for inputs and outputs."""

from typing import Literal

from pydantic import BaseModel, Field

from python_cdl.models.types import CDLTypeEnum


class Connector(BaseModel):
    """Base class for all connectors."""

    name: str = Field(description="Connector name")
    type: CDLTypeEnum = Field(description="Data type of the connector")
    quantity: str | None = Field(default=None, description="Physical quantity")
    unit: str | None = Field(default=None, description="Unit of measurement")
    description: str | None = Field(default=None, description="Natural language description")

    class Config:
        """Pydantic configuration."""

        frozen = False
        extra = "forbid"
        use_enum_values = True


class InputConnector(Connector):
    """Input connector for receiving values."""

    direction: Literal["input"] = "input"


class OutputConnector(Connector):
    """Output connector for providing values."""

    direction: Literal["output"] = "output"


class RealInput(InputConnector):
    """Real-valued input connector."""

    type: Literal[CDLTypeEnum.REAL] = CDLTypeEnum.REAL
    min: float | None = None
    max: float | None = None


class RealOutput(OutputConnector):
    """Real-valued output connector."""

    type: Literal[CDLTypeEnum.REAL] = CDLTypeEnum.REAL
    min: float | None = None
    max: float | None = None


class IntegerInput(InputConnector):
    """Integer-valued input connector."""

    type: Literal[CDLTypeEnum.INTEGER] = CDLTypeEnum.INTEGER
    min: int | None = None
    max: int | None = None


class IntegerOutput(OutputConnector):
    """Integer-valued output connector."""

    type: Literal[CDLTypeEnum.INTEGER] = CDLTypeEnum.INTEGER
    min: int | None = None
    max: int | None = None


class BooleanInput(InputConnector):
    """Boolean-valued input connector."""

    type: Literal[CDLTypeEnum.BOOLEAN] = CDLTypeEnum.BOOLEAN


class BooleanOutput(OutputConnector):
    """Boolean-valued output connector."""

    type: Literal[CDLTypeEnum.BOOLEAN] = CDLTypeEnum.BOOLEAN


class StringInput(InputConnector):
    """String-valued input connector."""

    type: Literal[CDLTypeEnum.STRING] = CDLTypeEnum.STRING


class StringOutput(OutputConnector):
    """String-valued output connector."""

    type: Literal[CDLTypeEnum.STRING] = CDLTypeEnum.STRING
