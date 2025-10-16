"""Example usage of VAV box controllers for a 5-zone building.

This script demonstrates:
1. Setting up zone controllers for all 5 zones
2. Simulating zone temperature changes
3. Computing control outputs (damper and reheat valve positions)
4. Generating CDL block representations
"""

import json
from typing import Dict

from .zone_controller import VAVBoxController, create_vav_controller_block
from .zone_models import ZoneState, ZoneType, get_zone_config


def simulate_zone_controllers():
    """Simulate VAV box controllers for all 5 zones."""

    print("=" * 80)
    print("VAV Box Controller Simulation - 5 Zone Building")
    print("=" * 80)
    print()

    # Initialize controllers for all zones
    zones = {}
    controllers = {}

    for zone_type in ZoneType:
        config = get_zone_config(zone_type)
        controllers[zone_type] = VAVBoxController(config)

        # Initialize zone state with varying temperatures
        if zone_type == ZoneType.CORRIDOR:
            initial_temp = 23.5  # Comfortable interior zone
        elif zone_type == ZoneType.SOUTH:
            initial_temp = 26.5  # Hot due to solar gain
        elif zone_type == ZoneType.NORTH:
            initial_temp = 22.0  # Cooler, less solar
        elif zone_type == ZoneType.EAST:
            initial_temp = 25.0  # Morning sun
        else:  # WEST
            initial_temp = 25.5  # Afternoon sun

        zones[zone_type] = ZoneState(
            room_temp=initial_temp,
            supply_air_temp=13.0,  # Typical supply air temp
        )

    print("Initial Zone Conditions:")
    print("-" * 80)
    for zone_type, state in zones.items():
        config = controllers[zone_type].config
        print(f"{zone_type.value.upper():12s} | Temp: {state.room_temp:5.1f}°C | "
              f"Cooling SP: {config.cooling_setpoint:5.1f}°C | "
              f"Heating SP: {config.heating_setpoint:5.1f}°C")
    print()

    # Simulate control for multiple time steps
    print("Control Simulation (first 10 seconds):")
    print("-" * 80)

    dt = 1.0  # 1 second time step
    num_steps = 10

    for step in range(num_steps):
        print(f"\nTime = {step} seconds:")
        print(f"{'Zone':<12} | {'Temp':<8} | {'Damper':<8} | {'Reheat':<8} | {'Airflow':<10} | {'Mode':<10}")
        print("-" * 80)

        for zone_type in ZoneType:
            controller = controllers[zone_type]
            state = zones[zone_type]
            config = controller.config

            # Update zone state with controller
            state = controller.update_state(state, dt=dt)
            zones[zone_type] = state

            # Determine operating mode
            if state.room_temp > config.cooling_setpoint + config.deadband:
                mode = "COOLING"
            elif state.room_temp < config.heating_setpoint:
                mode = "HEATING"
            else:
                mode = "DEADBAND"

            print(f"{zone_type.value:<12} | {state.room_temp:6.2f}°C | "
                  f"{state.damper_position:6.2%} | {state.reheat_valve_position:6.2%} | "
                  f"{state.airflow:7.3f} m³/s | {mode:<10}")

            # Simulate simple temperature response
            # (In real system, this would be based on thermal model)
            if state.damper_position > 0.3:
                # Cooling effect from increased airflow
                state.room_temp -= 0.05 * state.damper_position
            if state.reheat_valve_position > 0.1:
                # Heating effect from reheat coil
                state.room_temp += 0.03 * state.reheat_valve_position

    print("\n" + "=" * 80)
    print("Control Summary After 10 Seconds:")
    print("=" * 80)

    for zone_type in ZoneType:
        state = zones[zone_type]
        config = controllers[zone_type].config

        print(f"\n{zone_type.value.upper()} Zone:")
        print(f"  Temperature:           {state.room_temp:6.2f}°C")
        print(f"  Cooling Setpoint:      {config.cooling_setpoint:6.2f}°C")
        print(f"  Heating Setpoint:      {config.heating_setpoint:6.2f}°C")
        print(f"  Damper Position:       {state.damper_position:6.2%}")
        print(f"  Reheat Valve:          {state.reheat_valve_position:6.2%}")
        print(f"  Airflow:               {state.airflow:6.3f} m³/s")
        print(f"  Cooling Demand:        {state.cooling_demand:6.2%}")
        print(f"  Heating Demand:        {state.heating_demand:6.2%}")

    return zones, controllers


def generate_cdl_blocks():
    """Generate CDL block representations for all zone controllers."""

    print("\n" + "=" * 80)
    print("Generating CDL Block Representations")
    print("=" * 80)
    print()

    for zone_type in ZoneType:
        config = get_zone_config(zone_type)
        block = create_vav_controller_block(config)

        # Convert to JSON for inspection
        block_dict = block.model_dump()

        # Save to file
        output_file = f"/Users/acedrew/aceiot-projects/python-cdl/examples/vav_reheat/{zone_type.value}_controller.json"
        with open(output_file, 'w') as f:
            json.dump(block_dict, f, indent=2)

        print(f"Generated CDL block for {zone_type.value.upper()} zone:")
        print(f"  Name: {block.name}")
        print(f"  Type: {block.block_type}")
        print(f"  Inputs: {len(block.inputs)}")
        print(f"  Outputs: {len(block.outputs)}")
        print(f"  Parameters: {len(block.parameters)}")
        print(f"  Saved to: {output_file}")
        print()


def demonstrate_control_modes():
    """Demonstrate different control modes (cooling, heating, deadband)."""

    print("\n" + "=" * 80)
    print("Control Mode Demonstrations")
    print("=" * 80)

    config = get_zone_config(ZoneType.SOUTH)
    controller = VAVBoxController(config)

    # Test scenarios
    scenarios = [
        {
            "name": "Hot Room - Cooling Mode",
            "room_temp": 27.0,
            "supply_temp": 13.0,
            "expected_mode": "Cooling (high damper, no reheat)"
        },
        {
            "name": "Comfortable - Deadband Mode",
            "room_temp": 23.0,
            "supply_temp": 13.0,
            "expected_mode": "Deadband (min airflow, minimal reheat)"
        },
        {
            "name": "Cold Room - Heating Mode",
            "room_temp": 19.0,
            "supply_temp": 13.0,
            "expected_mode": "Heating (min airflow, active reheat)"
        },
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Room Temperature: {scenario['room_temp']}°C")
        print(f"  Supply Air Temperature: {scenario['supply_temp']}°C")
        print(f"  Expected: {scenario['expected_mode']}")

        # Reset controller for clean test
        controller.reset()

        # Run for a few steps to see response
        state = ZoneState(
            room_temp=scenario['room_temp'],
            supply_air_temp=scenario['supply_temp']
        )

        for i in range(5):
            state = controller.update_state(state, dt=1.0)

        print(f"  Actual Results (after 5 seconds):")
        print(f"    Damper Position: {state.damper_position:6.2%}")
        print(f"    Reheat Valve:    {state.reheat_valve_position:6.2%}")
        print(f"    Airflow:         {state.airflow:6.3f} m³/s")
        print(f"    Cooling Demand:  {state.cooling_demand:6.2%}")
        print(f"    Heating Demand:  {state.heating_demand:6.2%}")


if __name__ == "__main__":
    # Run main simulation
    zones, controllers = simulate_zone_controllers()

    # Generate CDL blocks
    generate_cdl_blocks()

    # Demonstrate control modes
    demonstrate_control_modes()

    print("\n" + "=" * 80)
    print("Simulation Complete!")
    print("=" * 80)
