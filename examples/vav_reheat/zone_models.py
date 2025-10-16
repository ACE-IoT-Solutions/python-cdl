"""Zone configuration models for VAV reheat system.

This module defines the zone-specific parameters and configurations
for a 5-zone VAV system with reheat capability.
"""

from dataclasses import dataclass
from enum import Enum


class ZoneType(str, Enum):
    """Zone types in the building."""

    CORRIDOR = "corridor"
    SOUTH = "south"
    NORTH = "north"
    EAST = "east"
    WEST = "west"


@dataclass
class ZoneConfig:
    """Configuration parameters for a single VAV zone.

    Attributes:
        zone_id: Unique identifier for the zone
        zone_type: Type of zone (corridor, perimeter, etc.)
        cooling_setpoint: Cooling temperature setpoint in degC
        heating_setpoint: Heating temperature setpoint in degC
        min_airflow: Minimum airflow rate in m3/s
        max_airflow: Maximum airflow rate in m3/s
        min_damper_position: Minimum damper position (0.0-1.0)
        max_damper_position: Maximum damper position (0.0-1.0)
        deadband: Temperature deadband in degC
        kp_damper: Proportional gain for damper PI controller
        ki_damper: Integral gain for damper PI controller
        kp_reheat: Proportional gain for reheat PI controller
        ki_reheat: Integral gain for reheat PI controller
    """

    zone_id: str
    zone_type: ZoneType
    cooling_setpoint: float  # degC
    heating_setpoint: float  # degC
    min_airflow: float  # m3/s
    max_airflow: float  # m3/s
    min_damper_position: float = 0.1  # fraction (0-1)
    max_damper_position: float = 1.0  # fraction (0-1)
    deadband: float = 1.0  # degC
    kp_damper: float = 0.5  # Proportional gain for damper control
    ki_damper: float = 0.1  # Integral gain for damper control
    kp_reheat: float = 0.3  # Proportional gain for reheat control
    ki_reheat: float = 0.05  # Integral gain for reheat control


# Default zone configurations based on ASHRAE 2006 sequences
DEFAULT_ZONE_CONFIGS = {
    ZoneType.CORRIDOR: ZoneConfig(
        zone_id="zone_corridor",
        zone_type=ZoneType.CORRIDOR,
        cooling_setpoint=24.0,
        heating_setpoint=21.0,
        min_airflow=0.15,  # Lower min flow for interior zone
        max_airflow=0.6,
        min_damper_position=0.15,
        deadband=1.0,
        kp_damper=0.5,
        ki_damper=0.1,
        kp_reheat=0.3,
        ki_reheat=0.05,
    ),
    ZoneType.SOUTH: ZoneConfig(
        zone_id="zone_south",
        zone_type=ZoneType.SOUTH,
        cooling_setpoint=23.0,  # Lower cooling setpoint for high solar gain
        heating_setpoint=21.0,
        min_airflow=0.2,
        max_airflow=1.0,
        min_damper_position=0.15,
        deadband=1.0,
        kp_damper=0.6,  # Higher gain for perimeter zone
        ki_damper=0.12,
        kp_reheat=0.35,
        ki_reheat=0.06,
    ),
    ZoneType.NORTH: ZoneConfig(
        zone_id="zone_north",
        zone_type=ZoneType.NORTH,
        cooling_setpoint=24.0,
        heating_setpoint=21.0,
        min_airflow=0.2,
        max_airflow=0.9,
        min_damper_position=0.15,
        deadband=1.0,
        kp_damper=0.55,
        ki_damper=0.11,
        kp_reheat=0.35,
        ki_reheat=0.06,
    ),
    ZoneType.EAST: ZoneConfig(
        zone_id="zone_east",
        zone_type=ZoneType.EAST,
        cooling_setpoint=23.5,  # Morning sun exposure
        heating_setpoint=21.0,
        min_airflow=0.2,
        max_airflow=0.95,
        min_damper_position=0.15,
        deadband=1.0,
        kp_damper=0.6,
        ki_damper=0.12,
        kp_reheat=0.35,
        ki_reheat=0.06,
    ),
    ZoneType.WEST: ZoneConfig(
        zone_id="zone_west",
        zone_type=ZoneType.WEST,
        cooling_setpoint=23.5,  # Afternoon sun exposure
        heating_setpoint=21.0,
        min_airflow=0.2,
        max_airflow=0.95,
        min_damper_position=0.15,
        deadband=1.0,
        kp_damper=0.6,
        ki_damper=0.12,
        kp_reheat=0.35,
        ki_reheat=0.06,
    ),
}


@dataclass
class ZoneState:
    """Runtime state for a VAV zone.

    Attributes:
        room_temp: Current room temperature in degC
        supply_air_temp: Supply air temperature in degC
        damper_position: Current damper position (0.0-1.0)
        reheat_valve_position: Current reheat valve position (0.0-1.0)
        airflow: Current airflow rate in m3/s
        cooling_demand: Cooling demand signal (0.0-1.0)
        heating_demand: Heating demand signal (0.0-1.0)
    """

    room_temp: float
    supply_air_temp: float
    damper_position: float = 0.0
    reheat_valve_position: float = 0.0
    airflow: float = 0.0
    cooling_demand: float = 0.0
    heating_demand: float = 0.0


def get_zone_config(zone_type: ZoneType) -> ZoneConfig:
    """Get the default configuration for a zone type.

    Args:
        zone_type: Type of zone

    Returns:
        Zone configuration with default parameters
    """
    return DEFAULT_ZONE_CONFIGS[zone_type]


def create_custom_zone_config(
    zone_id: str,
    zone_type: ZoneType,
    cooling_setpoint: float,
    heating_setpoint: float,
    min_airflow: float,
    max_airflow: float,
    **kwargs,
) -> ZoneConfig:
    """Create a custom zone configuration.

    Args:
        zone_id: Unique identifier for the zone
        zone_type: Type of zone
        cooling_setpoint: Cooling temperature setpoint in degC
        heating_setpoint: Heating temperature setpoint in degC
        min_airflow: Minimum airflow rate in m3/s
        max_airflow: Maximum airflow rate in m3/s
        **kwargs: Additional configuration parameters

    Returns:
        Custom zone configuration
    """
    return ZoneConfig(
        zone_id=zone_id,
        zone_type=zone_type,
        cooling_setpoint=cooling_setpoint,
        heating_setpoint=heating_setpoint,
        min_airflow=min_airflow,
        max_airflow=max_airflow,
        **kwargs,
    )
