"""
Basic P-controller verification tests.

Tests proportional controller behavior with synthetic test data to verify
fundamental control algorithm correctness.
"""

import pytest
import numpy as np
from python_cdl.models import Block, RealInput, RealOutput, Parameter, Equation
from python_cdl.runtime import ExecutionContext
from tests.verification.utils import (
    ToleranceSpec,
    compare_time_series,
    SimulationRunner,
    SimulationConfig,
)


@pytest.fixture
def p_controller_block():
    """Create a simple P-controller block."""
    return Block(
        name="PController",
        block_type="elementary",
        parameters=[
            Parameter(name="k", type="Real", value=2.0, description="Proportional gain"),
        ],
        inputs=[
            RealInput(name="u_s", description="Setpoint", unit="1"),
            RealInput(name="u_m", description="Measurement", unit="1"),
        ],
        outputs=[
            RealOutput(name="y", description="Control output", unit="1"),
        ],
        equations=[
            Equation(lhs="e", rhs="u_s - u_m"),  # Error
            Equation(lhs="y", rhs="k * e"),      # Proportional action
        ],
    )


@pytest.mark.verification
class TestPControllerBasic:
    """Basic verification tests for P-controller."""

    def test_zero_error_zero_output(self, p_controller_block, default_tolerance):
        """Test that zero error produces zero output."""
        ctx = ExecutionContext(p_controller_block)

        # Set equal setpoint and measurement
        ctx.set_input("u_s", 50.0)
        ctx.set_input("u_m", 50.0)
        ctx.compute()

        output = ctx.get_output("y")
        assert abs(output - 0.0) < 1e-10, f"Expected 0.0, got {output}"

    def test_proportional_gain(self, p_controller_block, default_tolerance):
        """Test that output is proportional to error."""
        ctx = ExecutionContext(p_controller_block)

        # Test with k=2.0 (default)
        ctx.set_input("u_s", 60.0)
        ctx.set_input("u_m", 50.0)
        ctx.compute()

        output = ctx.get_output("y")
        expected = 2.0 * (60.0 - 50.0)  # k * error = 2.0 * 10.0 = 20.0
        assert abs(output - expected) < 1e-10, f"Expected {expected}, got {output}"

    def test_gain_parameter_override(self, p_controller_block, default_tolerance):
        """Test that gain parameter can be overridden at runtime."""
        ctx = ExecutionContext(p_controller_block)

        # Override gain to 5.0
        ctx.set_parameter("k", 5.0)
        ctx.set_input("u_s", 60.0)
        ctx.set_input("u_m", 50.0)
        ctx.compute()

        output = ctx.get_output("y")
        expected = 5.0 * (60.0 - 50.0)  # k * error = 5.0 * 10.0 = 50.0
        assert abs(output - expected) < 1e-10, f"Expected {expected}, got {output}"

    def test_step_response(self, p_controller_block, default_tolerance):
        """Test P-controller response to step change in setpoint."""
        config = SimulationConfig(start_time=0.0, end_time=10.0, time_step=1.0)
        runner = SimulationRunner(p_controller_block)

        # Create step input: setpoint jumps from 50 to 60 at t=5
        def setpoint_func(t):
            return 60.0 if t >= 5.0 else 50.0

        # Measurement stays constant at 50
        def measurement_func(t):
            return 50.0

        # Run simulation
        result = runner.run_time_series(
            config=config,
            input_functions={
                "u_s": setpoint_func,
                "u_m": measurement_func,
            },
            output_names=["y"]
        )

        # Expected output (with k=2.0):
        # t < 5: error = 50-50 = 0, y = 0
        # t >= 5: error = 60-50 = 10, y = 20
        time = result.time
        actual_output = result.get_output("y")
        expected_output = np.where(time >= 5.0, 20.0, 0.0)

        # Compare time series
        comparison = compare_time_series(
            time,
            actual_output,
            expected_output,
            tolerance=default_tolerance,
            variable_name="y"
        )

        assert comparison.passed, comparison.summary()

    def test_ramp_response(self, p_controller_block, default_tolerance):
        """Test P-controller response to ramp input."""
        config = SimulationConfig(start_time=0.0, end_time=10.0, time_step=0.5)
        runner = SimulationRunner(p_controller_block)

        # Setpoint ramps from 0 to 100 over 10 seconds
        def setpoint_func(t):
            return 10.0 * t  # 10 units/second

        # Measurement stays at 0
        def measurement_func(t):
            return 0.0

        # Run simulation
        result = runner.run_time_series(
            config=config,
            input_functions={
                "u_s": setpoint_func,
                "u_m": measurement_func,
            },
            output_names=["y"]
        )

        # Expected output: y = k * (setpoint - 0) = 2.0 * 10*t = 20*t
        time = result.time
        actual_output = result.get_output("y")
        expected_output = 20.0 * time

        # Compare time series
        comparison = compare_time_series(
            time,
            actual_output,
            expected_output,
            tolerance=default_tolerance,
            variable_name="y"
        )

        assert comparison.passed, comparison.summary()

    def test_negative_error(self, p_controller_block, default_tolerance):
        """Test P-controller with negative error (measurement > setpoint)."""
        ctx = ExecutionContext(p_controller_block)

        # Measurement exceeds setpoint
        ctx.set_input("u_s", 50.0)
        ctx.set_input("u_m", 60.0)
        ctx.compute()

        output = ctx.get_output("y")
        expected = 2.0 * (50.0 - 60.0)  # k * error = 2.0 * (-10.0) = -20.0
        assert abs(output - expected) < 1e-10, f"Expected {expected}, got {output}"


@pytest.mark.verification
@pytest.mark.parametrize("gain,setpoint,measurement,expected_output", [
    (1.0, 50.0, 40.0, 10.0),   # k=1, error=10
    (2.0, 50.0, 40.0, 20.0),   # k=2, error=10
    (0.5, 100.0, 80.0, 10.0),  # k=0.5, error=20
    (3.0, 20.0, 25.0, -15.0),  # k=3, error=-5 (negative)
    (1.0, 0.0, 0.0, 0.0),      # Zero error
])
def test_p_controller_combinations(gain, setpoint, measurement, expected_output, p_controller_block):
    """Parametrized test for various P-controller configurations."""
    ctx = ExecutionContext(p_controller_block)
    ctx.set_parameter("k", gain)
    ctx.set_input("u_s", setpoint)
    ctx.set_input("u_m", measurement)
    ctx.compute()

    output = ctx.get_output("y")
    assert abs(output - expected_output) < 1e-10, \
        f"k={gain}, error={setpoint-measurement}: expected {expected_output}, got {output}"
