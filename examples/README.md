# Python CDL Examples

This directory contains example implementations demonstrating the Python CDL library for building automation control sequences.

## Examples

### 1. 24-Hour P-Controller Simulation

**File**: `cdl_controller_simulation.ipynb`

**Description**: Interactive Jupyter notebook demonstrating a complete 24-hour simulation of a proportional controller with output limiting.

**Control Sequence**: `CustomPWithLimiter` from OBC CDL specification
- **Type**: Composite block (P controller + Min limiter)
- **Application**: Zone temperature control with heating valve
- **Formula**: `y = min(yMax, k × e)` where `e = setpoint - measurement`

**Features**:
- ✅ Load CDL-JSON control sequence
- ✅ Validate CDL compliance
- ✅ Execute 288 time steps (5-minute intervals)
- ✅ Realistic zone temperature dynamics
- ✅ Occupied/unoccupied scheduling
- ✅ Performance metrics calculation
- ✅ Comprehensive visualization (3 plots)

**Scenario**:
- **Building Type**: Office building
- **Control Points**: Single zone temperature
- **Schedule**: Occupied 8am-6pm (22°C), Unoccupied (18°C)
- **Outside Temperature**: 5°C - 15°C daily variation
- **Duration**: 24 hours
- **Time Step**: 5 minutes

**How to Run**:
```bash
# Navigate to examples directory
cd examples

# Launch Jupyter notebook
uv run jupyter notebook cdl_controller_simulation.ipynb

# Or run with JupyterLab
uv run jupyter lab cdl_controller_simulation.ipynb
```

**Expected Outputs**:
- Zone temperature tracking setpoint
- Control output (heating valve %) over 24 hours
- Control error analysis
- Performance metrics (MAE, time at setpoint, energy usage)
- PNG visualization: `cdl_controller_24h_simulation.png`

---

### 2. CDL-JSON Control Sequence

**File**: `p_controller_limiter.json`

**Description**: CDL-JSON representation of the proportional controller with limiter used in the simulation notebook.

**Block Structure**:
```json
{
  "name": "CustomPWithLimiter",
  "type": "composite",
  "inputs": ["yMax", "e"],
  "outputs": ["y"],
  "parameters": [{"name": "k", "value": 0.5}],
  "components": [
    {"name": "gain", "type": "elementary", "blockType": "CDL.Reals.MultiplyByParameter"},
    {"name": "minValue", "type": "elementary", "blockType": "CDL.Reals.Min"}
  ]
}
```

**CDL Compliance**:
- ✅ Synchronous data flow
- ✅ Acyclic dependency graph
- ✅ Type-safe connections
- ✅ Elementary blocks from CDL standard library

**Use Cases**:
1. **Temperature Control**: Zone heating with valve saturation protection
2. **Damper Control**: Airflow modulation with position limits
3. **General Purpose**: Any proportional control with output constraints

---

## Running Examples

### Prerequisites

```bash
# Install Python CDL library with development dependencies
uv add python-cdl
uv add matplotlib numpy ipykernel --dev
```

### Interactive Notebook

```bash
# Start Jupyter in examples directory
cd examples
uv run jupyter notebook

# Open: cdl_controller_simulation.ipynb
```

### Programmatic Usage

```python
from python_cdl import CDLParser, ExecutionContext

# Load control sequence
parser = CDLParser()
controller = parser.parse_file("examples/p_controller_limiter.json")

# Execute
context = ExecutionContext(controller)
context.set_input("e", 2.0)  # Error: +2°C
context.set_input("yMax", 100.0)  # Limit: 100%
context.step()

output = context.get_output("y")  # Result: min(100, 0.5 * 2.0) = 1.0%
```

---

## Future Examples

### Planned Additions

1. **VAV Reheat Controller** (ASHRAE 2006 Guideline 36)
   - Multi-zone control
   - Finite state machine (occupied/unoccupied modes)
   - Economizer logic
   - Supply fan VFD control
   - Reheat coil sequencing

2. **PID Temperature Controller**
   - Full PID with integral and derivative action
   - Anti-windup protection
   - Setpoint tracking

3. **Economizer Control Sequence**
   - Outside air damper modulation
   - Enthalpy-based free cooling
   - Minimum ventilation requirements

4. **Demand-Controlled Ventilation**
   - CO₂-based airflow control
   - Occupancy sensing integration
   - Variable air volume modulation

5. **Lighting Control**
   - Daylight harvesting
   - Occupancy detection
   - Scene control

---

## Creating Your Own Examples

### 1. Start with CDL-JSON

Create a CDL-JSON file defining your control sequence:

```json
{
  "name": "MyController",
  "type": "composite",
  "inputs": [...],
  "outputs": [...],
  "parameters": [...],
  "components": [...],
  "connections": [...]
}
```

### 2. Validate with Python CDL

```python
from python_cdl import CDLParser, BlockValidator

parser = CDLParser()
controller = parser.parse_file("my_controller.json")

validator = BlockValidator()
result = validator.validate(controller)

if not result.is_valid:
    for error in result.errors:
        print(f"ERROR: {error.message}")
```

### 3. Execute with Simulation

```python
from python_cdl import ExecutionContext
import numpy as np

context = ExecutionContext(controller)

# Time series simulation
time_steps = 100
outputs = []

for t in range(time_steps):
    # Set inputs based on time
    context.set_input("input1", ...)

    # Execute
    context.step()

    # Collect outputs
    outputs.append(context.get_output("output1"))

# Analyze results
outputs = np.array(outputs)
```

### 4. Visualize Results

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(outputs)
plt.xlabel("Time Step")
plt.ylabel("Control Output")
plt.title("My Control Sequence Performance")
plt.grid(True)
plt.show()
```

---

## CDL Resources

### Official Documentation
- **CDL Specification**: https://obc.lbl.gov/specification/cdl.html
- **Buildings Library**: https://simulationresearch.lbl.gov/modelica/
- **CDL Reference**: https://obc.lbl.gov/specification/cdl/latest/help/CDL.html

### Standards
- **ASHRAE 231P**: Controls Description Language
- **ASHRAE Guideline 36**: High-Performance Sequences of Operation for HVAC Systems
- **ASHRAE Standard 223**: Semantic Data Standard for Building Systems

### Tools
- **modelica-json**: CDL to JSON translator (https://github.com/lbl-srg/modelica-json)
- **Python CDL**: This library (Python implementation)
- **OpenModelica**: Modelica simulation environment

---

## Support

For questions or issues:
1. Check the main project documentation: `/docs/API_DOCUMENTATION.md`
2. Review architecture docs: `/docs/architecture/`
3. Examine test cases: `/tests/`

---

## License

Examples are distributed under the same MIT license as the Python CDL library.
