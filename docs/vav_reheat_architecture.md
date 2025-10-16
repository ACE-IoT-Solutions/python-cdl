# ASHRAE2006 VAV Reheat System Architecture

**Project**: Python CDL Implementation
**System**: Buildings.Examples.VAVReheat.ASHRAE2006
**Control Sequence**: ASHRAE VAV 2A2-21232
**Date**: 2025-10-16
**Version**: 1.0

## Executive Summary

This document defines the architecture for implementing the Buildings.Examples.VAVReheat.ASHRAE2006 Modelica example in Python CDL. The system implements a five-zone Variable Air Volume (VAV) system with reheat following ASHRAE control sequence VAV 2A2-21232.

### System Overview

- **Type**: Multi-zone VAV with economizer and reheat
- **Zones**: 5 (Corridor, South, North, East, West)
- **AHU Components**: Supply/return fans, economizer, heating/cooling coils
- **Terminal Units**: VAV boxes with reheat coils (5 units)
- **Control Strategy**: Dual-maximum with constant volume heating
- **Operating Modes**: Occupied, Unoccupied Off, Night Setback, Warm-up, Pre-cool

## 1. System Component Hierarchy

### 1.1 Top-Level System Structure

```
VAVReheatSystem (CompositeBlock)
├── ModeController (Composite - Finite State Machine)
│   ├── OccupancySchedule (Elementary)
│   ├── ModeSelector (Elementary - State Machine)
│   └── SetpointManager (Composite)
├── AirHandlingUnit (Composite)
│   ├── SupplyFanController (Composite)
│   ├── ReturnFanController (Composite)
│   ├── EconomizerController (Composite)
│   ├── CoolingCoilController (Composite)
│   └── HeatingCoilController (Composite)
├── ZoneControllers (Composite - 5 instances)
│   ├── ZoneSouth (Composite)
│   ├── ZoneNorth (Composite)
│   ├── ZoneEast (Composite)
│   ├── ZoneWest (Composite)
│   └── ZoneCorridor (Composite)
└── SystemCoordination (Composite)
    ├── StaticPressureReset (Composite)
    ├── SupplyAirTempReset (Composite)
    └── VentilationCalculator (Composite)
```

### 1.2 Component Relationships

```
System Inputs:
  - Weather: OutdoorAirTemp, OutdoorAirHumidity, OutdoorAirEnthalpy
  - Schedules: OccupancySchedule, SetpointSchedules
  - Zone Measurements: ZoneTemp[5], ZoneFlowRate[5]
  - System Measurements: DuctStaticPressure, SupplyAirTemp, ReturnAirTemp

System Outputs:
  - Fan Speeds: SupplyFanSpeed, ReturnFanSpeed
  - Damper Positions: OutdoorAirDamper, ReturnAirDamper, ExhaustAirDamper
  - Coil Signals: CoolingCoilValve, HeatingCoilValve
  - Terminal Unit Signals: VAVDamperPosition[5], ReheatValvePosition[5]
```

## 2. File Organization Structure

### 2.1 Directory Layout

```
examples/
└── vav_reheat/
    ├── README.md                          # System documentation
    ├── system/
    │   ├── __init__.py                    # Package initialization
    │   ├── vav_system.py                  # Top-level system definition
    │   └── system_config.py               # System configuration/constants
    ├── controllers/
    │   ├── __init__.py
    │   ├── mode_controller.py             # Operating mode FSM
    │   ├── ahu_controller.py              # AHU control logic
    │   ├── zone_controller.py             # Zone-level controller
    │   └── coordination.py                # System coordination logic
    ├── sequences/
    │   ├── __init__.py
    │   ├── economizer.py                  # Economizer sequence
    │   ├── fan_control.py                 # Supply/return fan control
    │   ├── coil_control.py                # Heating/cooling coil control
    │   ├── vav_terminal.py                # Terminal unit control
    │   └── setpoint_reset.py              # Dynamic setpoint resets
    ├── cdl_json/
    │   ├── vav_system.json                # Complete system CDL-JSON
    │   ├── mode_controller.json           # Mode controller CDL-JSON
    │   ├── ahu_controller.json            # AHU controller CDL-JSON
    │   ├── zone_controller.json           # Zone controller CDL-JSON
    │   └── elementary_blocks.json         # Custom elementary blocks
    ├── simulation/
    │   ├── __init__.py
    │   ├── building_model.py              # Simplified building dynamics
    │   ├── weather_generator.py           # Weather data generation
    │   └── simulation_runner.py           # Main simulation executor
    ├── tests/
    │   ├── __init__.py
    │   ├── test_mode_controller.py        # Mode controller tests
    │   ├── test_ahu_controller.py         # AHU tests
    │   ├── test_zone_controller.py        # Zone controller tests
    │   ├── test_integration.py            # System integration tests
    │   └── fixtures/                      # Test data and scenarios
    └── notebooks/
        ├── system_overview.ipynb          # Interactive documentation
        ├── 24hour_simulation.ipynb        # Full day simulation
        └── performance_analysis.ipynb     # Energy/comfort analysis
```

### 2.2 CDL-JSON File Organization

Each major controller will have:
1. **Standalone CDL-JSON**: Individual controller as composite block
2. **Elementary Blocks**: Custom blocks specific to VAV control
3. **Integration JSON**: How controllers connect in full system

## 3. Class Definitions and Responsibilities

### 3.1 ModeController Class

**File**: `controllers/mode_controller.py`

**Purpose**: Manages system operating modes based on occupancy and conditions

```python
class ModeController(CompositeBlock):
    """
    Finite state machine for VAV system operating modes.

    States:
        - OCCUPIED: Normal occupied operation
        - UNOCCUPIED_OFF: System off during unoccupied periods
        - NIGHT_SETBACK: Minimal heating/cooling during unoccupied
        - WARMUP: Pre-heat before occupancy
        - PRECOOL: Pre-cool before occupancy

    Inputs:
        - occupancy_schedule: Boolean (occupied/unoccupied)
        - outdoor_temp: Real [degC]
        - zone_temps: Real[5] [degC]
        - time_to_occupancy: Real [minutes]

    Outputs:
        - current_mode: Integer (mode enumeration)
        - heating_setpoint: Real [degC]
        - cooling_setpoint: Real [degC]
        - min_outdoor_air: Real [%]

    Parameters:
        - occupied_heat_sp: 21.0 degC
        - occupied_cool_sp: 24.0 degC
        - unoccupied_heat_sp: 15.0 degC
        - unoccupied_cool_sp: 30.0 degC
        - warmup_time: 60.0 minutes
        - precool_time: 30.0 minutes
    """
```

**CDL Blocks Used**:
- `CDL.Logical.Switch` - Mode selection
- `CDL.Reals.Switch` - Setpoint selection
- `CDL.Integers.Equal` - State comparison
- `CDL.Logical.Timer` - Timing logic
- `CDL.Conversions.BooleanToInteger` - State encoding

### 3.2 AHUController Class

**File**: `controllers/ahu_controller.py`

**Purpose**: Coordinates all AHU-level control sequences

```python
class AHUController(CompositeBlock):
    """
    Air Handling Unit master controller.

    Subsystems:
        - SupplyFanController: Modulates fan speed based on duct pressure
        - ReturnFanController: Tracks supply airflow
        - EconomizerController: Outdoor/return air mixing
        - CoolingCoilController: Cooling valve control
        - HeatingCoilController: Heating valve control

    Inputs:
        - duct_static_pressure: Real [Pa]
        - duct_pressure_setpoint: Real [Pa]
        - supply_air_temp: Real [degC]
        - supply_temp_setpoint: Real [degC]
        - return_air_temp: Real [degC]
        - outdoor_air_temp: Real [degC]
        - outdoor_air_enthalpy: Real [J/kg]
        - return_air_enthalpy: Real [J/kg]
        - system_mode: Integer

    Outputs:
        - supply_fan_speed: Real [0-1]
        - return_fan_speed: Real [0-1]
        - outdoor_air_damper: Real [0-1]
        - return_air_damper: Real [0-1]
        - exhaust_damper: Real [0-1]
        - cooling_valve: Real [0-1]
        - heating_valve: Real [0-1]

    Control Logic:
        - Supply fan: PI control on duct static pressure
        - Return fan: Flow tracking with minimum delta
        - Economizer: Enthalpy-based free cooling with sequence
        - Coil sequencing: Economizer → Mechanical cooling → Heating
    """
```

**CDL Blocks Used**:
- `CDL.Continuous.PID` - Fan speed control, coil control
- `CDL.Reals.Min/Max` - Limiting and coordination
- `CDL.Logical.And/Or` - Enable conditions
- `CDL.Reals.Line` - Linearization for actuators

### 3.3 ZoneController Class

**File**: `controllers/zone_controller.py`

**Purpose**: Individual zone temperature and airflow control

```python
class ZoneController(CompositeBlock):
    """
    VAV terminal unit controller with reheat.
    Control sequence: Dual-maximum with constant volume heating.

    Inputs:
        - zone_temp: Real [degC]
        - cooling_setpoint: Real [degC]
        - heating_setpoint: Real [degC]
        - duct_static_pressure: Real [Pa]
        - supply_air_temp: Real [degC]
        - min_airflow: Real [m3/s]
        - max_airflow: Real [m3/s]

    Outputs:
        - damper_position: Real [0-1]
        - reheat_valve: Real [0-1]
        - airflow_setpoint: Real [m3/s]

    Control Logic:
        Cooling mode (Tzone > Tcool):
            - Increase airflow from minimum to maximum
            - Reheat valve closed

        Deadband (Theat < Tzone < Tcool):
            - Maintain minimum airflow
            - Reheat valve modulates to maintain Theat

        Heating mode (Tzone < Theat):
            - Increase airflow to heating maximum
            - Reheat valve fully open

    Parameters:
        - cooling_max_flow: 1.0 m3/s
        - heating_max_flow: 0.4 m3/s
        - min_flow: 0.15 m3/s
        - damper_kp: 0.5
        - reheat_kp: 0.5
    """
```

**CDL Blocks Used**:
- `CDL.Continuous.PID` - Temperature control loops
- `CDL.Reals.Line` - Airflow to damper position conversion
- `CDL.Logical.Hysteresis` - Mode transitions
- `CDL.Reals.MultiplyByParameter` - Gain scheduling
- `CDL.Reals.Limiter` - Output saturation

### 3.4 SystemCoordination Class

**File**: `controllers/coordination.py`

**Purpose**: System-wide coordination and supervisory control

```python
class SystemCoordination(CompositeBlock):
    """
    Supervisory control and coordination.

    Functions:
        - Static Pressure Reset: Trim & respond based on zone demands
        - Supply Air Temperature Reset: Based on zone cooling demands
        - Minimum Outdoor Air: Based on occupancy and ventilation
        - Demand Limiting: Response to demand signals

    Inputs:
        - zone_damper_positions: Real[5] [0-1]
        - zone_cooling_demands: Real[5] [0-1]
        - outdoor_air_temp: Real [degC]
        - system_mode: Integer

    Outputs:
        - duct_pressure_setpoint: Real [Pa]
        - supply_temp_setpoint: Real [degC]
        - min_oa_setpoint: Real [%]

    Reset Logic:
        Static Pressure Reset:
            - If any zone damper > 95%: Increase setpoint
            - If all zone dampers < 85%: Decrease setpoint
            - Limits: 150-400 Pa

        Supply Temp Reset:
            - Based on maximum zone cooling demand
            - Range: 13-18 degC
            - Outdoor air temperature compensation
    """
```

**CDL Blocks Used**:
- `CDL.Reals.MovingMean` - Averaging zone signals
- `CDL.Reals.Max/Min` - Finding extremes
- `CDL.Logical.TrueHoldWithReset` - Trim & respond logic
- `CDL.Reals.AddParameter` - Setpoint adjustments
- `CDL.Reals.Limiter` - Setpoint limits

### 3.5 Support Classes

**File**: `simulation/building_model.py`

```python
class SimplifiedBuildingModel:
    """
    Simplified building thermal dynamics for simulation.

    Purpose: Provide realistic zone temperature responses to control actions

    Features:
        - First-order thermal zones with heat capacity
        - Internal gains (people, lights, equipment)
        - Solar gains by orientation
        - Heat transfer through envelope
        - Airflow impact on zone temperature

    Not a CDL block - pure Python for simulation only
    """
```

**File**: `simulation/weather_generator.py`

```python
class WeatherGenerator:
    """
    Generate realistic weather profiles for simulation.

    Features:
        - Typical Meteorological Year (TMY) data import
        - Synthetic weather generation
        - Outdoor air temperature, humidity, enthalpy
        - Solar radiation by orientation
    """
```

## 4. Data Flow Diagrams

### 4.1 System-Level Data Flow

```
Weather Data → ModeController → Operating Mode → AHU Controller → Fan/Damper Signals
                     ↓                                    ↓
                Setpoints                          Supply Air Conditions
                     ↓                                    ↓
              Zone Controllers ← Zone Measurements
                     ↓
         Terminal Unit Signals (Dampers, Reheat)
                     ↓
            Building Thermal Model
                     ↓
          Updated Zone Temperatures → (feedback)
```

### 4.2 AHU Control Data Flow

```
Mode & Setpoints
       ↓
   [AHU Controller]
       ↓
   ┌───┴───┬─────────┬──────────┬────────────┐
   ↓       ↓         ↓          ↓            ↓
Supply   Return   Economizer  Cooling    Heating
  Fan      Fan                  Coil       Coil
   ↓       ↓         ↓          ↓            ↓
Speed   Speed   OA/RA/EA    Valve       Valve
             Dampers        Position    Position
```

### 4.3 Zone Control Data Flow

```
Zone Temperature ──┐
Cooling Setpoint ──┼─→ [Cooling Loop] ─→ Airflow Demand
Heating Setpoint ──┘         ↓                  ↓
                    [Mode Logic]          [Damper Control]
                         ↓                       ↓
                  [Heating Loop]         Damper Position
                         ↓
                  Reheat Valve Position
```

### 4.4 Mode Controller State Transitions

```
                    ┌──────────────┐
      ┌────────────→│ UNOCCUPIED   │←──────────┐
      │             │     OFF      │           │
      │             └──────┬───────┘           │
      │                    │                   │
      │ time_to_occ        │ outdoor_temp      │
      │ & cold             │                   │
      │                    ↓                   │
      │             ┌──────────────┐           │
      │             │   WARMUP     │           │
      │             └──────┬───────┘           │
      │                    │                   │
      │ time_to_occ        │ occupied          │
      │ & hot              │                   │
      │                    ↓                   │
      │             ┌──────────────┐           │
      │             │  PRECOOL     │           │
      │             └──────┬───────┘           │
      │                    │                   │
      │                    │ occupied          │
      │                    ↓                   │
      │             ┌──────────────┐           │
      └─────────────│   OCCUPIED   │───────────┘
       unoccupied   └──────────────┘    unoccupied
```

## 5. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Objectives**:
- Set up project structure
- Implement elementary blocks specific to VAV control
- Create base configuration and constants

**Deliverables**:
1. Directory structure created
2. `system_config.py` with all constants
3. Custom elementary blocks implemented:
   - `HysteresisWithDeadband` - For mode transitions
   - `DualMaximumLogic` - For zone airflow control
   - `TrimAndRespond` - For setpoint resets
   - `EnthalpyCalculator` - For economizer control
   - `AirflowToDamper` - Airflow to damper position conversion

**Tests**:
- Unit tests for each elementary block
- Validation against CDL specification

**Exit Criteria**: All elementary blocks pass tests and produce expected outputs

### Phase 2: Zone Control (Week 3)

**Objectives**:
- Implement single zone controller
- Validate dual-maximum control logic
- Test with simplified building model

**Deliverables**:
1. `zone_controller.py` implementation
2. `zone_controller.json` CDL-JSON definition
3. Zone controller unit tests
4. Single-zone simulation notebook

**Control Sequences**:
- Cooling mode airflow modulation
- Heating mode with reheat
- Deadband operation
- Mode transitions with hysteresis

**Tests**:
- Step response tests (setpoint changes)
- Disturbance rejection (load changes)
- Mode transition validation
- Energy conservation checks

**Exit Criteria**: Single zone maintains temperature within ±0.5°C of setpoint

### Phase 3: AHU Control (Week 4-5)

**Objectives**:
- Implement AHU controller with all subsystems
- Integrate supply/return fans, economizer, coils
- Test coil sequencing and economizer logic

**Deliverables**:
1. `ahu_controller.py` implementation
2. `sequences/economizer.py`
3. `sequences/fan_control.py`
4. `sequences/coil_control.py`
5. `ahu_controller.json` CDL-JSON definition
6. AHU controller tests
7. AHU simulation notebook

**Control Sequences**:
- Supply fan PI control with duct pressure feedback
- Return fan tracking control
- Economizer with enthalpy comparison
- Cooling/heating coil sequencing
- Minimum outdoor air enforcement

**Tests**:
- Fan control stability tests
- Economizer mode transitions
- Coil sequencing validation
- Outdoor air ventilation compliance

**Exit Criteria**:
- AHU maintains duct pressure setpoint ±10 Pa
- Economizer engages when beneficial
- Proper coil sequencing (no heating + cooling)

### Phase 4: Mode Control (Week 6)

**Objectives**:
- Implement operating mode finite state machine
- Create occupancy scheduling
- Implement setpoint managers for each mode

**Deliverables**:
1. `mode_controller.py` implementation
2. `mode_controller.json` CDL-JSON definition
3. Mode controller tests
4. Mode transition notebook

**Control Sequences**:
- State machine with 5 operating modes
- Occupancy schedule integration
- Dynamic setpoint calculation
- Warmup/precool timing logic

**Tests**:
- State transition validation
- Warmup/precool effectiveness
- Unoccupied energy savings
- Mode timing accuracy

**Exit Criteria**:
- Proper mode transitions based on schedule and conditions
- Zones reach setpoint before occupancy 95% of time

### Phase 5: System Coordination (Week 7)

**Objectives**:
- Implement supervisory control algorithms
- Add trim & respond logic for setpoint resets
- Integrate system-wide coordination

**Deliverables**:
1. `coordination.py` implementation
2. `sequences/setpoint_reset.py`
3. System coordination tests
4. Performance optimization notebook

**Control Sequences**:
- Static pressure reset (trim & respond)
- Supply air temperature reset
- Minimum outdoor air calculation
- Demand limiting (optional)

**Tests**:
- Setpoint reset validation
- System stability with resets
- Energy impact analysis
- Multi-zone interaction tests

**Exit Criteria**:
- Duct pressure resets reduce energy by 10%+
- Supply temp reset improves comfort
- No hunting or instability

### Phase 6: Full System Integration (Week 8-9)

**Objectives**:
- Integrate all controllers into complete system
- Create complete CDL-JSON system model
- Implement building thermal model
- Run full multi-zone simulations

**Deliverables**:
1. `vav_system.py` - Complete system integration
2. `vav_system.json` - Full system CDL-JSON
3. `simulation/building_model.py` - Thermal dynamics
4. `simulation/simulation_runner.py` - Simulation executor
5. `notebooks/24hour_simulation.ipynb` - Full simulation
6. Integration tests

**Simulation Features**:
- 5 thermal zones with different orientations
- Realistic internal gains (people, lights, equipment)
- Weather profiles (hot day, cold day, mild day)
- 24-hour continuous operation
- Mode transitions throughout day

**Tests**:
- Full system integration tests
- Multi-zone interaction validation
- Energy performance benchmarking
- Comfort metrics (PMV, temperature deviation)
- ASHRAE Standard 55 compliance

**Exit Criteria**:
- 24-hour simulation completes successfully
- All zones maintain comfort conditions during occupied hours
- System demonstrates energy-efficient operation
- Control sequences match ASHRAE 2006 specification

### Phase 7: Validation & Documentation (Week 10)

**Objectives**:
- Validate against Modelica reference implementation
- Create comprehensive documentation
- Generate performance reports
- Create tutorial notebooks

**Deliverables**:
1. Validation report comparing to Modelica results
2. Complete system README with architecture overview
3. API documentation for all controllers
4. Tutorial notebooks:
   - System overview and component explanation
   - Running custom simulations
   - Analyzing results
   - Modifying control sequences
5. Performance analysis:
   - Energy consumption breakdown
   - Comfort metrics
   - Control stability analysis
   - Comparison to baseline

**Validation Criteria**:
- Zone temperatures within ±1°C of Modelica reference
- Energy consumption within ±5% of Modelica reference
- Control signals match reference patterns
- Mode transitions occur at same times

**Exit Criteria**:
- All validation tests pass
- Documentation complete and reviewed
- Tutorial notebooks run successfully
- Performance meets or exceeds reference

## 6. Interfaces Between Components

### 6.1 ModeController → AHUController

```python
# Interface signals
mode_signals = {
    "current_mode": Integer,  # Operating mode enumeration
    "heating_setpoint": Real,  # Global heating setpoint [degC]
    "cooling_setpoint": Real,  # Global cooling setpoint [degC]
    "min_oa_fraction": Real,  # Minimum outdoor air [%]
    "enable_economizer": Boolean,  # Enable free cooling
}
```

### 6.2 ModeController → ZoneControllers

```python
# Interface signals (broadcast to all zones)
zone_setpoints = {
    "heating_setpoint": Real,  # Zone heating setpoint [degC]
    "cooling_setpoint": Real,  # Zone cooling setpoint [degC]
    "min_airflow": Real,  # Minimum airflow [m3/s]
}
```

### 6.3 AHUController → ZoneControllers

```python
# Interface signals (broadcast to all zones)
ahu_to_zones = {
    "supply_air_temp": Real,  # Supply air temperature [degC]
    "duct_static_pressure": Real,  # Duct pressure [Pa]
}
```

### 6.4 ZoneControllers → SystemCoordination

```python
# Interface signals (from each zone)
zone_feedback = {
    "damper_position": Real,  # Current damper position [0-1]
    "cooling_demand": Real,  # Cooling demand signal [0-1]
    "heating_demand": Real,  # Heating demand signal [0-1]
    "airflow_measured": Real,  # Measured airflow [m3/s]
}
```

### 6.5 SystemCoordination → AHUController

```python
# Interface signals
coordination_signals = {
    "duct_pressure_setpoint": Real,  # Dynamic pressure setpoint [Pa]
    "supply_temp_setpoint": Real,  # Dynamic temp setpoint [degC]
    "min_oa_setpoint": Real,  # Calculated minimum OA [m3/s]
}
```

## 7. Configuration and Parameters

### 7.1 System Configuration

**File**: `system/system_config.py`

```python
@dataclass
class VAVSystemConfig:
    """Complete VAV system configuration"""

    # Building parameters
    num_zones: int = 5
    floor_area: float = 1000.0  # m2
    floor_height: float = 3.0  # m

    # AHU parameters
    supply_fan_max_flow: float = 5.0  # m3/s
    supply_fan_efficiency: float = 0.6
    supply_fan_pressure: float = 300.0  # Pa

    # Economizer parameters
    economizer_type: str = "DifferentialEnthalpy"
    economizer_deadband: float = 8000.0  # J/kg
    min_oa_flow: float = 0.5  # m3/s

    # Coil parameters
    cooling_coil_capacity: float = 50000.0  # W
    heating_coil_capacity: float = 30000.0  # W

    # Zone parameters
    zone_configs: Dict[str, ZoneConfig] = field(default_factory=dict)
```

### 7.2 Zone Configuration

```python
@dataclass
class ZoneConfig:
    """Individual zone configuration"""

    name: str
    area: float  # m2
    volume: float  # m3
    orientation: str  # "North", "South", "East", "West", "Core"

    # Airflow parameters
    max_airflow_cooling: float  # m3/s
    max_airflow_heating: float  # m3/s
    min_airflow: float  # m3/s

    # Control parameters
    damper_kp: float = 0.5
    damper_ki: float = 0.1
    reheat_kp: float = 0.5
    reheat_ki: float = 0.1

    # Thermal parameters
    heat_capacity: float = 500000.0  # J/K
    ua_value: float = 200.0  # W/K (envelope conductance)
```

### 7.3 Control Tuning Parameters

```python
@dataclass
class ControlTuningParameters:
    """Tuning parameters for all controllers"""

    # Supply fan control
    supply_fan_kp: float = 1.0
    supply_fan_ki: float = 0.5
    supply_fan_min_speed: float = 0.3

    # Static pressure reset
    pressure_trim_rate: float = 5.0  # Pa/min
    pressure_respond_rate: float = 10.0  # Pa/min
    pressure_min: float = 150.0  # Pa
    pressure_max: float = 400.0  # Pa

    # Supply air temperature reset
    sat_reset_min: float = 13.0  # degC
    sat_reset_max: float = 18.0  # degC

    # Mode controller
    warmup_time: float = 60.0  # minutes
    precool_time: float = 30.0  # minutes
```

## 8. Technology Stack

### 8.1 Core Technologies

- **Language**: Python 3.13+
- **Data Models**: Pydantic v2
- **CDL Implementation**: Python CDL library
- **Numerical Computing**: NumPy
- **Visualization**: Matplotlib
- **Testing**: Pytest

### 8.2 Development Tools

- **Dependency Management**: uv
- **Type Checking**: Pyright (via pyrefly)
- **Linting**: Ruff
- **Notebooks**: Jupyter
- **Documentation**: Markdown + Jupyter notebooks

## 9. Testing Strategy

### 9.1 Unit Tests

**Scope**: Individual controller components

**Tests**:
- Elementary block functionality
- Controller response to inputs
- Parameter validation
- Edge cases and error handling

**Tools**: pytest with fixtures

### 9.2 Integration Tests

**Scope**: Controller interactions

**Tests**:
- Mode controller → AHU integration
- AHU → Zone controller integration
- System coordination feedback loops
- Multi-zone interactions

### 9.3 Simulation Tests

**Scope**: Full system behavior

**Tests**:
- 24-hour operation scenarios
- Seasonal variations (summer, winter, swing)
- Extreme weather conditions
- Occupancy pattern variations

### 9.4 Validation Tests

**Scope**: Comparison to reference implementation

**Tests**:
- Match Modelica reference results
- Energy consumption comparison
- Control signal validation
- Performance metrics comparison

## 10. Performance Requirements

### 10.1 Control Performance

- **Zone Temperature Control**: ±0.5°C of setpoint during occupied hours
- **Duct Pressure Control**: ±10 Pa of setpoint
- **Supply Air Temperature**: ±1°C of setpoint
- **Response Time**: Zone temperature reaches setpoint within 30 minutes
- **Stability**: No oscillations > 5 minutes period

### 10.2 Computational Performance

- **Simulation Speed**: > 100× real-time for typical system
- **Memory Usage**: < 500 MB for full system simulation
- **Execution Time**: Single time step < 10 ms
- **Scalability**: Support up to 20 zones without performance degradation

### 10.3 Energy Performance

- **HVAC Energy**: < 100 kWh/m2/year (climate-dependent)
- **Fan Energy**: < 15 kWh/m2/year
- **Economizer Savings**: > 20% cooling energy (when applicable)
- **Reset Savings**: > 10% fan energy from pressure reset

## 11. Key Architectural Decisions

### Decision 1: Composite Block Hierarchy

**Decision**: Implement using nested CompositeBlocks following CDL specification

**Rationale**:
- Matches Modelica structure for easier validation
- Enables modular testing and reuse
- Clear separation of concerns
- CDL-JSON export capability

**Alternatives Considered**:
- Flat structure: Rejected due to complexity and maintainability
- Pure Python classes: Rejected due to lack of CDL compliance

### Decision 2: Simulation vs. Real Building

**Decision**: Include simplified building thermal model for simulation

**Rationale**:
- Enables testing without physical hardware
- Provides realistic feedback for controller development
- Allows performance evaluation before deployment
- Educational value for understanding system behavior

**Trade-offs**:
- Simplified model may not capture all dynamics
- Validation against real building still required

### Decision 3: CDL-JSON Generation

**Decision**: Generate CDL-JSON from Python class definitions

**Rationale**:
- Enables interoperability with other CDL tools
- Validates controller structure
- Documents control sequences in standard format
- Enables model exchange with building automation systems

**Implementation**: Use Pydantic serialization to generate compliant JSON

### Decision 4: Modular Controller Design

**Decision**: Separate controllers for mode, AHU, zones, and coordination

**Rationale**:
- Matches ASHRAE sequence structure
- Enables independent testing and validation
- Facilitates understanding and maintenance
- Allows reuse of components in other systems

### Decision 5: Elementary Block Library

**Decision**: Implement VAV-specific elementary blocks

**Rationale**:
- Dual-maximum logic is specific to VAV control
- Trim & respond not in standard CDL library
- Custom blocks improve readability and reusability
- Can be contributed back to CDL library

## 12. Extension Points

### 12.1 Additional Control Strategies

The architecture supports adding alternative control strategies:

1. **Guideline 36 Implementation**: Replace ASHRAE 2006 sequences with modern G36
2. **Predictive Control**: Add MPC or optimal control algorithms
3. **Demand Response**: Integrate demand response strategies
4. **Fault Detection**: Add AFDD algorithms

### 12.2 Additional Zones

System designed to scale from 5 to 20+ zones:

```python
# Easy addition of zones
zone_configs = {
    "zone_south": ZoneConfig(...),
    "zone_north": ZoneConfig(...),
    # ... add more zones
}
```

### 12.3 Equipment Variations

Support for equipment variations:

- **Multiple AHUs**: Split system into multiple air handlers
- **Different Terminal Units**: Fan-powered boxes, CAV boxes
- **Additional Coils**: Preheat coils, heat recovery
- **Variable Refrigerant Flow**: VRF integration

### 12.4 Integration Options

- **BACnet Integration**: Connect to real BAS systems
- **MQTT Integration**: IoT device connectivity
- **Web Dashboard**: Real-time monitoring and control
- **Optimization Services**: Cloud-based optimization

## 13. Documentation Deliverables

### 13.1 Technical Documentation

1. **Architecture Document** (this document)
2. **API Reference**: Docstrings for all public interfaces
3. **Control Sequence Specification**: Detailed algorithm descriptions
4. **CDL-JSON Schema**: Complete system model documentation

### 13.2 User Documentation

1. **README.md**: System overview and quick start
2. **Installation Guide**: Setup instructions
3. **User Guide**: Running simulations and interpreting results
4. **Troubleshooting Guide**: Common issues and solutions

### 13.3 Tutorial Notebooks

1. **System Overview**: Interactive exploration of architecture
2. **Running Simulations**: Step-by-step simulation guide
3. **Custom Scenarios**: Creating custom test scenarios
4. **Performance Analysis**: Analyzing energy and comfort metrics
5. **Control Tuning**: Adjusting controller parameters

## 14. Success Criteria

### 14.1 Functional Criteria

✅ All controllers implemented and tested
✅ Full system integrates successfully
✅ 24-hour simulation runs without errors
✅ All operating modes function correctly
✅ Zone temperatures maintained within tolerance
✅ Energy performance meets expectations

### 14.2 Quality Criteria

✅ Code coverage > 90%
✅ Type checking passes (strict mode)
✅ All tests pass
✅ Documentation complete
✅ Validation against reference successful

### 14.3 Performance Criteria

✅ Simulation speed > 100× real-time
✅ Control stability demonstrated
✅ Energy savings validated
✅ Comfort requirements met

## 15. Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 1. Foundation | 2 weeks | Elementary blocks complete |
| 2. Zone Control | 1 week | Single zone controller validated |
| 3. AHU Control | 2 weeks | AHU controller complete |
| 4. Mode Control | 1 week | FSM operational |
| 5. Coordination | 1 week | Setpoint resets working |
| 6. Integration | 2 weeks | Full system simulation |
| 7. Validation | 1 week | Documentation & validation |
| **Total** | **10 weeks** | **Production-ready system** |

## 16. References

### Standards and Guidelines

1. **ASHRAE (2006)**. "Sequences of Operation for Common HVAC Systems." ASHRAE, Atlanta, GA.
2. **ASHRAE Guideline 36-2021**. "High-Performance Sequences of Operation for HVAC Systems."
3. **ASHRAE Standard 231P**. "Control Description Language (CDL)."

### Technical References

4. **Buildings Library**. Modelica Buildings library, LBNL. https://simulationresearch.lbl.gov/modelica/
5. **CDL Specification**. https://obc.lbl.gov/specification/cdl.html
6. **Buildings.Examples.VAVReheat.ASHRAE2006**. Reference implementation in Modelica.

### Implementation References

7. **Python CDL Architecture**. `/docs/architecture/ARCHITECTURE_SUMMARY.md`
8. **Python CDL Module Structure**. `/docs/architecture/module-structure.md`
9. **Pydantic Models Design**. `/docs/architecture/pydantic-models-design.md`

---

**Document Status**: COMPLETE - Ready for Implementation
**Next Steps**: Begin Phase 1 (Foundation) implementation
**Approval Required**: Project lead review before proceeding
