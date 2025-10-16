# VAV Reheat Architecture - Key Decisions Summary

**Date**: 2025-10-16
**System**: ASHRAE2006 VAV Reheat (Buildings.Examples.VAVReheat.ASHRAE2006)

## Executive Summary

Designed complete architecture for implementing ASHRAE2006 5-zone VAV Reheat system in Python CDL. The system implements control sequence VAV 2A2-21232 with economizer, reheat, and supervisory control.

## Key Architectural Decisions

### 1. Component Hierarchy (Nested Composite Blocks)

**Structure**:
```
VAVReheatSystem
├── ModeController (FSM: 5 operating modes)
├── AirHandlingUnit (5 subsystems)
├── ZoneControllers (5 instances, dual-maximum control)
└── SystemCoordination (supervisory control)
```

**Rationale**:
- Matches Modelica reference for validation
- Modular design enables independent testing
- Clear separation of concerns
- Reusable components

### 2. File Organization

**Directory Structure**:
```
examples/vav_reheat/
├── system/          # Top-level system
├── controllers/     # Main controllers (mode, AHU, zone, coordination)
├── sequences/       # Control sequences (economizer, fans, coils, resets)
├── cdl_json/        # CDL-JSON definitions
├── simulation/      # Building model and runner
├── tests/           # Comprehensive test suite
└── notebooks/       # Interactive documentation
```

**Benefits**:
- Clear separation of controllers and sequences
- CDL-JSON for interoperability
- Simulation support for testing
- Tutorial notebooks for education

### 3. Controller Design

#### 3.1 ModeController (Finite State Machine)

**States**: Occupied, Unoccupied Off, Night Setback, Warmup, Pre-cool

**Responsibilities**:
- Occupancy-based mode management
- Setpoint management per mode
- Warmup/precool timing
- Minimum outdoor air requirements

**Key Features**:
- State machine implementation using CDL blocks
- Hysteresis for stable transitions
- Temperature-based mode selection

#### 3.2 AHUController

**Subsystems**:
- Supply Fan: PI control on duct static pressure
- Return Fan: Flow tracking
- Economizer: Enthalpy-based free cooling
- Cooling Coil: Sequenced after economizer
- Heating Coil: Sequenced separately

**Key Features**:
- Coil sequencing prevents simultaneous heating/cooling
- Minimum outdoor air enforcement
- Smooth transitions between modes

#### 3.3 ZoneController (Dual-Maximum with Reheat)

**Control Logic**:
- **Cooling**: Increase airflow (min → max cooling)
- **Deadband**: Minimum airflow + reheat modulation
- **Heating**: Increase airflow (min → max heating) + reheat

**Key Features**:
- Three-mode operation with hysteresis
- Separate cooling and heating maximum airflows
- Discharge air temperature-based reheat control

#### 3.4 SystemCoordination (Supervisory Control)

**Functions**:
- Static pressure reset (trim & respond)
- Supply air temperature reset
- Minimum outdoor air calculation

**Key Features**:
- Zone feedback-based resets
- Energy optimization
- Maintains comfort and ventilation

### 4. Custom Elementary Blocks

**New Blocks Required**:
1. `DualMaximumLogic` - Zone airflow control
2. `TrimAndRespond` - Setpoint reset algorithm
3. `EnthalpyCalculator` - For economizer
4. `AirflowToDamper` - Flow to position conversion
5. `HysteresisWithDeadband` - Mode transitions

**Rationale**: Not in standard CDL library, specific to VAV control

### 5. Interface Specifications

**Critical Interfaces**:

| From → To | Signals | Type |
|-----------|---------|------|
| Mode → AHU | Operating mode, setpoints, OA minimum | Integer, Real |
| Mode → Zones | Heating/cooling setpoints, min airflow | Real |
| AHU → Zones | Supply air temp, duct pressure | Real |
| Zones → Coordination | Damper positions, demands | Real |
| Coordination → AHU | Reset setpoints | Real |

### 6. Simulation Integration

**Building Model**:
- Simplified first-order thermal zones
- Realistic internal gains (people, lights, equipment)
- Solar gains by orientation
- Envelope heat transfer

**Weather Generator**:
- TMY data import capability
- Synthetic weather profiles
- Temperature, humidity, enthalpy, solar

**Purpose**: Enable controller testing without physical building

### 7. Implementation Phases (10 weeks)

| Phase | Duration | Focus |
|-------|----------|-------|
| 1. Foundation | 2 weeks | Elementary blocks, structure |
| 2. Zone Control | 1 week | Single zone controller |
| 3. AHU Control | 2 weeks | AHU with all subsystems |
| 4. Mode Control | 1 week | Operating mode FSM |
| 5. Coordination | 1 week | Supervisory control |
| 6. Integration | 2 weeks | Full system + simulation |
| 7. Validation | 1 week | Testing + documentation |

### 8. Testing Strategy

**Four Layers**:
1. **Unit Tests**: Individual blocks and controllers
2. **Integration Tests**: Controller interactions
3. **Simulation Tests**: 24-hour scenarios
4. **Validation Tests**: Comparison to Modelica reference

**Coverage Targets**:
- Code coverage: > 90%
- Type coverage: 100% (Pyright strict)
- Validation accuracy: ±1°C temperature, ±5% energy

### 9. Performance Requirements

**Control Performance**:
- Zone temperature: ±0.5°C during occupied
- Duct pressure: ±10 Pa
- Response time: 30 minutes to setpoint

**Computational Performance**:
- Simulation speed: > 100× real-time
- Memory: < 500 MB
- Time step: < 10 ms

**Energy Performance**:
- HVAC energy: < 100 kWh/m²/year
- Economizer savings: > 20% cooling energy
- Reset savings: > 10% fan energy

### 10. Technology Stack

**Core**:
- Python 3.13+, Pydantic v2, Python CDL library
- NumPy (simulation), Matplotlib (visualization)
- Pytest (testing), Jupyter (notebooks)

**Tools**:
- uv (dependencies), Pyright (types), Ruff (linting)

## Data Flow Summary

```
Weather → Mode Controller → Setpoints & Operating Mode
             ↓                          ↓
         Schedules                  AHU Controller
             ↓                          ↓
      Zone Controllers ←───── Supply Air Conditions
             ↓
      Terminal Units → Building Model → Zone Temps (feedback)
             ↓
    System Coordination → Setpoint Resets → AHU Controller
```

## Configuration Highlights

**System Parameters**:
- 5 zones (Corridor, South, North, East, West)
- Supply fan: 5 m³/s maximum, 300 Pa design pressure
- Economizer: Differential enthalpy control
- Coil capacities: 50 kW cooling, 30 kW heating

**Zone Parameters** (per zone):
- Configurable airflow limits (cooling max, heating max, minimum)
- Individual thermal properties (heat capacity, UA value)
- Orientation-specific solar gains

**Control Tuning**:
- PI gains for all loops
- Trim & respond rates for resets
- Hysteresis bands for mode transitions

## Extension Points

**Supported Extensions**:
1. **Alternative Control**: G36, MPC, optimal control
2. **Additional Zones**: Scales to 20+ zones
3. **Equipment Variants**: Multiple AHUs, FPBs, VRF
4. **Integration**: BACnet, MQTT, web dashboards

## Success Criteria

**Functional**:
✅ All controllers implemented and tested
✅ 24-hour simulation successful
✅ All modes operational
✅ Temperature and airflow within tolerance

**Quality**:
✅ 90%+ code coverage
✅ Strict type checking passes
✅ Complete documentation
✅ Validation vs. Modelica reference

**Performance**:
✅ Real-time simulation capability
✅ Control stability demonstrated
✅ Energy savings validated
✅ Comfort requirements met

## Next Steps

1. **Review and Approve**: Architecture review by project lead
2. **Begin Phase 1**: Set up structure and elementary blocks
3. **Create Project Board**: Track progress through phases
4. **Set Up CI/CD**: Automated testing pipeline

## Documentation Deliverables

**Technical**:
- Architecture document (complete)
- API reference (auto-generated)
- Control sequence specification
- CDL-JSON schema

**User**:
- README with quick start
- Installation guide
- User guide
- Troubleshooting guide

**Tutorials** (Jupyter notebooks):
- System overview
- Running simulations
- Custom scenarios
- Performance analysis
- Control tuning

## References

1. **ASHRAE (2006)**: "Sequences of Operation for Common HVAC Systems"
2. **Buildings Library**: Modelica implementation at LBNL
3. **CDL Specification**: https://obc.lbl.gov/specification/cdl.html
4. **Python CDL Architecture**: `/docs/architecture/`

---

**Complete Architecture Document**: `/docs/vav_reheat_architecture.md`

**Status**: Architecture design COMPLETE - Ready for implementation

**Estimated Timeline**: 10 weeks from start to validated system

**Primary Architect**: System Architect Agent
