# VAV Reheat System Architecture

**Version**: 1.0
**Date**: 2025-10-16
**System**: ASHRAE2006 VAV Reheat

## Quick Reference

This document provides a quick reference for the VAV Reheat system architecture designed for Python CDL.

**Full Architecture Document**: `/docs/vav_reheat_architecture.md`
**Summary Document**: `/docs/examples/vav_reheat_summary.md`

## Component Overview

### 1. ModeController
**File**: `controllers/mode_controller.py`
**Type**: Finite State Machine
**States**: Occupied, Unoccupied Off, Night Setback, Warmup, Pre-cool
**Purpose**: Manages operating modes based on schedule and conditions

### 2. AHUController
**File**: `controllers/ahu_controller.py`
**Type**: Composite Controller
**Subsystems**: Supply/Return Fans, Economizer, Cooling/Heating Coils
**Purpose**: Central air handling unit control

### 3. ZoneController (×5)
**File**: `controllers/zone_controller.py`
**Type**: Composite Controller
**Control**: Dual-maximum with reheat
**Purpose**: Individual zone temperature and airflow control

### 4. SystemCoordination
**File**: `controllers/coordination.py`
**Type**: Supervisory Controller
**Functions**: Pressure reset, temp reset, ventilation
**Purpose**: System-wide optimization

## Data Flow

```
Weather → Mode Controller → Setpoints → AHU Controller → Supply Air
              ↓                              ↓
          Schedules                    Zone Controllers
                                            ↓
                                    Terminal Units
                                            ↓
                                    Building Model
                                            ↓
                                    Zone Temps (feedback)
                                            ↓
                                System Coordination → Resets
```

## Key Interfaces

### ModeController Outputs
- `current_mode`: Integer (mode enumeration)
- `heating_setpoint`: Real [degC]
- `cooling_setpoint`: Real [degC]
- `min_outdoor_air`: Real [%]

### AHUController Outputs
- `supply_fan_speed`: Real [0-1]
- `return_fan_speed`: Real [0-1]
- `oa_damper`, `ra_damper`, `ea_damper`: Real [0-1]
- `cooling_valve`, `heating_valve`: Real [0-1]

### ZoneController Outputs (per zone)
- `damper_position`: Real [0-1]
- `reheat_valve`: Real [0-1]
- `airflow_setpoint`: Real [m3/s]

### SystemCoordination Outputs
- `duct_pressure_setpoint`: Real [Pa]
- `supply_temp_setpoint`: Real [degC]
- `min_oa_setpoint`: Real [%]

## Control Sequences

### Zone Control (Dual-Maximum with Reheat)

```
Cooling (Tzone > Tcool):
  → Increase airflow: min → max_cooling
  → Reheat valve: closed

Deadband (Theat < Tzone < Tcool):
  → Airflow: minimum (for ventilation)
  → Reheat valve: modulates to maintain Theat

Heating (Tzone < Theat):
  → Increase airflow: min → max_heating
  → Reheat valve: fully open
```

### AHU Coil Sequencing

```
1. Economizer: 0% → 100% OA damper
2. Cooling Coil: After economizer fully open
3. Heating Coil: When supply temp < setpoint (cooling lockout)
```

### Supervisory Resets

**Static Pressure Reset (Trim & Respond)**:
```
If any_damper > 95%: SP = SP + trim_rate * dt
If all_dampers < 85%: SP = SP - respond_rate * dt
Limits: 150 Pa ≤ SP ≤ 400 Pa
```

**Supply Air Temperature Reset**:
```
SAT_SP = f(max_zone_cooling_demand, outdoor_temp)
Range: 13°C ≤ SAT_SP ≤ 18°C
```

## Implementation Phases

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. Foundation | 2 weeks | Elementary blocks |
| 2. Zone Control | 1 week | Zone controller validated |
| 3. AHU Control | 2 weeks | AHU controller complete |
| 4. Mode Control | 1 week | FSM operational |
| 5. Coordination | 1 week | Resets working |
| 6. Integration | 2 weeks | Full system simulation |
| 7. Validation | 1 week | Documentation complete |

**Total**: 10 weeks

## Directory Structure

```
vav_reheat/
├── system/              # Top-level system and config
├── controllers/         # Main control components
├── sequences/           # Reusable control sequences
├── cdl_json/           # CDL-JSON model definitions
├── simulation/         # Building model and runner
├── tests/              # Test suite
├── notebooks/          # Interactive tutorials
└── docs/               # Documentation (this folder)
```

## Configuration

### System Constants (system_config.py)
```python
NUM_ZONES = 5
SUPPLY_FAN_MAX_FLOW = 5.0  # m³/s
MIN_OUTDOOR_AIR = 0.5      # m³/s
COOLING_CAPACITY = 50000   # W
HEATING_CAPACITY = 30000   # W
```

### Zone Parameters (per zone)
```python
max_airflow_cooling = 1.0   # m³/s
max_airflow_heating = 0.4   # m³/s
min_airflow = 0.15          # m³/s
damper_kp = 0.5
reheat_kp = 0.5
```

### Setpoints
```python
occupied_heating = 21.0     # °C
occupied_cooling = 24.0     # °C
unoccupied_heating = 15.0   # °C
unoccupied_cooling = 30.0   # °C
```

## Testing Strategy

### Unit Tests
- Elementary block functionality
- Individual controller responses
- Parameter validation

### Integration Tests
- Controller interactions
- Multi-zone coordination
- Mode transitions

### Simulation Tests
- 24-hour operation
- Seasonal scenarios
- Extreme conditions

### Validation Tests
- Comparison to Modelica reference
- Energy consumption
- Temperature accuracy

## Performance Targets

### Control Performance
- Zone temperature: ±0.5°C during occupied
- Duct pressure: ±10 Pa of setpoint
- Response time: < 30 minutes

### Computational Performance
- Simulation speed: > 100× real-time
- Memory usage: < 500 MB
- Time step execution: < 10 ms

### Energy Performance
- HVAC energy: < 100 kWh/m²/year
- Economizer savings: > 20% cooling
- Reset savings: > 10% fan energy

## References

- **Full Architecture**: `/docs/vav_reheat_architecture.md`
- **Implementation Summary**: `/docs/examples/vav_reheat_summary.md`
- **CDL Specification**: https://obc.lbl.gov/specification/cdl.html
- **Modelica Reference**: Buildings.Examples.VAVReheat.ASHRAE2006

## Next Steps

1. Review architecture document
2. Begin Phase 1 implementation
3. Set up test infrastructure
4. Create project tracking board

---

**Status**: Architecture design complete
**Ready for**: Implementation Phase 1
