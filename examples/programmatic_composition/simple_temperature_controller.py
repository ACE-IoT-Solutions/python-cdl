"""Simple Temperature Controller - Programmatic CDL Composition Example.

This example demonstrates building a basic PI temperature controller
programmatically using Pydantic models and exporting to CDL-JSON.

The controller maintains room temperature by:
1. Reading temperature sensor
2. Computing error vs setpoint
3. PI control algorithm
4. Limiting output
5. Driving heating valve
"""

import json
from pathlib import Path

from python_cdl.models.blocks import CompositeBlock, ElementaryBlock
from python_cdl.models.connections import Connection
from python_cdl.models.connectors import RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum


def create_pi_controller() -> ElementaryBlock:
    """Create a PI controller block with anti-windup.

    CDL Type: Buildings.Controls.OBC.CDL.Continuous.LimPID
    """
    return ElementaryBlock(
        name="PI_Controller",
        block_type="Buildings.Controls.OBC.CDL.Continuous.LimPID",
        category="elementary",
        description="PI controller with output limiter for temperature control",
        inputs=[
            RealInput(
                name="u_s",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Setpoint temperature"
            ),
            RealInput(
                name="u_m",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Measured temperature"
            ),
        ],
        outputs=[
            RealOutput(
                name="y",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Control signal (0-1)"
            ),
        ],
        parameters=[
            Parameter(
                name="controllerType",
                type=CDLTypeEnum.INTEGER,
                value=2,  # PI control
                description="Type of controller (1=P, 2=PI, 3=PID)"
            ),
            Parameter(
                name="k",
                type=CDLTypeEnum.REAL,
                value=0.5,
                unit="1",
                description="Proportional gain"
            ),
            Parameter(
                name="Ti",
                type=CDLTypeEnum.REAL,
                value=60.0,
                unit="s",
                quantity="Time",
                description="Integral time constant"
            ),
            Parameter(
                name="yMax",
                type=CDLTypeEnum.REAL,
                value=1.0,
                unit="1",
                description="Maximum output"
            ),
            Parameter(
                name="yMin",
                type=CDLTypeEnum.REAL,
                value=0.0,
                unit="1",
                description="Minimum output"
            ),
        ],
    )


def create_temperature_sensor() -> ElementaryBlock:
    """Create a temperature sensor block with noise filtering.

    CDL Type: Buildings.Controls.OBC.CDL.Continuous.Filter
    """
    return ElementaryBlock(
        name="TempSensor",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Filter",
        category="elementary",
        description="Temperature sensor with first-order filter",
        inputs=[
            RealInput(
                name="u",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Raw temperature measurement"
            ),
        ],
        outputs=[
            RealOutput(
                name="y",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Filtered temperature"
            ),
        ],
        parameters=[
            Parameter(
                name="T",
                type=CDLTypeEnum.REAL,
                value=10.0,
                unit="s",
                quantity="Time",
                description="Filter time constant"
            ),
        ],
    )


def create_valve_actuator() -> ElementaryBlock:
    """Create a valve actuator with rate limiting.

    CDL Type: Buildings.Controls.OBC.CDL.Continuous.LimRateLimiter
    """
    return ElementaryBlock(
        name="HeatingValve",
        block_type="Buildings.Controls.OBC.CDL.Continuous.LimRateLimiter",
        category="elementary",
        description="Heating valve actuator with rate limiting",
        inputs=[
            RealInput(
                name="u",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Desired valve position"
            ),
        ],
        outputs=[
            RealOutput(
                name="y",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Actual valve position"
            ),
        ],
        parameters=[
            Parameter(
                name="riseRate",
                type=CDLTypeEnum.REAL,
                value=0.1,
                unit="1/s",
                description="Maximum rate of valve opening (per second)"
            ),
            Parameter(
                name="fallRate",
                type=CDLTypeEnum.REAL,
                value=0.1,
                unit="1/s",
                description="Maximum rate of valve closing (per second)"
            ),
        ],
    )


def create_setpoint_source() -> ElementaryBlock:
    """Create a constant setpoint source.

    CDL Type: Buildings.Controls.OBC.CDL.Continuous.Sources.Constant
    """
    return ElementaryBlock(
        name="SetpointSource",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Sources.Constant",
        category="elementary",
        description="Temperature setpoint (21°C = 294.15 K)",
        inputs=[],
        outputs=[
            RealOutput(
                name="y",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Setpoint temperature"
            ),
        ],
        parameters=[
            Parameter(
                name="k",
                type=CDLTypeEnum.REAL,
                value=294.15,  # 21°C in Kelvin
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Constant setpoint value"
            ),
        ],
    )


def create_temperature_control_system() -> CompositeBlock:
    """Create complete temperature control system as composite block."""

    # Create all component blocks
    setpoint = create_setpoint_source()
    sensor = create_temperature_sensor()
    controller = create_pi_controller()
    valve = create_valve_actuator()

    # Create composite system
    system = CompositeBlock(
        name="SimpleTemperatureController",
        block_type="TemperatureControlSystem",
        category="composite",
        description="Simple temperature control system with PI controller",
        inputs=[
            RealInput(
                name="temperature_measurement",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Room temperature sensor input"
            ),
        ],
        outputs=[
            RealOutput(
                name="valve_position",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Heating valve position output"
            ),
        ],
        blocks=[setpoint, sensor, controller, valve],
        connections=[
            # External input -> Sensor
            Connection(
                from_block="temperature_measurement",  # Composite input
                from_output="temperature_measurement",
                to_block="TempSensor",
                to_input="u",
                description="Raw temperature to sensor filter"
            ),
            # Setpoint -> Controller
            Connection(
                from_block="SetpointSource",
                from_output="y",
                to_block="PI_Controller",
                to_input="u_s",
                description="Setpoint to controller"
            ),
            # Sensor -> Controller
            Connection(
                from_block="TempSensor",
                from_output="y",
                to_block="PI_Controller",
                to_input="u_m",
                description="Filtered temperature to controller"
            ),
            # Controller -> Valve
            Connection(
                from_block="PI_Controller",
                from_output="y",
                to_block="HeatingValve",
                to_input="u",
                description="Control signal to valve"
            ),
            # Valve -> External output
            Connection(
                from_block="HeatingValve",
                from_output="y",
                to_block="valve_position",  # Composite output
                to_input="valve_position",
                description="Valve position output"
            ),
        ],
    )

    return system


def export_to_json(block: CompositeBlock, output_path: Path) -> None:
    """Export block to CDL-JSON format."""
    # Use Pydantic's model_dump for JSON serialization
    cdl_json = block.model_dump(mode='json', exclude_none=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(cdl_json, f, indent=2)

    print(f"✓ Exported to {output_path}")
    print(f"  File size: {output_path.stat().st_size:,} bytes")


def print_system_summary(system: CompositeBlock) -> None:
    """Print a summary of the control system."""
    print("\n" + "="*70)
    print(f"Control System: {system.name}")
    print("="*70)
    print(f"\nDescription: {system.description}")
    print(f"\nType: {system.block_type}")
    print(f"Category: {system.category}")

    print(f"\nInputs ({len(system.inputs)}):")
    for inp in system.inputs:
        print(f"  • {inp.name}: {inp.type} [{inp.unit}] - {inp.description}")

    print(f"\nOutputs ({len(system.outputs)}):")
    for out in system.outputs:
        print(f"  • {out.name}: {out.type} [{out.unit}] - {out.description}")

    print(f"\nInternal Blocks ({len(system.blocks)}):")
    for block in system.blocks:
        print(f"  • {block.name} ({block.block_type})")
        if block.parameters:
            for param in block.parameters:
                print(f"      - {param.name} = {param.value} {param.unit or ''}")

    print(f"\nConnections ({len(system.connections)}):")
    for conn in system.connections:
        print(f"  • {conn.from_block}.{conn.from_output} → {conn.to_block}.{conn.to_input}")

    print("\n" + "="*70 + "\n")


def main():
    """Main execution function."""
    print("\n🏗️  Building Simple Temperature Controller Programmatically")
    print("="*70)

    # Create the control system
    print("\n1. Creating control system components...")
    system = create_temperature_control_system()
    print(f"   ✓ Created {len(system.blocks)} blocks")
    print(f"   ✓ Configured {len(system.connections)} connections")

    # Print summary
    print("\n2. System summary:")
    print_system_summary(system)

    # Export to JSON
    print("3. Exporting to CDL-JSON format...")
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "simple_temp_controller.json"
    export_to_json(system, output_file)

    # Validation
    print("\n4. Validating structure...")
    from python_cdl.validators import BlockValidator

    validator = BlockValidator()
    result = validator.validate(system)

    # Handle both tuple and ValidationResult returns
    if hasattr(result, 'is_valid'):
        is_valid = result.is_valid
        errors = result.errors if hasattr(result, 'errors') else []
    else:
        is_valid, errors = result

    if is_valid:
        print("   ✓ Block structure is valid")
    else:
        print(f"   ✗ Validation errors: {errors}")
        return

    # Round-trip test
    print("\n5. Testing round-trip import...")
    from python_cdl.parser import CDLParser

    parser = CDLParser()
    with open(output_file) as f:
        json_data = json.load(f)
    reimported = parser.parse(json_data)
    print(f"   ✓ Successfully re-imported {reimported.name}")

    print("\n✅ Example completed successfully!")
    print(f"\nGenerated file: {output_file}")
    print("\nNext steps:")
    print("  • Open the JSON file to see the CDL structure")
    print("  • Modify parameters and re-run to experiment")
    print("  • Use this as a template for your own controllers")


if __name__ == "__main__":
    main()
