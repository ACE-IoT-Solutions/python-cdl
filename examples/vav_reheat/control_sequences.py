"""Integrated AHU control sequences for VAV reheat system.

This module integrates all central AHU control sequences into a coordinated system:
- Mode selection determines operating state
- Fan controllers maintain proper airflow and pressurization
- Economizer optimizes energy usage through free cooling
- Pressure reset optimizes distribution efficiency

Control Coordination:
1. Mode selector determines current operating mode based on schedule and conditions
2. Duct pressure reset adjusts setpoint based on zone demand
3. Supply fan controller maintains duct static pressure
4. Return fan tracks supply fan with building pressure compensation
5. Economizer modulates dampers for mixed air temperature control

The system implements ASHRAE Guideline 36 High Performance Sequences of Operation.
"""

from typing import Any

from pydantic import Field

from python_cdl.models.blocks import CompositeBlock
from python_cdl.models.connections import Connection
from python_cdl.models.connectors import BooleanInput, BooleanOutput, RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum

from .ahu_controller import (
    DuctPressureReset,
    EconomizerController,
    ModeSelector,
    ReturnFanController,
    SupplyFanController,
)


class AHUControlSystem(CompositeBlock):
    """Complete AHU control system integrating all control sequences.

    This composite block coordinates all central AHU control functions:
    - Operating mode selection
    - Supply and return fan control
    - Economizer operation
    - Duct static pressure optimization

    The control system accepts high-level inputs (schedules, measurements)
    and produces all necessary actuator commands for the AHU.
    """

    def __init__(self, name: str = "AHUControlSystem", **kwargs: Any):
        """Initialize integrated AHU control system."""
        # Create child controller blocks
        mode_selector = ModeSelector(name="modeSelector")
        pressure_reset = DuctPressureReset(name="ductPressureReset")
        supply_fan = SupplyFanController(name="supplyFanController")
        return_fan = ReturnFanController(name="returnFanController")
        economizer = EconomizerController(name="economizerController")

        super().__init__(
            name=name,
            block_type="AHUControlSystem",
            description="Integrated AHU control system with mode selection, fan control, and economizer",
            # System-level inputs
            inputs=[
                # Schedule and occupancy
                BooleanInput(
                    name="uOccupancySchedule",
                    description="Occupancy schedule input",
                ),
                RealInput(
                    name="timeOfDay",
                    quantity="Time",
                    unit="h",
                    description="Current time of day (0-24)",
                ),
                # Zone conditions
                RealInput(
                    name="TZoneAverage",
                    quantity="Temperature",
                    unit="degC",
                    description="Average zone temperature",
                ),
                RealInput(
                    name="TZoneSetpoint",
                    quantity="Temperature",
                    unit="degC",
                    description="Zone temperature setpoint",
                ),
                RealInput(
                    name="uDamperPositions",
                    description="VAV box damper positions for trim/respond",
                ),
                # Air measurements
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
                    name="TMix",
                    quantity="Temperature",
                    unit="degC",
                    description="Mixed air temperature",
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
                # Pressure measurements
                RealInput(
                    name="pDuct",
                    quantity="Pressure",
                    unit="Pa",
                    description="Duct static pressure measurement",
                ),
                RealInput(
                    name="pBldg",
                    quantity="Pressure",
                    unit="Pa",
                    description="Building static pressure measurement",
                ),
                # Airflow measurements
                RealInput(
                    name="VSupAir",
                    quantity="VolumeFlowRate",
                    unit="m3/s",
                    description="Supply airflow measurement",
                ),
                # Safety inputs
                BooleanInput(
                    name="uFreezeStat",
                    description="Freeze stat alarm (true = freeze condition)",
                ),
                BooleanInput(
                    name="uEmergencyStop",
                    description="Emergency stop (true = stop all equipment)",
                ),
            ],
            # System-level outputs
            outputs=[
                # Operating mode indicators
                BooleanOutput(
                    name="yOccupiedMode",
                    description="System in occupied mode",
                ),
                BooleanOutput(
                    name="yMorningWarmupMode",
                    description="System in morning warmup mode",
                ),
                BooleanOutput(
                    name="yNightSetbackMode",
                    description="System in night setback mode",
                ),
                BooleanOutput(
                    name="yUnoccupiedMode",
                    description="System in unoccupied mode",
                ),
                # Fan commands
                RealOutput(
                    name="ySupplyFanSpeed",
                    min=0.0,
                    max=1.0,
                    description="Supply fan VFD speed command",
                ),
                RealOutput(
                    name="yReturnFanSpeed",
                    min=0.0,
                    max=1.0,
                    description="Return fan VFD speed command",
                ),
                BooleanOutput(
                    name="ySupplyFanStatus",
                    description="Supply fan running status",
                ),
                # Damper commands
                RealOutput(
                    name="yOutdoorDamper",
                    min=0.0,
                    max=1.0,
                    description="Outdoor air damper position command",
                ),
                RealOutput(
                    name="yReturnDamper",
                    min=0.0,
                    max=1.0,
                    description="Return air damper position command",
                ),
                RealOutput(
                    name="yReliefDamper",
                    min=0.0,
                    max=1.0,
                    description="Relief damper position command",
                ),
                # Status and diagnostics
                BooleanOutput(
                    name="yEconomizerActive",
                    description="Economizer operating (not at minimum OA)",
                ),
                RealOutput(
                    name="yDuctPressureSetpoint",
                    quantity="Pressure",
                    unit="Pa",
                    description="Current duct static pressure setpoint",
                ),
                BooleanOutput(
                    name="ySystemAlarm",
                    description="System alarm condition exists",
                ),
            ],
            # System-level parameters
            parameters=[
                Parameter(
                    name="TMixSetCooling",
                    type=CDLTypeEnum.REAL,
                    value=13.0,
                    quantity="Temperature",
                    unit="degC",
                    description="Mixed air temperature setpoint for cooling",
                ),
                Parameter(
                    name="TMixSetHeating",
                    type=CDLTypeEnum.REAL,
                    value=16.0,
                    quantity="Temperature",
                    unit="degC",
                    description="Mixed air temperature setpoint for heating",
                ),
                Parameter(
                    name="pBldgSetpoint",
                    type=CDLTypeEnum.REAL,
                    value=12.5,
                    quantity="Pressure",
                    unit="Pa",
                    description="Building static pressure setpoint",
                ),
                Parameter(
                    name="enableEconomizer",
                    type=CDLTypeEnum.BOOLEAN,
                    value=True,
                    description="Enable economizer operation",
                ),
                Parameter(
                    name="enablePressureReset",
                    type=CDLTypeEnum.BOOLEAN,
                    value=True,
                    description="Enable duct pressure reset logic",
                ),
            ],
            # Child blocks
            blocks=[
                mode_selector,
                pressure_reset,
                supply_fan,
                return_fan,
                economizer,
            ],
            # Internal connections
            connections=[
                # Mode selector connections
                Connection(
                    from_block="uOccupancySchedule",
                    from_output="uOccupancySchedule",
                    to_block="modeSelector",
                    to_input="uOccupied",
                    description="Pass occupancy schedule to mode selector",
                ),
                Connection(
                    from_block="TZoneAverage",
                    from_output="TZoneAverage",
                    to_block="modeSelector",
                    to_input="TZonAve",
                    description="Zone temperature to mode selector",
                ),
                Connection(
                    from_block="TZoneSetpoint",
                    from_output="TZoneSetpoint",
                    to_block="modeSelector",
                    to_input="TZonSet",
                    description="Zone setpoint to mode selector",
                ),
                Connection(
                    from_block="TOut",
                    from_output="TOut",
                    to_block="modeSelector",
                    to_input="TOut",
                    description="Outside temperature to mode selector",
                ),
                Connection(
                    from_block="timeOfDay",
                    from_output="timeOfDay",
                    to_block="modeSelector",
                    to_input="timeOfDay",
                    description="Time of day to mode selector",
                ),
                # Mode selector to other controllers
                Connection(
                    from_block="modeSelector",
                    from_output="yOccupied",
                    to_block="ductPressureReset",
                    to_input="uOccupied",
                    description="Occupied status to pressure reset",
                ),
                Connection(
                    from_block="modeSelector",
                    from_output="yOccupied",
                    to_block="supplyFanController",
                    to_input="uOccupied",
                    description="Occupied status to supply fan",
                ),
                # Pressure reset connections
                Connection(
                    from_block="uDamperPositions",
                    from_output="uDamperPositions",
                    to_block="ductPressureReset",
                    to_input="uDamperPositions",
                    description="VAV damper positions to pressure reset",
                ),
                Connection(
                    from_block="ductPressureReset",
                    from_output="pDuctSet",
                    to_block="supplyFanController",
                    to_input="pDuctSet",
                    description="Pressure setpoint to supply fan controller",
                ),
                # Supply fan connections
                Connection(
                    from_block="pDuct",
                    from_output="pDuct",
                    to_block="supplyFanController",
                    to_input="pDuct",
                    description="Duct pressure measurement to supply fan controller",
                ),
                # Return fan connections
                Connection(
                    from_block="VSupAir",
                    from_output="VSupAir",
                    to_block="returnFanController",
                    to_input="VSupAir",
                    description="Supply airflow to return fan controller",
                ),
                Connection(
                    from_block="pBldg",
                    from_output="pBldg",
                    to_block="returnFanController",
                    to_input="pBldg",
                    description="Building pressure to return fan controller",
                ),
                # Economizer connections
                Connection(
                    from_block="TMix",
                    from_output="TMix",
                    to_block="economizerController",
                    to_input="TMix",
                    description="Mixed air temperature to economizer",
                ),
                Connection(
                    from_block="TOut",
                    from_output="TOut",
                    to_block="economizerController",
                    to_input="TOut",
                    description="Outside air temperature to economizer",
                ),
                Connection(
                    from_block="TRet",
                    from_output="TRet",
                    to_block="economizerController",
                    to_input="TRet",
                    description="Return air temperature to economizer",
                ),
                Connection(
                    from_block="hOut",
                    from_output="hOut",
                    to_block="economizerController",
                    to_input="hOut",
                    description="Outside air enthalpy to economizer",
                ),
                Connection(
                    from_block="hRet",
                    from_output="hRet",
                    to_block="economizerController",
                    to_input="hRet",
                    description="Return air enthalpy to economizer",
                ),
                Connection(
                    from_block="VSupAir",
                    from_output="VSupAir",
                    to_block="economizerController",
                    to_input="VSupAir",
                    description="Supply airflow to economizer for min OA calculation",
                ),
                Connection(
                    from_block="uFreezeStat",
                    from_output="uFreezeStat",
                    to_block="economizerController",
                    to_input="uFreezeStat",
                    description="Freeze stat to economizer",
                ),
                # Output connections to system boundary
                Connection(
                    from_block="modeSelector",
                    from_output="yOccupied",
                    to_block="yOccupiedMode",
                    to_input="yOccupiedMode",
                    description="Occupied mode to system output",
                ),
                Connection(
                    from_block="modeSelector",
                    from_output="yMorningWarmup",
                    to_block="yMorningWarmupMode",
                    to_input="yMorningWarmupMode",
                    description="Morning warmup mode to system output",
                ),
                Connection(
                    from_block="modeSelector",
                    from_output="yNightSetback",
                    to_block="yNightSetbackMode",
                    to_input="yNightSetbackMode",
                    description="Night setback mode to system output",
                ),
                Connection(
                    from_block="modeSelector",
                    from_output="yUnoccupied",
                    to_block="yUnoccupiedMode",
                    to_input="yUnoccupiedMode",
                    description="Unoccupied mode to system output",
                ),
                Connection(
                    from_block="supplyFanController",
                    from_output="yFanSpeed",
                    to_block="ySupplyFanSpeed",
                    to_input="ySupplyFanSpeed",
                    description="Supply fan speed to system output",
                ),
                Connection(
                    from_block="supplyFanController",
                    from_output="yFanStatus",
                    to_block="ySupplyFanStatus",
                    to_input="ySupplyFanStatus",
                    description="Supply fan status to system output",
                ),
                Connection(
                    from_block="returnFanController",
                    from_output="yFanSpeed",
                    to_block="yReturnFanSpeed",
                    to_input="yReturnFanSpeed",
                    description="Return fan speed to system output",
                ),
                Connection(
                    from_block="economizerController",
                    from_output="yOutDamper",
                    to_block="yOutdoorDamper",
                    to_input="yOutdoorDamper",
                    description="Outdoor damper position to system output",
                ),
                Connection(
                    from_block="economizerController",
                    from_output="yRetDamper",
                    to_block="yReturnDamper",
                    to_input="yReturnDamper",
                    description="Return damper position to system output",
                ),
                Connection(
                    from_block="economizerController",
                    from_output="yRelDamper",
                    to_block="yReliefDamper",
                    to_input="yReliefDamper",
                    description="Relief damper position to system output",
                ),
                Connection(
                    from_block="economizerController",
                    from_output="yEconomizerActive",
                    to_block="yEconomizerActive",
                    to_input="yEconomizerActive",
                    description="Economizer status to system output",
                ),
                Connection(
                    from_block="ductPressureReset",
                    from_output="pDuctSet",
                    to_block="yDuctPressureSetpoint",
                    to_input="yDuctPressureSetpoint",
                    description="Duct pressure setpoint to system output",
                ),
                Connection(
                    from_block="supplyFanController",
                    from_output="yAlarm",
                    to_block="ySystemAlarm",
                    to_input="ySystemAlarm",
                    description="Fan alarm to system alarm output",
                ),
            ],
            **kwargs,
        )


class CoordinationLogic:
    """Coordination logic and operational notes for the AHU control system.

    This class documents the control coordination strategy and operational behavior.
    It does not contain executable code but serves as documentation.
    """

    @staticmethod
    def get_operational_notes() -> dict[str, str]:
        """Return operational notes for each control sequence.

        Returns:
            Dictionary mapping control function to operational notes
        """
        return {
            "mode_selection": """
            Mode Selector Finite State Machine:

            State Transitions:
            1. UNOCCUPIED -> MORNING_WARMUP
               - Trigger: Time approaches occupancy AND (TZone < TSetpoint - dTWarmup)
               - Action: Start fans at minimum speed, enable heating

            2. MORNING_WARMUP -> OCCUPIED
               - Trigger: (TZone >= TSetpoint) OR (Schedule = Occupied)
               - Action: Transition to normal occupied control

            3. OCCUPIED -> UNOCCUPIED
               - Trigger: Schedule = Unoccupied AND Time < Night Setback Start
               - Action: Reduce fan speed, disable economizer

            4. OCCUPIED -> NIGHT_SETBACK
               - Trigger: Schedule = Unoccupied AND Time >= Night Setback Start
               - Action: Enable setback temperatures, minimum ventilation

            5. ANY -> EMERGENCY
               - Trigger: Emergency stop signal OR critical alarm
               - Action: Controlled shutdown of all equipment
            """,
            "supply_fan_control": """
            Supply Fan PI Control Loop:

            Control Strategy:
            - PI controller maintains duct static pressure at setpoint
            - Proportional gain: 0.5 (tunable based on system characteristics)
            - Integral time: 60 seconds (eliminates steady-state error)
            - Anti-windup protection when output saturates

            Operating Constraints:
            - Occupied minimum speed: 30% (ensures adequate ventilation)
            - Unoccupied minimum speed: 15% (maintains building pressurization)
            - Maximum speed: 100%
            - Ramp rate limit: 10% per minute (prevents water hammer)

            Fan Proving:
            - 30 second delay after start command
            - Expects airflow or current feedback
            - Alarm if fan fails to prove
            """,
            "return_fan_tracking": """
            Return Fan Tracking Control:

            Base Strategy:
            - Return fan tracks supply fan at 90% of supply airflow
            - Allows positive building pressure (typically 12.5 Pa)

            Building Pressure Trim:
            - If pBldg > pBldgSet: Increase return fan speed
            - If pBldg < pBldgSet: Decrease return fan speed
            - Trim gain: 0.02 (prevents oscillation)

            Coordination:
            - Return fan never exceeds supply fan speed
            - Minimum speed: 30% when supply fan is running
            - Tracks supply fan ramp rates
            """,
            "economizer_control": """
            Economizer Control Strategy:

            Operating Modes:
            1. Minimum OA Mode (Economizer Disabled)
               - Conditions: TOut < -5°C OR TOut > 21°C OR hOut > 65 kJ/kg
               - OA damper: Minimum position (15% of supply flow)
               - Return damper: Maximum position
               - Relief damper: Tracks OA damper

            2. Economizer Mode (Modulating)
               - Conditions: -5°C < TOut < 21°C AND hOut < hRet - 5 kJ/kg
               - Control: PI on mixed air temperature (13°C setpoint cooling)
               - Dampers modulate to maintain TMix setpoint
               - OA damper range: Minimum OA to 100%

            3. 100% OA Mode (Maximum Free Cooling)
               - Conditions: TOut < TMixSet AND hOut << hRet
               - OA damper: 100% open
               - Return damper: 0% (fully closed)
               - Relief damper: 100% open

            Safety Overrides:
            - Freeze stat alarm: Close OA damper to minimum
            - High wind shutdown: Return to minimum OA
            - Low mixed air temp (<4°C): Reduce OA damper
            """,
            "pressure_reset": """
            Duct Static Pressure Reset (Trim & Respond):

            Trim Logic (Every 5 minutes):
            - Count zones with damper > 90% open
            - If count = 0 for 5 minutes: Decrease setpoint by 25 Pa
            - Limit: Do not trim below minimum setpoint (75 Pa)

            Respond Logic (Every 30 seconds):
            - If any zone damper > 90%: Increase setpoint by 25 Pa
            - Immediate response to ensure zone satisfaction
            - Limit: Do not respond above maximum setpoint (400 Pa)

            Mode-Based Initial Setpoints:
            - Occupied: 250 Pa (ensures adequate distribution)
            - Unoccupied: 100 Pa (energy savings)
            - Morning warmup: 300 Pa (rapid heat delivery)

            Benefits:
            - Reduces fan energy (can save 30-50% fan power)
            - Maintains zone comfort (all zones can be satisfied)
            - Automatic adaptation to load changes
            """,
            "system_coordination": """
            Overall System Coordination:

            Startup Sequence:
            1. Verify no alarms (freeze stat, smoke, etc.)
            2. Determine operating mode (occupied/unoccupied/warmup)
            3. Position dampers to minimum OA
            4. Start return fan to minimum speed
            5. Start supply fan to minimum speed
            6. Verify both fans prove (30 sec timeout)
            7. Enable economizer control
            8. Enable pressure reset logic
            9. Ramp fans to maintain pressure setpoint

            Normal Operation:
            - All control loops run concurrently
            - Mode selector updates every 60 seconds
            - Pressure reset updates every 5 minutes (trim) and 30 seconds (respond)
            - Fan controllers update every 1 second
            - Economizer updates every 1 second

            Shutdown Sequence:
            1. Disable economizer (return to minimum OA)
            2. Ramp supply fan to minimum speed
            3. Ramp return fan to minimum speed
            4. After 2 minute purge: Stop fans
            5. Close all dampers

            Emergency Shutdown:
            - Immediate: Stop supply fan
            - After 30 seconds: Stop return fan
            - Immediate: Close OA damper, open return damper
            """,
        }

    @staticmethod
    def get_tuning_parameters() -> dict[str, dict[str, Any]]:
        """Return recommended tuning parameters for different system types.

        Returns:
            Dictionary mapping system type to tuning parameters
        """
        return {
            "small_system": {
                "description": "Single-zone or small VAV (< 10,000 CFM)",
                "supply_fan": {"kp": 0.8, "Ti": 45.0, "spdMin": 0.4},
                "economizer": {"kp": 0.8, "Ti": 90.0},
                "pressure_reset": {"trimAmount": 15.0, "trimInterval": 180.0},
            },
            "medium_system": {
                "description": "Medium VAV system (10,000 - 30,000 CFM)",
                "supply_fan": {"kp": 0.5, "Ti": 60.0, "spdMin": 0.3},
                "economizer": {"kp": 0.5, "Ti": 120.0},
                "pressure_reset": {"trimAmount": 25.0, "trimInterval": 300.0},
            },
            "large_system": {
                "description": "Large VAV system (> 30,000 CFM)",
                "supply_fan": {"kp": 0.3, "Ti": 90.0, "spdMin": 0.25},
                "economizer": {"kp": 0.3, "Ti": 180.0},
                "pressure_reset": {"trimAmount": 35.0, "trimInterval": 360.0},
            },
            "high_performance": {
                "description": "High-performance system (ASHRAE Guideline 36)",
                "supply_fan": {"kp": 0.4, "Ti": 60.0, "spdMin": 0.3},
                "economizer": {"kp": 0.4, "Ti": 120.0},
                "pressure_reset": {
                    "trimAmount": 25.0,
                    "trimInterval": 300.0,
                    "damperThreshold": 0.85,
                },
            },
        }
