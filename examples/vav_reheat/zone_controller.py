"""VAV box controller with reheat for zone-level control.

This module implements ASHRAE Guideline 36-2006 sequences for VAV terminal units
with reheat. The controller manages damper position for cooling and reheat valve
position for heating based on zone temperature and setpoints.

Control Sequence:
1. When room temp > cooling setpoint + deadband:
   - Increase damper position to increase cooling
   - Reheat valve fully closed

2. When cooling setpoint - deadband < room temp < cooling setpoint + deadband:
   - Maintain minimum airflow
   - Modulate reheat if needed

3. When room temp < heating setpoint:
   - Maintain minimum airflow
   - Modulate reheat valve to maintain heating setpoint
"""

from typing import Tuple

from python_cdl.models.blocks import CompositeBlock
from python_cdl.models.connectors import RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum

from .zone_models import ZoneConfig, ZoneState


class VAVBoxController:
    """VAV box controller with reheat capability.

    Implements ASHRAE 2006 sequences for VAV terminal unit control with:
    - PI control for damper position based on cooling demand
    - Minimum airflow enforcement
    - Sequenced reheat control when in heating mode
    - Temperature deadband operation
    """

    def __init__(self, config: ZoneConfig):
        """Initialize VAV box controller.

        Args:
            config: Zone configuration parameters
        """
        self.config = config
        self.damper_integral = 0.0
        self.reheat_integral = 0.0
        self.last_error_damper = 0.0
        self.last_error_reheat = 0.0

    def reset(self):
        """Reset controller integral terms."""
        self.damper_integral = 0.0
        self.reheat_integral = 0.0
        self.last_error_damper = 0.0
        self.last_error_reheat = 0.0

    def compute_control(
        self,
        room_temp: float,
        supply_air_temp: float,
        dt: float = 1.0,
    ) -> Tuple[float, float]:
        """Compute damper and reheat valve positions.

        Args:
            room_temp: Current room temperature in degC
            supply_air_temp: Supply air temperature in degC
            dt: Time step in seconds (default: 1.0)

        Returns:
            Tuple of (damper_position, reheat_valve_position) both in range [0, 1]
        """
        # Calculate temperature errors
        cooling_error = room_temp - self.config.cooling_setpoint
        heating_error = self.config.heating_setpoint - room_temp

        # Determine operating mode based on temperature and deadband
        in_deadband = (
            abs(room_temp - self.config.cooling_setpoint) <= self.config.deadband
            and room_temp >= self.config.heating_setpoint
        )

        # Mode 1: Cooling mode (room temp > cooling setpoint + deadband)
        if cooling_error > self.config.deadband:
            damper_position = self._compute_cooling_damper(cooling_error, dt)
            reheat_valve_position = 0.0
            self.reheat_integral = 0.0  # Reset reheat integral

        # Mode 2: Deadband mode (between heating and cooling setpoints)
        elif in_deadband:
            # Maintain minimum airflow
            damper_position = self.config.min_damper_position
            # Small reheat if slightly below cooling setpoint
            if room_temp < self.config.cooling_setpoint - 0.5:
                reheat_valve_position = self._compute_reheat_valve(heating_error, dt)
            else:
                reheat_valve_position = 0.0
            self.damper_integral = 0.0  # Reset damper integral

        # Mode 3: Heating mode (room temp < heating setpoint)
        else:
            # Maintain minimum airflow
            damper_position = self.config.min_damper_position
            reheat_valve_position = self._compute_reheat_valve(heating_error, dt)
            self.damper_integral = 0.0  # Reset damper integral

        return damper_position, reheat_valve_position

    def _compute_cooling_damper(self, error: float, dt: float) -> float:
        """Compute damper position for cooling mode using PI control.

        Args:
            error: Temperature error (room_temp - cooling_setpoint)
            dt: Time step in seconds

        Returns:
            Damper position in range [min_damper_position, 1.0]
        """
        # PI control for damper
        proportional = self.config.kp_damper * error
        self.damper_integral += self.config.ki_damper * error * dt

        # Anti-windup: limit integral term
        max_integral = 1.0 - self.config.min_damper_position
        self.damper_integral = max(-max_integral, min(max_integral, self.damper_integral))

        # Calculate damper position
        damper_position = self.config.min_damper_position + proportional + self.damper_integral

        # Clamp to valid range
        damper_position = max(
            self.config.min_damper_position,
            min(self.config.max_damper_position, damper_position),
        )

        return damper_position

    def _compute_reheat_valve(self, error: float, dt: float) -> float:
        """Compute reheat valve position for heating mode using PI control.

        Args:
            error: Temperature error (heating_setpoint - room_temp)
            dt: Time step in seconds

        Returns:
            Reheat valve position in range [0.0, 1.0]
        """
        # PI control for reheat valve
        proportional = self.config.kp_reheat * error
        self.reheat_integral += self.config.ki_reheat * error * dt

        # Anti-windup: limit integral term
        self.reheat_integral = max(0.0, min(1.0, self.reheat_integral))

        # Calculate valve position
        valve_position = proportional + self.reheat_integral

        # Clamp to valid range [0, 1]
        valve_position = max(0.0, min(1.0, valve_position))

        return valve_position

    def compute_airflow(self, damper_position: float, supply_pressure: float = 1.0) -> float:
        """Compute airflow based on damper position.

        Simplified linear relationship between damper position and airflow.
        In real implementation, this would use actual damper characteristics.

        Args:
            damper_position: Damper position in range [0, 1]
            supply_pressure: Supply air pressure (normalized, default: 1.0)

        Returns:
            Airflow rate in m3/s
        """
        # Linear interpolation between min and max airflow
        airflow_range = self.config.max_airflow - self.config.min_airflow
        airflow = self.config.min_airflow + airflow_range * damper_position * supply_pressure

        return max(self.config.min_airflow, min(self.config.max_airflow, airflow))

    def update_state(
        self,
        state: ZoneState,
        dt: float = 1.0,
        supply_pressure: float = 1.0,
    ) -> ZoneState:
        """Update zone state based on control computations.

        Args:
            state: Current zone state
            dt: Time step in seconds
            supply_pressure: Supply air pressure (normalized)

        Returns:
            Updated zone state
        """
        # Compute control outputs
        damper_pos, reheat_pos = self.compute_control(
            room_temp=state.room_temp,
            supply_air_temp=state.supply_air_temp,
            dt=dt,
        )

        # Compute airflow
        airflow = self.compute_airflow(damper_pos, supply_pressure)

        # Calculate demand signals
        cooling_error = max(0.0, state.room_temp - self.config.cooling_setpoint)
        heating_error = max(0.0, self.config.heating_setpoint - state.room_temp)
        cooling_demand = min(1.0, cooling_error / 2.0)  # Normalize to [0, 1]
        heating_demand = min(1.0, heating_error / 2.0)  # Normalize to [0, 1]

        # Update state
        state.damper_position = damper_pos
        state.reheat_valve_position = reheat_pos
        state.airflow = airflow
        state.cooling_demand = cooling_demand
        state.heating_demand = heating_demand

        return state


def create_vav_controller_block(zone_config: ZoneConfig) -> CompositeBlock:
    """Create a CDL CompositeBlock representation of the VAV controller.

    This function creates a CDL block structure that represents the VAV
    controller logic using the python-cdl framework.

    Args:
        zone_config: Zone configuration parameters

    Returns:
        CompositeBlock representing the VAV controller
    """
    # Create the composite block
    block = CompositeBlock(
        name=f"VAVController_{zone_config.zone_id}",
        block_type="VAVBoxController",
        description="VAV box controller with reheat for zone-level control",
    )

    # Define input connectors
    block.inputs = [
        RealInput(
            name="room_temp",
            type=CDLTypeEnum.REAL,
            quantity="ThermodynamicTemperature",
            unit="degC",
            description="Room temperature measurement",
        ),
        RealInput(
            name="supply_air_temp",
            type=CDLTypeEnum.REAL,
            quantity="ThermodynamicTemperature",
            unit="degC",
            description="Supply air temperature",
        ),
        RealInput(
            name="supply_pressure",
            type=CDLTypeEnum.REAL,
            quantity="Pressure",
            unit="Pa",
            description="Supply air pressure (normalized)",
            min=0.0,
            max=2.0,
        ),
    ]

    # Define output connectors
    block.outputs = [
        RealOutput(
            name="damper_position",
            type=CDLTypeEnum.REAL,
            quantity="Dimensionless",
            unit="1",
            description="VAV damper position command",
            min=0.0,
            max=1.0,
        ),
        RealOutput(
            name="reheat_valve_position",
            type=CDLTypeEnum.REAL,
            quantity="Dimensionless",
            unit="1",
            description="Reheat valve position command",
            min=0.0,
            max=1.0,
        ),
        RealOutput(
            name="airflow",
            type=CDLTypeEnum.REAL,
            quantity="VolumeFlowRate",
            unit="m3/s",
            description="Zone airflow rate",
            min=0.0,
        ),
        RealOutput(
            name="cooling_demand",
            type=CDLTypeEnum.REAL,
            quantity="Dimensionless",
            unit="1",
            description="Cooling demand signal",
            min=0.0,
            max=1.0,
        ),
        RealOutput(
            name="heating_demand",
            type=CDLTypeEnum.REAL,
            quantity="Dimensionless",
            unit="1",
            description="Heating demand signal",
            min=0.0,
            max=1.0,
        ),
    ]

    # Define parameters from zone configuration
    block.parameters = [
        Parameter(
            name="cooling_setpoint",
            type=CDLTypeEnum.REAL,
            value=zone_config.cooling_setpoint,
            quantity="ThermodynamicTemperature",
            unit="degC",
            description="Cooling temperature setpoint",
        ),
        Parameter(
            name="heating_setpoint",
            type=CDLTypeEnum.REAL,
            value=zone_config.heating_setpoint,
            quantity="ThermodynamicTemperature",
            unit="degC",
            description="Heating temperature setpoint",
        ),
        Parameter(
            name="min_airflow",
            type=CDLTypeEnum.REAL,
            value=zone_config.min_airflow,
            quantity="VolumeFlowRate",
            unit="m3/s",
            description="Minimum airflow rate",
        ),
        Parameter(
            name="max_airflow",
            type=CDLTypeEnum.REAL,
            value=zone_config.max_airflow,
            quantity="VolumeFlowRate",
            unit="m3/s",
            description="Maximum airflow rate",
        ),
        Parameter(
            name="min_damper_position",
            type=CDLTypeEnum.REAL,
            value=zone_config.min_damper_position,
            quantity="Dimensionless",
            unit="1",
            description="Minimum damper position",
        ),
        Parameter(
            name="kp_damper",
            type=CDLTypeEnum.REAL,
            value=zone_config.kp_damper,
            quantity="Dimensionless",
            unit="1",
            description="Proportional gain for damper control",
        ),
        Parameter(
            name="ki_damper",
            type=CDLTypeEnum.REAL,
            value=zone_config.ki_damper,
            quantity="Dimensionless",
            unit="1",
            description="Integral gain for damper control",
        ),
        Parameter(
            name="kp_reheat",
            type=CDLTypeEnum.REAL,
            value=zone_config.kp_reheat,
            quantity="Dimensionless",
            unit="1",
            description="Proportional gain for reheat control",
        ),
        Parameter(
            name="ki_reheat",
            type=CDLTypeEnum.REAL,
            value=zone_config.ki_reheat,
            quantity="Dimensionless",
            unit="1",
            description="Integral gain for reheat control",
        ),
    ]

    return block
