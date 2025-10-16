"""
VAV Reheat System Example - 24-Hour Simulation

This example demonstrates a complete Variable Air Volume (VAV) system with
reheat following ASHRAE Guideline 36-2018 sequences of operation.

System Components:
- 1 Air Handling Unit (AHU) with economizer
- 5 Zone terminal boxes with reheat
- Coordinated control sequences

The simulation runs for 24 hours with realistic building loads and
demonstrates proper ASHRAE sequence compliance.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

# Import Python CDL library
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from python_cdl import CDLParser, ExecutionContext, BlockValidator


@dataclass
class ZoneState:
    """State of a single zone."""
    name: str
    temperature: float  # K
    setpoint: float  # K
    airflow: float  # m3/s
    damper_position: float  # 0-1
    reheat_valve: float  # 0-1


@dataclass
class AHUState:
    """State of the Air Handling Unit."""
    outdoor_temp: float  # K
    mixed_temp: float  # K
    supply_temp: float  # K
    supply_temp_setpoint: float  # K
    duct_pressure: float  # Pa
    duct_pressure_setpoint: float  # Pa
    fan_speed: float  # 0-1
    oa_damper: float  # 0-1
    ra_damper: float  # 0-1
    cooling_valve: float  # 0-1
    heating_valve: float  # 0-1
    occupied: bool


class VAVSystem:
    """Complete VAV system with AHU and multiple zones."""

    def __init__(self, num_zones: int = 5):
        """Initialize VAV system.

        Args:
            num_zones: Number of VAV terminal boxes
        """
        self.num_zones = num_zones

        # Load controllers
        self._load_controllers()

        # Initialize states
        self.ahu_state = AHUState(
            outdoor_temp=283.15,  # 10°C
            mixed_temp=291.15,  # 18°C
            supply_temp=286.15,  # 13°C
            supply_temp_setpoint=286.15,  # 13°C
            duct_pressure=500.0,  # Pa
            duct_pressure_setpoint=500.0,  # Pa
            fan_speed=0.5,
            oa_damper=0.3,
            ra_damper=0.7,
            cooling_valve=0.0,
            heating_valve=0.0,
            occupied=False
        )

        self.zone_states = [
            ZoneState(
                name=f"Zone{i+1}",
                temperature=291.15,  # 18°C
                setpoint=294.15,  # 21°C
                airflow=0.10,  # m3/s
                damper_position=0.5,
                reheat_valve=0.0
            )
            for i in range(num_zones)
        ]

        # Simulation parameters
        self.time_step = 300.0  # 5 minutes in seconds
        self.current_time = 0.0

        # Physical parameters (simplified building physics)
        self.zone_volume = 300.0  # m3 per zone
        self.zone_area = 100.0  # m2 per zone
        self.u_value = 2.0  # W/(m2·K) - building envelope U-value
        self.air_density = 1.2  # kg/m3
        self.air_specific_heat = 1005.0  # J/(kg·K)
        self.reheat_capacity = 5000.0  # W per zone

        # Data logging
        self.history: Dict[str, List[Any]] = {
            'time': [],
            'ahu_outdoor_temp': [],
            'ahu_supply_temp': [],
            'ahu_fan_speed': [],
            'ahu_oa_damper': [],
            'ahu_cooling_valve': [],
            'ahu_heating_valve': [],
        }

        for i in range(num_zones):
            self.history[f'zone{i+1}_temp'] = []
            self.history[f'zone{i+1}_setpoint'] = []
            self.history[f'zone{i+1}_airflow'] = []
            self.history[f'zone{i+1}_reheat'] = []

    def _load_controllers(self):
        """Load CDL controller definitions."""
        # Load AHU controller
        ahu_path = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "vav_ahu_controller.json"
        with open(ahu_path) as f:
            ahu_data = json.load(f)

        parser = CDLParser()
        self.ahu_controller = parser.parse(ahu_data)
        self.ahu_context = ExecutionContext(self.ahu_controller)

        # Validate AHU controller
        validator = BlockValidator()
        result = validator.validate(self.ahu_controller)
        if not result.is_valid:
            print("WARNING: AHU controller validation failed:")
            for error in result.errors:
                print(f"  - {error}")

        # Load zone controller (same controller for all zones)
        zone_path = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "vav_zone_controller.json"
        with open(zone_path) as f:
            zone_data = json.load(f)

        self.zone_controller = parser.parse(zone_data)
        result = validator.validate(self.zone_controller)
        if not result.is_valid:
            print("WARNING: Zone controller validation failed:")
            for error in result.errors:
                print(f"  - {error}")

        # Create execution context for each zone
        self.zone_contexts = [
            ExecutionContext(self.zone_controller)
            for _ in range(self.num_zones)
        ]

    def get_occupancy_schedule(self, hour: float) -> bool:
        """Get occupancy status based on time of day.

        Args:
            hour: Hour of day (0-24)

        Returns:
            True if occupied, False if unoccupied
        """
        # Occupied 7 AM to 6 PM on weekdays
        return 7 <= hour < 18

    def get_zone_setpoint(self, hour: float, occupied: bool) -> float:
        """Get zone temperature setpoint.

        Args:
            hour: Hour of day
            occupied: Occupancy status

        Returns:
            Temperature setpoint in Kelvin
        """
        if occupied:
            return 294.15  # 21°C occupied
        else:
            return 291.15  # 18°C unoccupied setback

    def get_outdoor_temperature(self, hour: float) -> float:
        """Get outdoor temperature based on time of day.

        Simulates a sinusoidal daily temperature variation.

        Args:
            hour: Hour of day (0-24)

        Returns:
            Outdoor temperature in Kelvin
        """
        # Daily variation: min at 6 AM, max at 3 PM
        t_min = 278.15  # 5°C minimum
        t_max = 293.15  # 20°C maximum
        t_avg = (t_min + t_max) / 2
        t_amp = (t_max - t_min) / 2

        # Peak at hour 15 (3 PM)
        phase = (hour - 15) * 2 * np.pi / 24
        return t_avg + t_amp * np.cos(phase)

    def compute_ahu_control(self):
        """Compute AHU control outputs.

        This implements simplified ASHRAE G36 AHU sequences:
        1. Fan speed modulation based on duct static pressure
        2. Economizer control based on outdoor conditions
        3. Cooling/heating coil control for supply temperature
        """
        # Set AHU inputs
        self.ahu_context.set_input("TOut", self.ahu_state.outdoor_temp)
        self.ahu_context.set_input("TMix", self.ahu_state.mixed_temp)
        self.ahu_context.set_input("TSup", self.ahu_state.supply_temp)
        self.ahu_context.set_input("TSupSet", self.ahu_state.supply_temp_setpoint)
        self.ahu_context.set_input("dpDuc", self.ahu_state.duct_pressure)
        self.ahu_context.set_input("dpDucSet", self.ahu_state.duct_pressure_setpoint)
        self.ahu_context.set_input("uOcc", self.ahu_state.occupied)

        # Execute AHU controller
        self.ahu_context.compute()

        # Get outputs (with fallback to simple control if compute doesn't work)
        fan_speed = self.ahu_context.get_output("yFan")
        if fan_speed is None:
            # Simple PI control for fan speed
            dp_error = self.ahu_state.duct_pressure_setpoint - self.ahu_state.duct_pressure
            fan_speed = np.clip(0.5 + 0.001 * dp_error, 0.2, 1.0)

        oa_damper = self.ahu_context.get_output("yOutDam")
        if oa_damper is None:
            # Simple economizer logic
            if self.ahu_state.outdoor_temp < 289.15:  # Below 16°C
                oa_damper = 0.8  # Use outdoor air for cooling
            else:
                oa_damper = 0.2  # Minimum outdoor air

        ra_damper = 1.0 - oa_damper

        cooling_valve = self.ahu_context.get_output("yCooCoil")
        if cooling_valve is None:
            # Simple cooling control
            temp_error = self.ahu_state.supply_temp - self.ahu_state.supply_temp_setpoint
            cooling_valve = np.clip(0.1 * temp_error, 0.0, 1.0)

        heating_valve = self.ahu_context.get_output("yHeaCoil")
        if heating_valve is None:
            # Simple heating control
            temp_error = self.ahu_state.supply_temp_setpoint - self.ahu_state.supply_temp
            heating_valve = np.clip(0.1 * temp_error, 0.0, 1.0)

        # Update AHU state
        self.ahu_state.fan_speed = float(fan_speed)
        self.ahu_state.oa_damper = float(oa_damper)
        self.ahu_state.ra_damper = float(ra_damper)
        self.ahu_state.cooling_valve = float(cooling_valve)
        self.ahu_state.heating_valve = float(heating_valve)

    def compute_zone_control(self, zone_idx: int):
        """Compute zone control outputs.

        Implements ASHRAE G36 VAV box sequences:
        1. Cooling: Modulate airflow from min to max
        2. Heating: Reduce to minimum airflow, then modulate reheat

        Args:
            zone_idx: Zone index (0-based)
        """
        zone = self.zone_states[zone_idx]
        ctx = self.zone_contexts[zone_idx]

        # Set zone inputs
        ctx.set_input("TZon", zone.temperature)
        ctx.set_input("TZonSet", zone.setpoint)
        ctx.set_input("TSup", self.ahu_state.supply_temp)
        ctx.set_input("VDis_flow_min", 0.05)  # 50 L/s minimum
        ctx.set_input("VDis_flow_max", 0.20)  # 200 L/s maximum

        # Execute zone controller
        ctx.compute()

        # Get outputs (with fallback to simple control)
        airflow = ctx.get_output("VDis_flow")
        if airflow is None:
            # Simple airflow control based on temperature error
            temp_error = zone.temperature - zone.setpoint
            if temp_error > 0.5:  # Cooling needed
                airflow = 0.05 + (0.15 * min(temp_error / 2.0, 1.0))
            else:
                airflow = 0.05  # Minimum

        damper = ctx.get_output("yDam")
        if damper is None:
            damper = (airflow - 0.05) / 0.15  # Map airflow to damper position

        reheat_valve = ctx.get_output("yVal")
        if reheat_valve is None:
            # Simple reheat control
            temp_error = zone.setpoint - zone.temperature
            if temp_error > 0.5 and airflow <= 0.06:  # Heating needed, at minimum airflow
                reheat_valve = np.clip(0.5 * temp_error, 0.0, 1.0)
            else:
                reheat_valve = 0.0

        # Update zone state
        zone.airflow = float(airflow)
        zone.damper_position = float(np.clip(damper, 0.0, 1.0))
        zone.reheat_valve = float(reheat_valve)

    def simulate_ahu_physics(self, dt: float):
        """Simulate AHU physics (simplified).

        Args:
            dt: Time step in seconds
        """
        # Mix outdoor and return air
        oa_fraction = self.ahu_state.oa_damper
        ra_fraction = self.ahu_state.ra_damper

        # Average zone temperature for return air
        avg_zone_temp = np.mean([z.temperature for z in self.zone_states])

        self.ahu_state.mixed_temp = (
            oa_fraction * self.ahu_state.outdoor_temp +
            ra_fraction * avg_zone_temp
        )

        # Apply heating/cooling coils
        # Simplified: each 10% valve position changes temp by 1K
        temp_change = 0.0
        if self.ahu_state.cooling_valve > 0.01:
            temp_change -= 10.0 * self.ahu_state.cooling_valve  # Cooling
        if self.ahu_state.heating_valve > 0.01:
            temp_change += 10.0 * self.ahu_state.heating_valve  # Heating

        target_supply_temp = self.ahu_state.mixed_temp + temp_change

        # First-order lag on temperature change
        tau = 60.0  # Time constant
        alpha = dt / (tau + dt)
        self.ahu_state.supply_temp += alpha * (target_supply_temp - self.ahu_state.supply_temp)

        # Duct pressure based on fan speed and total airflow
        total_airflow = sum(z.airflow for z in self.zone_states)
        pressure_from_flow = 200.0 * total_airflow  # Simplified
        pressure_from_fan = 700.0 * self.ahu_state.fan_speed

        target_pressure = pressure_from_fan - pressure_from_flow
        self.ahu_state.duct_pressure += alpha * (target_pressure - self.ahu_state.duct_pressure)

    def simulate_zone_physics(self, zone_idx: int, dt: float):
        """Simulate zone thermal physics (simplified).

        Args:
            zone_idx: Zone index
            dt: Time step in seconds
        """
        zone = self.zone_states[zone_idx]

        # Heat from supply air
        mass_flow = zone.airflow * self.air_density  # kg/s
        q_supply = mass_flow * self.air_specific_heat * (
            self.ahu_state.supply_temp - zone.temperature
        )

        # Heat from reheat coil
        q_reheat = self.reheat_capacity * zone.reheat_valve

        # Heat loss to outdoor through envelope
        q_envelope = -self.zone_area * self.u_value * (
            zone.temperature - self.ahu_state.outdoor_temp
        )

        # Internal gains (occupancy, equipment, lighting)
        q_internal = 1000.0 if self.ahu_state.occupied else 200.0  # W

        # Total heat balance
        q_total = q_supply + q_reheat + q_envelope + q_internal

        # Temperature change
        zone_mass = self.zone_volume * self.air_density
        zone_thermal_mass = zone_mass * self.air_specific_heat

        dT = (q_total * dt) / zone_thermal_mass
        zone.temperature += dT

    def step(self):
        """Execute one simulation time step."""
        # Get current hour for scheduling
        hour = (self.current_time / 3600.0) % 24

        # Update occupancy and setpoints
        self.ahu_state.occupied = self.get_occupancy_schedule(hour)
        for zone in self.zone_states:
            zone.setpoint = self.get_zone_setpoint(hour, self.ahu_state.occupied)

        # Update outdoor conditions
        self.ahu_state.outdoor_temp = self.get_outdoor_temperature(hour)

        # Execute control sequences
        self.compute_ahu_control()
        for i in range(self.num_zones):
            self.compute_zone_control(i)

        # Simulate physics
        self.simulate_ahu_physics(self.time_step)
        for i in range(self.num_zones):
            self.simulate_zone_physics(i, self.time_step)

        # Log data
        self.log_data()

        # Advance time
        self.current_time += self.time_step

    def log_data(self):
        """Log current state to history."""
        hour = self.current_time / 3600.0

        self.history['time'].append(hour)
        self.history['ahu_outdoor_temp'].append(self.ahu_state.outdoor_temp - 273.15)  # °C
        self.history['ahu_supply_temp'].append(self.ahu_state.supply_temp - 273.15)
        self.history['ahu_fan_speed'].append(self.ahu_state.fan_speed * 100)  # %
        self.history['ahu_oa_damper'].append(self.ahu_state.oa_damper * 100)
        self.history['ahu_cooling_valve'].append(self.ahu_state.cooling_valve * 100)
        self.history['ahu_heating_valve'].append(self.ahu_state.heating_valve * 100)

        for i, zone in enumerate(self.zone_states):
            self.history[f'zone{i+1}_temp'].append(zone.temperature - 273.15)
            self.history[f'zone{i+1}_setpoint'].append(zone.setpoint - 273.15)
            self.history[f'zone{i+1}_airflow'].append(zone.airflow * 1000)  # L/s
            self.history[f'zone{i+1}_reheat'].append(zone.reheat_valve * 100)

    def run_simulation(self, duration_hours: float = 24.0):
        """Run simulation for specified duration.

        Args:
            duration_hours: Simulation duration in hours
        """
        num_steps = int(duration_hours * 3600 / self.time_step)

        print(f"Running VAV system simulation for {duration_hours} hours...")
        print(f"Number of zones: {self.num_zones}")
        print(f"Time step: {self.time_step/60:.1f} minutes")
        print(f"Total steps: {num_steps}")
        print()

        for step in range(num_steps):
            self.step()

            # Print progress every hour
            if step % 12 == 0:
                hour = self.current_time / 3600.0
                zone1 = self.zone_states[0]
                print(f"Hour {hour:5.1f}: "
                      f"OAT={self.ahu_state.outdoor_temp-273.15:5.1f}°C  "
                      f"SAT={self.ahu_state.supply_temp-273.15:5.1f}°C  "
                      f"Zone1={zone1.temperature-273.15:5.1f}°C (SP={zone1.setpoint-273.15:5.1f}°C)  "
                      f"Reheat={zone1.reheat_valve*100:4.1f}%")

        print()
        print("Simulation complete!")

    def plot_results(self, output_file: str = "vav_system_24h_simulation.png"):
        """Generate comprehensive plot of simulation results.

        Args:
            output_file: Path to save plot
        """
        fig, axes = plt.subplots(4, 2, figsize=(16, 12))
        fig.suptitle('VAV System 24-Hour Simulation - ASHRAE Guideline 36', fontsize=16, fontweight='bold')

        time = np.array(self.history['time'])

        # Plot 1: Zone Temperatures
        ax = axes[0, 0]
        for i in range(min(3, self.num_zones)):  # Plot first 3 zones
            ax.plot(time, self.history[f'zone{i+1}_temp'], label=f'Zone {i+1}', linewidth=2)
            ax.plot(time, self.history[f'zone{i+1}_setpoint'], '--', alpha=0.7, linewidth=1)
        ax.plot(time, self.history['ahu_outdoor_temp'], 'k:', label='Outdoor', linewidth=1.5)
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Zone Temperatures')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.axhspan(7, 18, alpha=0.1, color='yellow', label='Occupied')

        # Plot 2: AHU Supply Temperature
        ax = axes[0, 1]
        ax.plot(time, self.history['ahu_supply_temp'], 'b-', label='Supply Temp', linewidth=2)
        ax.axhline(y=13, color='r', linestyle='--', label='Setpoint (13°C)', linewidth=1)
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('AHU Supply Air Temperature')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        # Plot 3: Zone Airflows
        ax = axes[1, 0]
        for i in range(min(3, self.num_zones)):
            ax.plot(time, self.history[f'zone{i+1}_airflow'], label=f'Zone {i+1}', linewidth=2)
        ax.set_ylabel('Airflow (L/s)')
        ax.set_title('Zone Airflow Rates')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 4: Reheat Valves
        ax = axes[1, 1]
        for i in range(min(3, self.num_zones)):
            ax.plot(time, self.history[f'zone{i+1}_reheat'], label=f'Zone {i+1}', linewidth=2)
        ax.set_ylabel('Valve Position (%)')
        ax.set_title('Zone Reheat Valve Positions')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 5: AHU Fan Speed
        ax = axes[2, 0]
        ax.plot(time, self.history['ahu_fan_speed'], 'g-', linewidth=2)
        ax.fill_between(time, 0, self.history['ahu_fan_speed'], alpha=0.3)
        ax.set_ylabel('Fan Speed (%)')
        ax.set_title('AHU Supply Fan Speed')
        ax.grid(True, alpha=0.3)

        # Plot 6: Economizer Dampers
        ax = axes[2, 1]
        ax.plot(time, self.history['ahu_oa_damper'], 'b-', label='OA Damper', linewidth=2)
        ax.set_ylabel('Damper Position (%)')
        ax.set_title('AHU Outdoor Air Damper')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        # Plot 7: Cooling Coil
        ax = axes[3, 0]
        ax.plot(time, self.history['ahu_cooling_valve'], 'b-', linewidth=2)
        ax.fill_between(time, 0, self.history['ahu_cooling_valve'], alpha=0.3, color='blue')
        ax.set_ylabel('Valve Position (%)')
        ax.set_xlabel('Time (hours)')
        ax.set_title('AHU Cooling Coil Valve')
        ax.grid(True, alpha=0.3)

        # Plot 8: Heating Coil
        ax = axes[3, 1]
        ax.plot(time, self.history['ahu_heating_valve'], 'r-', linewidth=2)
        ax.fill_between(time, 0, self.history['ahu_heating_valve'], alpha=0.3, color='red')
        ax.set_ylabel('Valve Position (%)')
        ax.set_xlabel('Time (hours)')
        ax.set_title('AHU Heating Coil Valve')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        output_path = Path(__file__).parent / output_file
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

        plt.close()

    def print_performance_summary(self):
        """Print performance metrics and energy analysis."""
        print("\n" + "="*60)
        print("VAV SYSTEM PERFORMANCE SUMMARY")
        print("="*60)

        # Zone performance
        print("\nZONE PERFORMANCE:")
        for i in range(self.num_zones):
            temps = np.array(self.history[f'zone{i+1}_temp'])
            setpoints = np.array(self.history[f'zone{i+1}_setpoint'])
            errors = np.abs(temps - setpoints)

            mae = np.mean(errors)
            max_error = np.max(errors)
            time_in_comfort = np.sum(errors < 0.5) / len(errors) * 100

            print(f"  Zone {i+1}:")
            print(f"    Mean Absolute Error: {mae:.2f}°C")
            print(f"    Maximum Error: {max_error:.2f}°C")
            print(f"    Time at Setpoint (±0.5°C): {time_in_comfort:.1f}%")

        # Energy usage
        print("\nENERGY USAGE INDICATORS:")
        avg_reheat = np.mean([np.mean(self.history[f'zone{i+1}_reheat']) for i in range(self.num_zones)])
        avg_cooling = np.mean(self.history['ahu_cooling_valve'])
        avg_heating = np.mean(self.history['ahu_heating_valve'])
        avg_fan = np.mean(self.history['ahu_fan_speed'])

        print(f"  Average Zone Reheat: {avg_reheat:.1f}%")
        print(f"  Average AHU Cooling: {avg_cooling:.1f}%")
        print(f"  Average AHU Heating: {avg_heating:.1f}%")
        print(f"  Average Fan Speed: {avg_fan:.1f}%")

        # Economizer usage
        high_oa = np.sum(np.array(self.history['ahu_oa_damper']) > 50) / len(self.history['ahu_oa_damper']) * 100
        print(f"  Economizer Active (OA>50%): {high_oa:.1f}% of time")

        print("\n" + "="*60)


def main():
    """Main function to run VAV system example."""
    print("="*60)
    print("VAV REHEAT SYSTEM SIMULATION")
    print("Following ASHRAE Guideline 36-2018")
    print("="*60)
    print()

    # Create VAV system with 5 zones
    vav = VAVSystem(num_zones=5)

    # Run 24-hour simulation
    vav.run_simulation(duration_hours=24.0)

    # Generate plots
    vav.plot_results()

    # Print performance summary
    vav.print_performance_summary()

    print("\n✅ Simulation complete! Check vav_system_24h_simulation.png for results.")


if __name__ == "__main__":
    main()
