"""Tests for VAV box controller with reheat.

This module provides basic tests to verify the VAV controller implementation
follows ASHRAE 2006 sequences correctly.
"""

import pytest

from .zone_controller import VAVBoxController
from .zone_models import ZoneState, ZoneType, get_zone_config


class TestVAVBoxController:
    """Test suite for VAV box controller."""

    def test_cooling_mode(self):
        """Test controller in cooling mode (high temperature)."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Hot room requiring cooling
        state = ZoneState(room_temp=27.0, supply_air_temp=13.0)

        # Run for a few steps
        for _ in range(5):
            state = controller.update_state(state, dt=1.0)

        # In cooling mode:
        # - Damper should be well above minimum
        # - Reheat should be off
        assert state.damper_position > config.min_damper_position
        assert state.reheat_valve_position == 0.0
        assert state.cooling_demand > 0.0
        assert state.heating_demand == 0.0

    def test_heating_mode(self):
        """Test controller in heating mode (low temperature)."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Cold room requiring heating
        state = ZoneState(room_temp=19.0, supply_air_temp=13.0)

        # Run for a few steps
        for _ in range(5):
            state = controller.update_state(state, dt=1.0)

        # In heating mode:
        # - Damper should be at minimum
        # - Reheat should be active
        assert state.damper_position == config.min_damper_position
        assert state.reheat_valve_position > 0.0
        assert state.cooling_demand == 0.0
        assert state.heating_demand > 0.0

    def test_deadband_mode(self):
        """Test controller in deadband mode (comfortable temperature)."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Comfortable temperature in deadband
        state = ZoneState(room_temp=22.5, supply_air_temp=13.0)

        # Run for a few steps
        for _ in range(5):
            state = controller.update_state(state, dt=1.0)

        # In deadband mode:
        # - Damper should be at minimum
        # - Reheat should be minimal or off
        assert state.damper_position == config.min_damper_position
        assert state.reheat_valve_position <= 0.1
        assert state.cooling_demand == 0.0
        assert state.heating_demand == 0.0

    def test_minimum_airflow_enforcement(self):
        """Test that minimum airflow is always maintained."""
        config = get_zone_config(ZoneType.CORRIDOR)
        controller = VAVBoxController(config)

        # Test various temperatures
        test_temps = [19.0, 22.0, 23.5, 26.0]

        for temp in test_temps:
            controller.reset()
            state = ZoneState(room_temp=temp, supply_air_temp=13.0)

            for _ in range(5):
                state = controller.update_state(state, dt=1.0)

            # Airflow should never be below minimum
            assert state.airflow >= config.min_airflow
            # Damper should never be below minimum
            assert state.damper_position >= config.min_damper_position

    def test_output_clamping(self):
        """Test that outputs are properly clamped to valid ranges."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Extreme temperature conditions
        extreme_temps = [15.0, 30.0]

        for temp in extreme_temps:
            controller.reset()
            state = ZoneState(room_temp=temp, supply_air_temp=13.0)

            for _ in range(10):
                state = controller.update_state(state, dt=1.0)

            # Check all outputs are within valid ranges
            assert 0.0 <= state.damper_position <= 1.0
            assert 0.0 <= state.reheat_valve_position <= 1.0
            assert 0.0 <= state.cooling_demand <= 1.0
            assert 0.0 <= state.heating_demand <= 1.0
            assert state.airflow >= 0.0

    def test_mode_transitions(self):
        """Test smooth transitions between control modes."""
        config = get_zone_config(ZoneType.EAST)
        controller = VAVBoxController(config)

        # Start in cooling mode
        state = ZoneState(room_temp=27.0, supply_air_temp=13.0)
        state = controller.update_state(state, dt=1.0)
        initial_damper = state.damper_position

        # Should be in cooling mode initially
        assert initial_damper > config.min_damper_position
        assert state.reheat_valve_position == 0.0

        # Set temperature to deadband
        state.room_temp = 22.5
        controller.reset()  # Reset integral terms for clean test
        for _ in range(3):
            state = controller.update_state(state, dt=1.0)

        # Should be in deadband now
        assert state.damper_position == config.min_damper_position
        assert state.reheat_valve_position <= 0.1

        # Set temperature to heating mode
        state.room_temp = 19.0
        controller.reset()  # Reset integral terms
        for _ in range(3):
            state = controller.update_state(state, dt=1.0)

        # Should be in heating mode now
        assert state.damper_position == config.min_damper_position
        assert state.reheat_valve_position > 0.0

    def test_all_zones_initialized(self):
        """Test that all zone types can be initialized."""
        for zone_type in ZoneType:
            config = get_zone_config(zone_type)
            controller = VAVBoxController(config)

            # Verify controller is properly initialized
            assert controller.config == config
            assert controller.damper_integral == 0.0
            assert controller.reheat_integral == 0.0

            # Verify basic operation
            state = ZoneState(room_temp=22.0, supply_air_temp=13.0)
            state = controller.update_state(state, dt=1.0)

            assert state.damper_position >= 0.0
            assert state.reheat_valve_position >= 0.0

    def test_controller_reset(self):
        """Test that reset clears integral terms."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Run controller to build up integral terms
        state = ZoneState(room_temp=27.0, supply_air_temp=13.0)
        for _ in range(10):
            state = controller.update_state(state, dt=1.0)

        # Integral terms should be non-zero
        assert controller.damper_integral != 0.0 or controller.reheat_integral != 0.0

        # Reset and verify
        controller.reset()
        assert controller.damper_integral == 0.0
        assert controller.reheat_integral == 0.0

    def test_airflow_calculation(self):
        """Test airflow calculation based on damper position."""
        config = get_zone_config(ZoneType.SOUTH)
        controller = VAVBoxController(config)

        # Test at minimum damper position (0.0)
        # This should give minimum airflow
        airflow_min = controller.compute_airflow(0.0)
        assert airflow_min == pytest.approx(config.min_airflow, rel=0.01)

        # Test at maximum damper position
        airflow_max = controller.compute_airflow(1.0)
        assert airflow_max == pytest.approx(config.max_airflow, rel=0.01)

        # Test at mid position - should be between min and max
        airflow_mid = controller.compute_airflow(0.5)
        expected_mid = config.min_airflow + 0.5 * (config.max_airflow - config.min_airflow)
        assert airflow_mid == pytest.approx(expected_mid, rel=0.01)

        # Verify airflow increases with damper position
        airflow_25 = controller.compute_airflow(0.25)
        airflow_75 = controller.compute_airflow(0.75)
        assert airflow_25 < airflow_mid < airflow_75

    def test_perimeter_vs_interior_zones(self):
        """Test that perimeter zones have different characteristics than interior."""
        corridor_config = get_zone_config(ZoneType.CORRIDOR)
        south_config = get_zone_config(ZoneType.SOUTH)

        # Perimeter zones should have:
        # - Higher max airflow capacity
        # - Different control gains
        assert south_config.max_airflow > corridor_config.max_airflow
        assert south_config.kp_damper >= corridor_config.kp_damper


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
