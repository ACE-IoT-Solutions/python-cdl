"""Room Control System - Advanced Programmatic CDL Composition.

This example demonstrates a more complex control system with:
- Dual-mode operation (heating and cooling)
- Mode switching logic
- Multiple interconnected controllers
- Realistic HVAC control sequences

The system automatically switches between heating and cooling based
on room temperature and setpoints.
"""

import json
from pathlib import Path

from python_cdl.models.blocks import CompositeBlock, ElementaryBlock
from python_cdl.models.connections import Connection
from python_cdl.models.connectors import BooleanInput, BooleanOutput, RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.types import CDLTypeEnum


def create_heating_controller() -> ElementaryBlock:
    """Create PI controller for heating mode."""
    return ElementaryBlock(
        name="HeatingController",
        block_type="Buildings.Controls.OBC.CDL.Continuous.LimPID",
        category="elementary",
        description="PI controller for heating valve",
        inputs=[
            RealInput(name="u_s", type=CDLTypeEnum.REAL, unit="K"),
            RealInput(name="u_m", type=CDLTypeEnum.REAL, unit="K"),
        ],
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="1", min=0.0, max=1.0),
        ],
        parameters=[
            Parameter(name="controllerType", type=CDLTypeEnum.INTEGER, value=2),
            Parameter(name="k", type=CDLTypeEnum.REAL, value=0.5),
            Parameter(name="Ti", type=CDLTypeEnum.REAL, value=120.0, unit="s"),
            Parameter(name="yMax", type=CDLTypeEnum.REAL, value=1.0),
            Parameter(name="yMin", type=CDLTypeEnum.REAL, value=0.0),
            Parameter(name="reverseActing", type=CDLTypeEnum.BOOLEAN, value=True),
        ],
    )


def create_cooling_controller() -> ElementaryBlock:
    """Create PI controller for cooling mode."""
    return ElementaryBlock(
        name="CoolingController",
        block_type="Buildings.Controls.OBC.CDL.Continuous.LimPID",
        category="elementary",
        description="PI controller for cooling valve",
        inputs=[
            RealInput(name="u_s", type=CDLTypeEnum.REAL, unit="K"),
            RealInput(name="u_m", type=CDLTypeEnum.REAL, unit="K"),
        ],
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="1", min=0.0, max=1.0),
        ],
        parameters=[
            Parameter(name="controllerType", type=CDLTypeEnum.INTEGER, value=2),
            Parameter(name="k", type=CDLTypeEnum.REAL, value=0.8),
            Parameter(name="Ti", type=CDLTypeEnum.REAL, value=90.0, unit="s"),
            Parameter(name="yMax", type=CDLTypeEnum.REAL, value=1.0),
            Parameter(name="yMin", type=CDLTypeEnum.REAL, value=0.0),
            Parameter(name="reverseActing", type=CDLTypeEnum.BOOLEAN, value=False),
        ],
    )


def create_mode_selector() -> ElementaryBlock:
    """Create mode selection logic based on temperature and setpoints."""
    return ElementaryBlock(
        name="ModeSelector",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Hysteresis",
        category="elementary",
        description="Select heating/cooling mode with hysteresis",
        inputs=[
            RealInput(
                name="u",
                type=CDLTypeEnum.REAL,
                unit="K",
                description="Temperature error (measured - setpoint)"
            ),
        ],
        outputs=[
            BooleanOutput(
                name="y",
                type=CDLTypeEnum.BOOLEAN,
                description="True = heating mode, False = cooling mode"
            ),
        ],
        parameters=[
            Parameter(
                name="uLow",
                type=CDLTypeEnum.REAL,
                value=-1.0,
                unit="K",
                description="Lower threshold (switch to heating)"
            ),
            Parameter(
                name="uHigh",
                type=CDLTypeEnum.REAL,
                value=1.0,
                unit="K",
                description="Upper threshold (switch to cooling)"
            ),
        ],
    )


def create_subtractor() -> ElementaryBlock:
    """Create subtractor for error calculation."""
    return ElementaryBlock(
        name="ErrorCalculator",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Add",
        category="elementary",
        description="Calculate temperature error",
        inputs=[
            RealInput(name="u1", type=CDLTypeEnum.REAL, unit="K"),
            RealInput(name="u2", type=CDLTypeEnum.REAL, unit="K"),
        ],
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="K"),
        ],
        parameters=[
            Parameter(name="k1", type=CDLTypeEnum.REAL, value=1.0),
            Parameter(name="k2", type=CDLTypeEnum.REAL, value=-1.0),  # Subtract
        ],
    )


def create_switch() -> ElementaryBlock:
    """Create switch to select between heating and cooling outputs."""
    return ElementaryBlock(
        name="OutputSwitch",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Switch",
        category="elementary",
        description="Switch between heating and cooling valve commands",
        inputs=[
            RealInput(name="u1", type=CDLTypeEnum.REAL, unit="1", description="Heating signal"),
            RealInput(name="u2", type=CDLTypeEnum.REAL, unit="1", description="Cooling signal"),
            BooleanInput(name="u3", type=CDLTypeEnum.BOOLEAN, description="Mode selection"),
        ],
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="1", min=0.0, max=1.0),
        ],
    )


def create_heating_setpoint() -> ElementaryBlock:
    """Create heating setpoint source (20°C)."""
    return ElementaryBlock(
        name="HeatingSetpoint",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Sources.Constant",
        category="elementary",
        description="Heating mode setpoint",
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="K"),
        ],
        parameters=[
            Parameter(name="k", type=CDLTypeEnum.REAL, value=293.15, unit="K"),  # 20°C
        ],
    )


def create_cooling_setpoint() -> ElementaryBlock:
    """Create cooling setpoint source (24°C)."""
    return ElementaryBlock(
        name="CoolingSetpoint",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Sources.Constant",
        category="elementary",
        description="Cooling mode setpoint",
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="K"),
        ],
        parameters=[
            Parameter(name="k", type=CDLTypeEnum.REAL, value=297.15, unit="K"),  # 24°C
        ],
    )


def create_deadband_setpoint() -> ElementaryBlock:
    """Create deadband center setpoint (22°C)."""
    return ElementaryBlock(
        name="DeadbandSetpoint",
        block_type="Buildings.Controls.OBC.CDL.Continuous.Sources.Constant",
        category="elementary",
        description="Deadband center for mode switching",
        outputs=[
            RealOutput(name="y", type=CDLTypeEnum.REAL, unit="K"),
        ],
        parameters=[
            Parameter(name="k", type=CDLTypeEnum.REAL, value=295.15, unit="K"),  # 22°C
        ],
    )


def create_room_control_system() -> CompositeBlock:
    """Create complete dual-mode room control system."""

    # Create all blocks
    heating_sp = create_heating_setpoint()
    cooling_sp = create_cooling_setpoint()
    deadband_sp = create_deadband_setpoint()
    error_calc = create_subtractor()
    mode_selector = create_mode_selector()
    heating_ctrl = create_heating_controller()
    cooling_ctrl = create_cooling_controller()
    output_switch = create_switch()

    # Create composite system
    system = CompositeBlock(
        name="RoomControlSystem",
        block_type="DualModeRoomController",
        category="composite",
        description=(
            "Automatic dual-mode room temperature control system. "
            "Switches between heating and cooling based on temperature. "
            "Deadband prevents rapid mode switching."
        ),
        inputs=[
            RealInput(
                name="room_temperature",
                type=CDLTypeEnum.REAL,
                unit="K",
                quantity="ThermodynamicTemperature",
                description="Measured room temperature"
            ),
        ],
        outputs=[
            RealOutput(
                name="heating_valve",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Heating valve position (0-1)"
            ),
            RealOutput(
                name="cooling_valve",
                type=CDLTypeEnum.REAL,
                unit="1",
                min=0.0,
                max=1.0,
                description="Cooling valve position (0-1)"
            ),
            BooleanOutput(
                name="heating_mode",
                type=CDLTypeEnum.BOOLEAN,
                description="True when in heating mode"
            ),
        ],
        blocks=[
            heating_sp,
            cooling_sp,
            deadband_sp,
            error_calc,
            mode_selector,
            heating_ctrl,
            cooling_ctrl,
            output_switch,
        ],
        connections=[
            # Calculate error for mode selection
            Connection(
                from_block="room_temperature",
                from_output="room_temperature",
                to_block="ErrorCalculator",
                to_input="u1",
                description="Room temp to error calculator"
            ),
            Connection(
                from_block="DeadbandSetpoint",
                from_output="y",
                to_block="ErrorCalculator",
                to_input="u2",
                description="Deadband setpoint to error calculator"
            ),
            # Mode selection
            Connection(
                from_block="ErrorCalculator",
                from_output="y",
                to_block="ModeSelector",
                to_input="u",
                description="Temperature error to mode selector"
            ),
            # Heating controller
            Connection(
                from_block="HeatingSetpoint",
                from_output="y",
                to_block="HeatingController",
                to_input="u_s",
                description="Heating setpoint"
            ),
            Connection(
                from_block="room_temperature",
                from_output="room_temperature",
                to_block="HeatingController",
                to_input="u_m",
                description="Room temp to heating controller"
            ),
            # Cooling controller
            Connection(
                from_block="CoolingSetpoint",
                from_output="y",
                to_block="CoolingController",
                to_input="u_s",
                description="Cooling setpoint"
            ),
            Connection(
                from_block="room_temperature",
                from_output="room_temperature",
                to_block="CoolingController",
                to_input="u_m",
                description="Room temp to cooling controller"
            ),
            # Output switch
            Connection(
                from_block="HeatingController",
                from_output="y",
                to_block="OutputSwitch",
                to_input="u1",
                description="Heating output to switch"
            ),
            Connection(
                from_block="CoolingController",
                from_output="y",
                to_block="OutputSwitch",
                to_input="u2",
                description="Cooling output to switch"
            ),
            Connection(
                from_block="ModeSelector",
                from_output="y",
                to_block="OutputSwitch",
                to_input="u3",
                description="Mode to switch"
            ),
            # Outputs
            Connection(
                from_block="HeatingController",
                from_output="y",
                to_block="heating_valve",
                to_input="heating_valve",
                description="Heating valve output"
            ),
            Connection(
                from_block="CoolingController",
                from_output="y",
                to_block="cooling_valve",
                to_input="cooling_valve",
                description="Cooling valve output"
            ),
            Connection(
                from_block="ModeSelector",
                from_output="y",
                to_block="heating_mode",
                to_input="heating_mode",
                description="Mode indicator output"
            ),
        ],
    )

    return system


def main():
    """Main execution."""
    print("\n🏗️  Building Room Control System Programmatically")
    print("="*70)

    # Create system
    print("\n1. Creating dual-mode control system...")
    system = create_room_control_system()
    print(f"   ✓ Created {len(system.blocks)} blocks")
    print(f"   ✓ Configured {len(system.connections)} connections")

    # Print summary
    print(f"\n2. System: {system.name}")
    print(f"   {system.description}")
    print(f"\n   Inputs: {', '.join(i.name for i in system.inputs)}")
    print(f"   Outputs: {', '.join(o.name for o in system.outputs)}")
    print(f"\n   Control Modes:")
    print("   • Heating: T < 20°C (293.15 K)")
    print("   • Deadband: 20°C < T < 24°C")
    print("   • Cooling: T > 24°C (297.15 K)")
    print("   • Hysteresis: ±1°C to prevent rapid switching")

    # Export
    print("\n3. Exporting to CDL-JSON...")
    output_dir = Path(__file__).parent / "output"
    output_file = output_dir / "room_control_system.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    cdl_json = system.model_dump(mode='json', exclude_none=True)

    with open(output_file, 'w') as f:
        json.dump(cdl_json, f, indent=2)

    print(f"   ✓ Exported to {output_file}")
    print(f"   File size: {output_file.stat().st_size:,} bytes")

    # Validate
    print("\n4. Validating...")
    from python_cdl.validators import BlockValidator, GraphValidator

    block_validator = BlockValidator()
    graph_validator = GraphValidator()

    result = block_validator.validate(system)
    if hasattr(result, 'is_valid'):
        is_valid = result.is_valid
        errors = result.errors if hasattr(result, 'errors') else []
    else:
        is_valid, errors = result

    if is_valid:
        print("   ✓ Block structure is valid")
    else:
        print(f"   ✗ Block validation errors: {errors}")
        return

    result = graph_validator.validate(system)
    if hasattr(result, 'is_valid'):
        is_valid = result.is_valid
        errors = result.errors if hasattr(result, 'errors') else []
    else:
        is_valid, errors = result

    if is_valid:
        print("   ✓ Connection graph is valid (no cycles)")
    else:
        print(f"   ⚠ Graph validation: {errors}")

    print("\n✅ Example completed successfully!")
    print(f"\nGenerated file: {output_file}")
    print("\nKey features demonstrated:")
    print("  • Multiple elementary blocks composed into system")
    print("  • Mode switching with hysteresis")
    print("  • Dual PI controllers for heating and cooling")
    print("  • Boolean logic for control flow")
    print("  • Complex connection patterns")


if __name__ == "__main__":
    main()
