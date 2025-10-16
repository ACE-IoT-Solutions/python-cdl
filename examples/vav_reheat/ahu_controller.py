"""Central AHU control sequences for VAV reheat system.

This module implements the primary control sequences for an Air Handling Unit (AHU)
in a VAV reheat system, including:
- Mode selection (Occupied/Unoccupied/Morning Warmup/Night Setback)
- Supply fan speed control with duct static pressure reset
- Return fan tracking
- Economizer control with mixed air temperature control
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from python_cdl.models.blocks import CompositeBlock, ElementaryBlock
from python_cdl.models.connectors import BooleanInput, BooleanOutput, RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum


class OperatingMode(str, Enum):
    """AHU operating modes."""

    OCCUPIED = "occupied"
    UNOCCUPIED = "unoccupied"
    MORNING_WARMUP = "morning_warmup"
    NIGHT_SETBACK = "night_setback"


class ModeSelector(CompositeBlock):
    """Mode selector using finite state machine for AHU operating modes.

    Determines the current operating mode based on:
    - Occupancy schedule
    - Zone temperature conditions
    - Outside air temperature
    - Time of day

    Transitions:
    - Unoccupied -> Morning Warmup: When approaching occupancy time and zones are cold
    - Morning Warmup -> Occupied: When zones reach temperature or occupancy begins
    - Occupied -> Unoccupied: When schedule indicates unoccupied period
    - Occupied -> Night Setback: When schedule indicates night setback period
    """

    def __init__(self, name: str = "ModeSelector", **kwargs: Any):
        """Initialize mode selector with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="ModeSelector",
            description="Finite state machine for AHU operating mode selection",
            inputs=[
                BooleanInput(
                    name="uOccupied",
                    description="Occupancy schedule input (true = occupied period)",
                ),
                RealInput(
                    name="TZonAve",
                    quantity="Temperature",
                    unit="degC",
                    description="Average zone temperature",
                ),
                RealInput(
                    name="TZonSet",
                    quantity="Temperature",
                    unit="degC",
                    description="Zone temperature setpoint",
                ),
                RealInput(
                    name="TOut",
                    quantity="Temperature",
                    unit="degC",
                    description="Outside air temperature",
                ),
                RealInput(
                    name="timeOfDay",
                    quantity="Time",
                    unit="h",
                    description="Time of day in hours (0-24)",
                ),
            ],
            outputs=[
                BooleanOutput(
                    name="yOccupied",
                    description="Occupied mode active",
                ),
                BooleanOutput(
                    name="yMorningWarmup",
                    description="Morning warmup mode active",
                ),
                BooleanOutput(
                    name="yNightSetback",
                    description="Night setback mode active",
                ),
                BooleanOutput(
                    name="yUnoccupied",
                    description="Unoccupied mode active",
                ),
            ],
            parameters=[
                Parameter(
                    name="tWarmupStart",
                    type=CDLTypeEnum.REAL,
                    value=1.0,
                    quantity="Time",
                    unit="h",
                    description="Hours before occupancy to start warmup",
                ),
                Parameter(
                    name="dTWarmup",
                    type=CDLTypeEnum.REAL,
                    value=2.0,
                    quantity="TemperatureDifference",
                    unit="K",
                    description="Temperature deficit to trigger warmup",
                ),
                Parameter(
                    name="tNightSetbackStart",
                    type=CDLTypeEnum.REAL,
                    value=22.0,
                    quantity="Time",
                    unit="h",
                    description="Time of day to start night setback",
                ),
            ],
            **kwargs,
        )


class PIController(ElementaryBlock):
    """Proportional-Integral controller for continuous control.

    Implements PI control algorithm:
    u(t) = Kp * e(t) + Ki * ∫e(τ)dτ

    Where:
    - e(t) is the control error (setpoint - measurement)
    - Kp is the proportional gain
    - Ki is the integral gain
    """

    def __init__(self, name: str = "PIController", **kwargs: Any):
        """Initialize PI controller with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="PIController",
            description="Proportional-Integral controller with anti-windup",
            inputs=[
                RealInput(
                    name="u_s",
                    description="Setpoint value",
                ),
                RealInput(
                    name="u_m",
                    description="Measured value",
                ),
                BooleanInput(
                    name="enable",
                    description="Enable controller (false = reset integral term)",
                ),
            ],
            outputs=[
                RealOutput(
                    name="y",
                    min=0.0,
                    max=1.0,
                    description="Control output (0-1)",
                ),
            ],
            parameters=[
                Parameter(
                    name="k",
                    type=CDLTypeEnum.REAL,
                    value=1.0,
                    description="Proportional gain",
                    min=0.0,
                ),
                Parameter(
                    name="Ti",
                    type=CDLTypeEnum.REAL,
                    value=60.0,
                    quantity="Time",
                    unit="s",
                    description="Integral time constant",
                    min=0.01,
                ),
                Parameter(
                    name="yMax",
                    type=CDLTypeEnum.REAL,
                    value=1.0,
                    description="Maximum controller output",
                ),
                Parameter(
                    name="yMin",
                    type=CDLTypeEnum.REAL,
                    value=0.0,
                    description="Minimum controller output",
                ),
            ],
            **kwargs,
        )


class SupplyFanController(CompositeBlock):
    """Supply fan speed controller with duct static pressure control.

    Controls VFD speed to maintain duct static pressure setpoint.
    Implements:
    - PI control for static pressure
    - Trim and respond logic for setpoint optimization
    - Minimum speed enforcement during occupied periods
    - Fan proving logic
    """

    def __init__(self, name: str = "SupplyFanController", **kwargs: Any):
        """Initialize supply fan controller with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="SupplyFanController",
            description="VFD speed control for supply fan with static pressure control",
            inputs=[
                RealInput(
                    name="pDuctSet",
                    quantity="Pressure",
                    unit="Pa",
                    description="Duct static pressure setpoint",
                ),
                RealInput(
                    name="pDuct",
                    quantity="Pressure",
                    unit="Pa",
                    description="Measured duct static pressure",
                ),
                BooleanInput(
                    name="uEnable",
                    description="Enable fan operation",
                ),
                BooleanInput(
                    name="uOccupied",
                    description="Occupied mode active",
                ),
            ],
            outputs=[
                RealOutput(
                    name="yFanSpeed",
                    min=0.0,
                    max=1.0,
                    description="Fan speed command (0-1)",
                ),
                BooleanOutput(
                    name="yFanStatus",
                    description="Fan running status",
                ),
                BooleanOutput(
                    name="yAlarm",
                    description="Fan alarm (failed to prove)",
                ),
            ],
            parameters=[
                Parameter(
                    name="kp",
                    type=CDLTypeEnum.REAL,
                    value=0.5,
                    description="Proportional gain for pressure control",
                ),
                Parameter(
                    name="Ti",
                    type=CDLTypeEnum.REAL,
                    value=60.0,
                    quantity="Time",
                    unit="s",
                    description="Integral time constant",
                ),
                Parameter(
                    name="spdMin",
                    type=CDLTypeEnum.REAL,
                    value=0.3,
                    description="Minimum fan speed when occupied",
                    min=0.0,
                    max=1.0,
                ),
                Parameter(
                    name="spdMinUnoccupied",
                    type=CDLTypeEnum.REAL,
                    value=0.15,
                    description="Minimum fan speed when unoccupied",
                    min=0.0,
                    max=1.0,
                ),
                Parameter(
                    name="tProveDelay",
                    type=CDLTypeEnum.REAL,
                    value=30.0,
                    quantity="Time",
                    unit="s",
                    description="Time delay for fan proving",
                ),
            ],
            **kwargs,
        )


class ReturnFanController(CompositeBlock):
    """Return fan tracking controller.

    Controls return fan to track supply fan airflow with configurable offset.
    Implements:
    - Airflow tracking with offset
    - Building pressure control influence
    - Minimum speed enforcement
    """

    def __init__(self, name: str = "ReturnFanController", **kwargs: Any):
        """Initialize return fan controller with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="ReturnFanController",
            description="Return fan speed tracking with building pressure control",
            inputs=[
                RealInput(
                    name="VSupAir",
                    quantity="VolumeFlowRate",
                    unit="m3/s",
                    description="Supply airflow rate",
                ),
                RealInput(
                    name="pBldg",
                    quantity="Pressure",
                    unit="Pa",
                    description="Building static pressure",
                ),
                RealInput(
                    name="pBldgSet",
                    quantity="Pressure",
                    unit="Pa",
                    description="Building pressure setpoint",
                ),
                BooleanInput(
                    name="uEnable",
                    description="Enable return fan",
                ),
            ],
            outputs=[
                RealOutput(
                    name="yFanSpeed",
                    min=0.0,
                    max=1.0,
                    description="Return fan speed command (0-1)",
                ),
            ],
            parameters=[
                Parameter(
                    name="kTracking",
                    type=CDLTypeEnum.REAL,
                    value=0.9,
                    description="Tracking gain (return flow as fraction of supply)",
                    min=0.0,
                    max=1.0,
                ),
                Parameter(
                    name="kPressure",
                    type=CDLTypeEnum.REAL,
                    value=0.02,
                    description="Building pressure control gain",
                ),
                Parameter(
                    name="spdMin",
                    type=CDLTypeEnum.REAL,
                    value=0.3,
                    description="Minimum return fan speed",
                    min=0.0,
                    max=1.0,
                ),
            ],
            **kwargs,
        )


class EconomizerController(CompositeBlock):
    """Economizer control with mixed air temperature control.

    Controls outdoor air, return air, and relief dampers to:
    - Maintain mixed air temperature setpoint
    - Maximize free cooling when conditions permit
    - Enforce minimum outdoor air requirements
    - Implement differential enthalpy economizer logic

    Damper Control Modes:
    - Minimum OA: Economizer disabled, maintain minimum outdoor air
    - Economizer: Modulate dampers to maintain mixed air temperature
    - 100% OA: Maximum free cooling when outdoor conditions are favorable
    """

    def __init__(self, name: str = "EconomizerController", **kwargs: Any):
        """Initialize economizer controller with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="EconomizerController",
            description="Economizer with mixed air temperature and enthalpy control",
            inputs=[
                RealInput(
                    name="TMixSet",
                    quantity="Temperature",
                    unit="degC",
                    description="Mixed air temperature setpoint",
                ),
                RealInput(
                    name="TMix",
                    quantity="Temperature",
                    unit="degC",
                    description="Measured mixed air temperature",
                ),
                RealInput(
                    name="TOut",
                    quantity="Temperature",
                    unit="degC",
                    description="Outside air temperature",
                ),
                RealInput(
                    name="TRet",
                    quantity="Temperature",
                    unit="degC",
                    description="Return air temperature",
                ),
                RealInput(
                    name="hOut",
                    quantity="SpecificEnthalpy",
                    unit="J/kg",
                    description="Outside air enthalpy",
                ),
                RealInput(
                    name="hRet",
                    quantity="SpecificEnthalpy",
                    unit="J/kg",
                    description="Return air enthalpy",
                ),
                RealInput(
                    name="VSupAir",
                    quantity="VolumeFlowRate",
                    unit="m3/s",
                    description="Supply airflow for minimum OA calculation",
                ),
                BooleanInput(
                    name="uEnable",
                    description="Enable economizer operation",
                ),
                BooleanInput(
                    name="uFreezeStat",
                    description="Freeze stat alarm (true = alarm active)",
                ),
            ],
            outputs=[
                RealOutput(
                    name="yOutDamper",
                    min=0.0,
                    max=1.0,
                    description="Outdoor air damper position (0=closed, 1=open)",
                ),
                RealOutput(
                    name="yRetDamper",
                    min=0.0,
                    max=1.0,
                    description="Return air damper position (0=closed, 1=open)",
                ),
                RealOutput(
                    name="yRelDamper",
                    min=0.0,
                    max=1.0,
                    description="Relief damper position (0=closed, 1=open)",
                ),
                BooleanOutput(
                    name="yEconomizerActive",
                    description="Economizer mode active (not at minimum OA)",
                ),
            ],
            parameters=[
                Parameter(
                    name="VOutMinFra",
                    type=CDLTypeEnum.REAL,
                    value=0.15,
                    description="Minimum outdoor air fraction",
                    min=0.0,
                    max=1.0,
                ),
                Parameter(
                    name="kp",
                    type=CDLTypeEnum.REAL,
                    value=0.5,
                    description="Proportional gain for mixed air temperature control",
                ),
                Parameter(
                    name="Ti",
                    type=CDLTypeEnum.REAL,
                    value=120.0,
                    quantity="Time",
                    unit="s",
                    description="Integral time constant",
                ),
                Parameter(
                    name="TOutLowLim",
                    type=CDLTypeEnum.REAL,
                    value=-5.0,
                    quantity="Temperature",
                    unit="degC",
                    description="Lower limit for economizer operation",
                ),
                Parameter(
                    name="TOutHighLim",
                    type=CDLTypeEnum.REAL,
                    value=21.0,
                    quantity="Temperature",
                    unit="degC",
                    description="Upper limit for economizer operation",
                ),
                Parameter(
                    name="hOutHighLim",
                    type=CDLTypeEnum.REAL,
                    value=65000.0,
                    quantity="SpecificEnthalpy",
                    unit="J/kg",
                    description="Maximum outdoor air enthalpy for economizer",
                ),
                Parameter(
                    name="dhEconomizerMin",
                    type=CDLTypeEnum.REAL,
                    value=5000.0,
                    quantity="SpecificEnthalpy",
                    unit="J/kg",
                    description="Minimum enthalpy difference (hRet - hOut) for economizer",
                ),
            ],
            **kwargs,
        )


class DuctPressureReset(CompositeBlock):
    """Duct static pressure setpoint reset based on zone demand.

    Implements trim and respond logic to optimize duct static pressure:
    - Increases pressure when zones are not satisfied
    - Decreases pressure to save energy when all zones are satisfied
    - Limits setpoint within acceptable range

    Logic:
    - If any zone damper > threshold: Trim up pressure setpoint
    - If all zone dampers < threshold for sustained period: Trim down setpoint
    - Rate limits applied to prevent instability
    """

    def __init__(self, name: str = "DuctPressureReset", **kwargs: Any):
        """Initialize duct pressure reset with inputs, outputs, and parameters."""
        super().__init__(
            name=name,
            block_type="DuctPressureReset",
            description="Duct static pressure setpoint reset using trim and respond",
            inputs=[
                RealInput(
                    name="uDamperPositions",
                    description="Array of VAV box damper positions (0-1)",
                    min=0.0,
                    max=1.0,
                ),
                BooleanInput(
                    name="uOccupied",
                    description="Occupied mode active",
                ),
            ],
            outputs=[
                RealOutput(
                    name="pDuctSet",
                    quantity="Pressure",
                    unit="Pa",
                    description="Duct static pressure setpoint",
                ),
            ],
            parameters=[
                Parameter(
                    name="pDuctSetMin",
                    type=CDLTypeEnum.REAL,
                    value=75.0,
                    quantity="Pressure",
                    unit="Pa",
                    description="Minimum duct static pressure setpoint",
                ),
                Parameter(
                    name="pDuctSetMax",
                    type=CDLTypeEnum.REAL,
                    value=400.0,
                    quantity="Pressure",
                    unit="Pa",
                    description="Maximum duct static pressure setpoint",
                ),
                Parameter(
                    name="pDuctSetOccupied",
                    type=CDLTypeEnum.REAL,
                    value=250.0,
                    quantity="Pressure",
                    unit="Pa",
                    description="Initial occupied setpoint",
                ),
                Parameter(
                    name="pDuctSetUnoccupied",
                    type=CDLTypeEnum.REAL,
                    value=100.0,
                    quantity="Pressure",
                    unit="Pa",
                    description="Initial unoccupied setpoint",
                ),
                Parameter(
                    name="damperThreshold",
                    type=CDLTypeEnum.REAL,
                    value=0.9,
                    description="Damper position threshold for trim up",
                    min=0.0,
                    max=1.0,
                ),
                Parameter(
                    name="trimAmount",
                    type=CDLTypeEnum.REAL,
                    value=25.0,
                    quantity="Pressure",
                    unit="Pa",
                    description="Pressure adjustment per trim cycle",
                ),
                Parameter(
                    name="trimInterval",
                    type=CDLTypeEnum.REAL,
                    value=300.0,
                    quantity="Time",
                    unit="s",
                    description="Time between trim adjustments",
                ),
                Parameter(
                    name="respondTime",
                    type=CDLTypeEnum.REAL,
                    value=30.0,
                    quantity="Time",
                    unit="s",
                    description="Response time for immediate pressure increase",
                ),
            ],
            **kwargs,
        )
