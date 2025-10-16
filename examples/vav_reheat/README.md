# VAV Reheat System - Complete Building Control

This example implements ASHRAE Guideline 36 High Performance Sequences of Operation for a complete Variable Air Volume (VAV) reheat system including both zone-level and system-level controls.

## Overview

The VAV reheat system provides comprehensive building control through:

### Zone-Level Control
- **Modulating VAV damper** for cooling via increased airflow
- **Hot water reheat coil** for heating when cooling is insufficient
- **Minimum airflow enforcement** for ventilation requirements
- **PI control loops** for both damper and reheat valve

### System-Level Control (AHU)
- **Operating mode selection** via finite state machine
- **Supply fan speed control** with duct static pressure maintenance
- **Return fan tracking** with building pressure control
- **Economizer control** with differential enthalpy and mixed air temperature control
- **Duct static pressure reset** using trim and respond logic

## Files

### Zone-Level Control (Terminal Units)

- **`zone_models.py`** - Zone configuration dataclasses and parameters
  - `ZoneConfig`: Zone-specific parameters (setpoints, flow rates, control gains)
  - `ZoneState`: Runtime state variables (temps, positions, demands)
  - `ZoneType`: Enumeration of 5 zone types
  - Default configurations for all zones

- **`zone_controller.py`** - VAV box controller implementation
  - `VAVBoxController`: Main controller class with PI control
  - Three operating modes: Cooling, Deadband, Heating
  - Control output computation for damper and reheat
  - CDL block generation function

### System-Level Control (AHU)

- **`ahu_controller.py`** - Central AHU control sequences
  - `ModeSelector`: Finite state machine for operating mode selection
  - `SupplyFanController`: VFD speed control with PI for static pressure
  - `ReturnFanController`: Airflow tracking with building pressure compensation
  - `EconomizerController`: Damper modulation for free cooling and mixed air control
  - `DuctPressureReset`: Trim and respond logic for pressure setpoint optimization
  - `PIController`: Base PI controller implementation

- **`control_sequences.py`** - Integrated AHU control system
  - `AHUControlSystem`: Complete coordinated control system
  - `CoordinationLogic`: Documentation of control coordination and tuning parameters
  - Connection logic between all controllers
  - System-level parameter definitions

### Examples and Demonstrations

- **`example_usage.py`** - Demonstration script
  - 5-zone building simulation
  - Control mode demonstrations
  - CDL block generation

### Generated Outputs

- **`{zone}_controller.json`** - CDL block representations for each zone
  - Inputs: room_temp, supply_air_temp, supply_pressure
  - Outputs: damper_position, reheat_valve_position, airflow, cooling_demand, heating_demand
  - Parameters: setpoints, flow limits, control gains

## Building Zones

### Zone Configurations

| Zone     | Type      | Cooling SP | Heating SP | Min Flow | Max Flow | Notes                    |
|----------|-----------|------------|------------|----------|----------|--------------------------|
| Corridor | Interior  | 24.0°C     | 21.0°C     | 0.15 m³/s| 0.6 m³/s | Lower flow requirements  |
| South    | Perimeter | 23.0°C     | 21.0°C     | 0.2 m³/s | 1.0 m³/s | High solar gain          |
| North    | Perimeter | 24.0°C     | 21.0°C     | 0.2 m³/s | 0.9 m³/s | Minimal solar exposure   |
| East     | Perimeter | 23.5°C     | 21.0°C     | 0.2 m³/s | 0.95 m³/s| Morning sun exposure     |
| West     | Perimeter | 23.5°C     | 21.0°C     | 0.2 m³/s | 0.95 m³/s| Afternoon sun exposure   |

## AHU Control Sequences (ASHRAE Guideline 36)

### 1. Mode Selection (Finite State Machine)

The mode selector determines the current operating mode based on occupancy schedule, zone conditions, and time of day.

**Operating Modes:**
- **Occupied**: Normal occupied period with full ventilation and tight temperature control
- **Unoccupied**: Minimal ventilation, relaxed temperature control
- **Morning Warmup**: Pre-occupancy heating to bring zones to setpoint
- **Night Setback**: Extended unoccupied period with setback temperatures

**State Transitions:**
```
UNOCCUPIED → MORNING_WARMUP: Time < occupancy start - 1h AND TZone < TSetpoint - 2K
MORNING_WARMUP → OCCUPIED: TZone >= TSetpoint OR occupancy schedule active
OCCUPIED → UNOCCUPIED: Occupancy schedule inactive AND time < 22:00
OCCUPIED → NIGHT_SETBACK: Occupancy schedule inactive AND time >= 22:00
```

### 2. Supply Fan Control

PI controller maintains duct static pressure at setpoint (adjusted by pressure reset logic).

**Parameters:**
- Proportional gain: 0.5 (tunable)
- Integral time: 60 seconds
- Occupied minimum speed: 30%
- Unoccupied minimum speed: 15%

**Features:**
- Anti-windup protection
- Fan proving with 30-second timeout
- Alarm generation on failure to prove

### 3. Return Fan Tracking

Return fan tracks supply fan airflow with building pressure compensation.

**Control Strategy:**
```
VReturnFan = 0.9 × VSupplyFan + kPressure × (pBldgSet - pBldg)
```

**Parameters:**
- Tracking gain: 0.9 (return airflow as fraction of supply)
- Pressure gain: 0.02
- Minimum speed: 30%

### 4. Economizer Control

Modulates outdoor, return, and relief dampers for free cooling and mixed air temperature control.

**Operating Modes:**

**Minimum OA Mode:**
- Conditions: TOut < -5°C OR TOut > 21°C OR hOut > 65 kJ/kg
- OA damper: Minimum position (15% of supply flow)
- Return damper: Maximum position

**Economizer Mode:**
- Conditions: -5°C < TOut < 21°C AND hOut < hRet - 5 kJ/kg
- PI control on mixed air temperature (13°C setpoint)
- Dampers modulate between minimum OA and 100% OA

**100% OA Mode:**
- Conditions: TOut < TMixSet AND hOut << hRet
- Maximum free cooling
- OA damper: 100% open

**Safety Overrides:**
- Freeze stat alarm: Return to minimum OA
- Low mixed air temp (<4°C): Reduce OA damper

### 5. Duct Static Pressure Reset

Trim and respond logic optimizes duct static pressure setpoint based on zone demand.

**Trim Logic (Every 5 minutes):**
- If all VAV dampers < 90% for 5 minutes: Decrease setpoint by 25 Pa
- Minimum setpoint: 75 Pa

**Respond Logic (Every 30 seconds):**
- If any VAV damper > 90%: Increase setpoint by 25 Pa immediately
- Maximum setpoint: 400 Pa

**Mode-Based Setpoints:**
- Occupied: 250 Pa initial
- Unoccupied: 100 Pa initial
- Morning warmup: 300 Pa initial

**Benefits:**
- 30-50% fan energy savings
- Maintains zone comfort
- Automatic adaptation to load changes

## Zone Control Sequence (ASHRAE Guideline 36)

### Mode 1: Cooling Mode
**Trigger**: `room_temp > cooling_setpoint + deadband`

- Increase damper position to increase cooling airflow
- Reheat valve fully closed (0%)
- PI control modulates damper from min position to 100%

### Mode 2: Deadband Mode
**Trigger**: `heating_setpoint < room_temp < cooling_setpoint + deadband`

- Maintain minimum airflow for ventilation
- Damper at minimum position (typically 15%)
- Minimal reheat if temperature drops below cooling setpoint - 0.5°C

### Mode 3: Heating Mode
**Trigger**: `room_temp < heating_setpoint`

- Maintain minimum airflow
- Damper at minimum position
- Modulate reheat valve to maintain heating setpoint
- PI control for reheat valve position (0-100%)

## Control Algorithm

### Damper Control (Cooling)
```python
# PI controller for damper position
error = room_temp - cooling_setpoint
proportional = kp_damper * error
integral += ki_damper * error * dt

damper_position = min_damper_position + proportional + integral
damper_position = clamp(damper_position, min_damper_position, 1.0)
```

### Reheat Control (Heating)
```python
# PI controller for reheat valve
error = heating_setpoint - room_temp
proportional = kp_reheat * error
integral += ki_reheat * error * dt

reheat_position = proportional + integral
reheat_position = clamp(reheat_position, 0.0, 1.0)
```

### Anti-Windup Protection
- Integral terms limited to prevent excessive accumulation
- Integrator reset when switching between modes
- Output clamping to physical limits [0, 1]

## Usage

### AHU Control System Usage

```python
from control_sequences import AHUControlSystem, CoordinationLogic

# Create integrated AHU control system
ahu_system = AHUControlSystem(name="Building_AHU_1")

# Access coordination documentation
operational_notes = CoordinationLogic.get_operational_notes()
tuning_params = CoordinationLogic.get_tuning_parameters()

# Get tuning parameters for your system type
medium_system_params = tuning_params["medium_system"]
print(f"Supply Fan Kp: {medium_system_params['supply_fan']['kp']}")

# Access individual controllers
print(f"System has {len(ahu_system.blocks)} control blocks:")
for block in ahu_system.blocks:
    print(f"  - {block.name}: {block.block_type}")

# Export to CDL JSON
import json
ahu_dict = ahu_system.model_dump()
with open("ahu_control_system.json", "w") as f:
    json.dump(ahu_dict, f, indent=2)
```

### Individual AHU Controller Usage

```python
from ahu_controller import (
    ModeSelector,
    SupplyFanController,
    EconomizerController,
    DuctPressureReset
)

# Create mode selector
mode_selector = ModeSelector(name="AHU_ModeSelector")

# Configure parameters
mode_selector.parameters[0].value = 1.5  # tWarmupStart (hours)
mode_selector.parameters[1].value = 2.5  # dTWarmup (K)

# Create supply fan controller
supply_fan = SupplyFanController(name="AHU_SupplyFan")
supply_fan.get_parameter("kp").value = 0.6  # Adjust proportional gain
supply_fan.get_parameter("spdMin").value = 0.35  # Adjust minimum speed

# Create economizer controller
economizer = EconomizerController(name="AHU_Economizer")

# Configure economizer limits
economizer.get_parameter("TOutLowLim").value = -7.0  # Lower limit for cold climate
economizer.get_parameter("TOutHighLim").value = 24.0  # Upper limit

# Create pressure reset controller
pressure_reset = DuctPressureReset(name="AHU_PressureReset")

# Configure trim and respond parameters
pressure_reset.get_parameter("trimAmount").value = 30.0  # More aggressive trimming
pressure_reset.get_parameter("damperThreshold").value = 0.85  # Respond earlier
```

### Zone Controller Usage

```python
from zone_controller import VAVBoxController
from zone_models import get_zone_config, ZoneType, ZoneState

# Get configuration for south zone
config = get_zone_config(ZoneType.SOUTH)

# Create controller
controller = VAVBoxController(config)

# Initialize zone state
state = ZoneState(
    room_temp=26.0,      # Current temperature
    supply_air_temp=13.0  # Supply air temperature
)

# Compute control outputs (1 second timestep)
state = controller.update_state(state, dt=1.0)

# Access control outputs
print(f"Damper Position: {state.damper_position:.2%}")
print(f"Reheat Valve: {state.reheat_valve_position:.2%}")
print(f"Airflow: {state.airflow:.3f} m³/s")
```

### Running the Example

```bash
cd examples/vav_reheat
python example_usage.py
```

This will:
1. Initialize controllers for all 5 zones
2. Simulate 10 seconds of operation
3. Display control outputs and zone states
4. Generate CDL block JSON files
5. Demonstrate different control modes

### Custom Zone Configuration

```python
from zone_models import create_custom_zone_config, ZoneType

# Create custom configuration
custom_config = create_custom_zone_config(
    zone_id="custom_zone_1",
    zone_type=ZoneType.SOUTH,
    cooling_setpoint=22.0,
    heating_setpoint=20.0,
    min_airflow=0.25,
    max_airflow=1.2,
    kp_damper=0.7,
    ki_damper=0.15
)

controller = VAVBoxController(custom_config)
```

## CDL Block Integration

The implementation includes CDL block generation:

```python
from zone_controller import create_vav_controller_block
from zone_models import get_zone_config, ZoneType

# Generate CDL block representation
config = get_zone_config(ZoneType.SOUTH)
block = create_vav_controller_block(config)

# Export to JSON
block_dict = block.model_dump()
```

Each CDL block includes:
- **3 Inputs**: room_temp, supply_air_temp, supply_pressure
- **5 Outputs**: damper_position, reheat_valve_position, airflow, cooling_demand, heating_demand
- **9 Parameters**: setpoints, flow limits, control gains

## Tuning Guidelines

### Damper Control Tuning
- **kp_damper**: 0.5-0.7 (perimeter zones higher)
- **ki_damper**: 0.1-0.15 (perimeter zones higher)
- Higher gains for zones with high disturbances (solar load)

### Reheat Control Tuning
- **kp_reheat**: 0.3-0.4
- **ki_reheat**: 0.05-0.08
- Conservative tuning to prevent oscillation

### Deadband
- Typical: 1.0°C (adjustable per zone)
- Larger deadband reduces hunting behavior
- Smaller deadband provides tighter temperature control

## System Integration

### Complete Control Hierarchy

The VAV reheat system uses a hierarchical control architecture:

```
Building Level
└── AHU Control System
    ├── Mode Selector ─────────┐
    ├── Supply Fan Controller   ├─→ Coordinated Operation
    ├── Return Fan Controller   │
    ├── Economizer Controller   │
    └── Pressure Reset ─────────┘
        │
        ├─→ Supply Air to Zones
        │
    Zone Level (5 zones)
    ├── Corridor VAV Controller
    ├── South Zone VAV Controller
    ├── North Zone VAV Controller
    ├── East Zone VAV Controller
    └── West Zone VAV Controller
```

### Control Flow

1. **Mode Selector** determines system operating mode (Occupied/Unoccupied/Warmup/Setback)
2. **Economizer** modulates dampers to maintain mixed air temperature (13°C cooling setpoint)
3. **Supply Fan** maintains duct static pressure at setpoint from pressure reset
4. **Pressure Reset** adjusts setpoint based on zone VAV damper positions
5. **Return Fan** tracks supply fan with building pressure compensation
6. **Zone Controllers** modulate VAV dampers based on zone cooling demand
7. **Reheat Coils** provide individual zone heating when needed

### Data Flow

**AHU to Zones:**
- Supply air temperature (typically 13-15°C for cooling)
- Duct static pressure (75-400 Pa)
- Operating mode (occupied/unoccupied)

**Zones to AHU:**
- VAV damper positions (for pressure reset logic)
- Zone cooling demands (for supply air temp reset - future enhancement)
- Zone heating demands (for morning warmup decision)

**External Inputs:**
- Occupancy schedule
- Outside air temperature and enthalpy
- Building pressure
- Time of day

## Key Features

### Zone-Level Control
- ✅ ASHRAE Guideline 36 compliant sequences
- ✅ PI control with anti-windup protection
- ✅ Three-mode operation (cooling/deadband/heating)
- ✅ Minimum airflow enforcement
- ✅ Zone-specific tuning parameters
- ✅ Demand signal calculation for optimization

### System-Level Control
- ✅ Finite state machine for mode selection
- ✅ PI-based fan speed control with static pressure maintenance
- ✅ Return fan tracking with building pressure compensation
- ✅ Differential enthalpy economizer with mixed air control
- ✅ Trim and respond pressure reset (30-50% energy savings)
- ✅ Coordinated startup and shutdown sequences
- ✅ Safety interlocks and alarm generation

### Integration Features
- ✅ Complete CDL block representations for all controllers
- ✅ Hierarchical control architecture
- ✅ Configurable for different building types and climates
- ✅ Documented coordination logic and tuning guidelines
- ✅ Based on ASHRAE Guideline 36 High Performance Sequences

## Testing

The example includes comprehensive demonstrations:

1. **Multi-zone simulation** - Shows interaction between 5 zones with different loads
2. **Control mode tests** - Validates cooling, deadband, and heating modes
3. **State tracking** - Monitors all control variables over time
4. **CDL generation** - Produces valid CDL block representations

## References

- ASHRAE Guideline 36-2021: High Performance Sequences of Operation for HVAC Systems
- ASHRAE Standard 90.1: Energy Standard for Buildings
- Control Description Language (CDL) specification
- Python CDL library documentation

## Implementation Summary

This example demonstrates a production-ready implementation of:

### Implemented Controllers (9 total)

**Zone Level (1):**
- VAVBoxController with PI control for damper and reheat

**System Level (8):**
1. ModeSelector - Finite state machine with 4 operating modes
2. SupplyFanController - PI control for duct static pressure
3. ReturnFanController - Airflow tracking with building pressure trim
4. EconomizerController - Three-mode damper control with enthalpy logic
5. DuctPressureReset - Trim and respond optimization
6. PIController - Reusable PI control block
7. AHUControlSystem - Integrated coordinated control system
8. CoordinationLogic - Documentation and tuning parameters class

### Control Parameters

**Total configurable parameters across all controllers: 50+**
- Mode timing and thresholds
- PI gains and time constants
- Pressure limits and setpoints
- Temperature limits and setpoints
- Economizer enable/disable conditions
- Fan speed limits
- Trim and respond timing

### Lines of Code
- `ahu_controller.py`: ~600 lines
- `control_sequences.py`: ~700 lines
- `zone_controller.py`: ~350 lines
- `zone_models.py`: ~200 lines
- **Total: ~1850 lines of production control logic**

## Next Steps and Extensions

Potential enhancements for production deployment:

1. **Runtime Simulation**
   - Add execution context for time-based simulation
   - Implement block executor for control loop evaluation
   - Create thermal zone models for closed-loop testing

2. **Advanced Features**
   - Supply air temperature reset based on zone demands
   - Demand-controlled ventilation (CO₂-based)
   - Optimal start/stop timing algorithms
   - Fault detection and diagnostics

3. **Integration**
   - BACnet/Modbus protocol adapters
   - Building management system (BMS) integration
   - Historical data logging and trending
   - Energy monitoring and reporting

4. **Additional Controllers**
   - Chilled water plant control
   - Hot water plant control
   - Cooling tower control
   - Sequence of operations for dual-duct systems
