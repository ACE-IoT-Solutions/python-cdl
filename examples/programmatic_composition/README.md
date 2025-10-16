# Programmatic Control Composition Example

This example demonstrates how to build CDL control programs programmatically using Pydantic models and export them to CDL-JSON format.

## Overview

Instead of parsing existing CDL-JSON files, this example shows how to:
1. Create elementary blocks using Python code
2. Compose blocks into composite systems
3. Define connections between blocks
4. Set parameters and configure inputs/outputs
5. Export the complete control program to CDL-JSON

## Examples Included

### 1. Simple Temperature Controller (`simple_temperature_controller.py`)
- Basic PI controller with setpoint
- Temperature sensor input
- Valve output
- Demonstrates elementary block composition

### 2. Room Temperature Control (`room_control_system.py`)
- Complete room control with heating and cooling
- Switching logic between modes
- Multiple interconnected blocks
- Demonstrates composite block creation

### 3. Economizer Controller (`economizer_controller.py`)
- Complex multi-input controller
- Outdoor air temperature comparison
- Damper position calculation
- Real-world HVAC application

## Key Concepts

### Building Blocks Programmatically

```python
from python_cdl.models.blocks import ElementaryBlock
from python_cdl.models.connectors import RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum

# Create a PI controller block
pi_controller = ElementaryBlock(
    name="PI_TempControl",
    block_type="LimPID",
    category="elementary",
    inputs=[
        RealInput(name="setpoint", type=CDLTypeEnum.REAL, unit="K"),
        RealInput(name="measurement", type=CDLTypeEnum.REAL, unit="K")
    ],
    outputs=[
        RealOutput(name="control_output", type=CDLTypeEnum.REAL, unit="1")
    ],
    parameters=[
        Parameter(name="k", type=CDLTypeEnum.REAL, value=0.5),
        Parameter(name="Ti", type=CDLTypeEnum.REAL, value=60.0)
    ]
)
```

### Composing Systems

```python
from python_cdl.models.blocks import CompositeBlock
from python_cdl.models.connections import Connection

# Create composite system
system = CompositeBlock(
    name="TemperatureControlSystem",
    block_type="CompositeController",
    category="composite",
    blocks=[sensor, controller, actuator],
    connections=[
        Connection(
            from_block="sensor",
            from_port="temperature",
            to_block="controller",
            to_port="measurement"
        )
    ]
)
```

### Exporting to CDL-JSON

```python
import json

# Export using Pydantic's model_dump
cdl_json = system.model_dump(mode='json', exclude_none=True)

# Save to file
with open('control_system.json', 'w') as f:
    json.dump(cdl_json, f, indent=2)
```

## Running the Examples

Each example can be run independently:

```bash
# Simple temperature controller
uv run python simple_temperature_controller.py

# Room control system
uv run python room_control_system.py

# Economizer controller
uv run python economizer_controller.py
```

Each script will:
1. Build the control system programmatically
2. Print the structure to console
3. Export to a CDL-JSON file
4. Validate the exported JSON can be re-imported

## File Structure

```
programmatic_composition/
├── README.md                          # This file
├── simple_temperature_controller.py   # Basic PI control example
├── room_control_system.py             # Multi-mode room control
├── economizer_controller.py           # Complex HVAC controller
├── output/                            # Generated CDL-JSON files
│   ├── simple_temp_controller.json
│   ├── room_control_system.json
│   └── economizer_controller.json
└── utils.py                           # Helper functions for export/validation
```

## Benefits of Programmatic Composition

1. **Type Safety** - Pydantic validates all fields at creation time
2. **Reusability** - Create functions that generate common patterns
3. **Version Control** - Code is easier to diff and track than JSON
4. **Testing** - Unit test control logic before deployment
5. **Documentation** - Self-documenting with Python docstrings
6. **Flexibility** - Generate controls dynamically based on configuration

## Integration with Python CDL

The programmatically created blocks are fully compatible with:
- `ExecutionContext` for simulation
- `BlockValidator` for validation
- `GraphValidator` for connection checking
- JSON parser for round-trip import/export

## Next Steps

- Modify the examples to create your own controllers
- Combine patterns from multiple examples
- Export and deploy to real control systems
- Use as templates for code generation tools
