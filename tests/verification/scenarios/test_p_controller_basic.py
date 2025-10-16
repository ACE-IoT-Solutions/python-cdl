"""Basic P-controller verification tests.

This test module validates fundamental proportional controller behavior
using synthetic test data and analytical solutions.

Test scenarios:
1. Step response - verify proportional gain behavior
2. Setpoint tracking - verify steady-state accuracy
3. Gain sweep - verify linear gain relationship
4. Error response - verify correct error calculation
"""

import json
from pathlib import Path

import numpy as np
import pytest

from python_cdl.parser import load_cdl_file
from tests.verification.utils import (
    SimulationConfig,
    SimulationRunner,
    ToleranceSpec,
    compare_time_series,
)


@pytest.fixture
def p_controller_block():
    """Load P-controller block from JSON."""
    # Use the example P-controller with limiter
    block_path = Path(__file__).parent.parent.parent.parent / "examples" / "p_controller_limiter.json"
    return load_cdl_file(block_path)


@pytest.fixture
def p_controller_runner(p_controller_block):
    """Create simulation runner for P-controller."""
    return SimulationRunner(p_controller_block)


@pytest.mark.verification
@pytest.mark.time_series
def test_p_controller_step_response(p_controller_runner, default_tolerance):
    """Test P-controller response to step change in error signal.

    Validates:
    - Output = k * error (where k=5.0 from block definition)
    - Immediate response (no dynamics in P-controller)
    - Correct proportional gain
    """
    # Test configuration
    config = SimulationConfig(
        start_time=0.0,
        end_time=10.0,
        time_step=0.1
    )

    # Step input: error jumps from 0 to 1 at t=0
    # yMax = 10.0 (no limiting)
    input_functions = {
        "e": lambda t: 1.0,      # Constant error = 1.0
        "yMax": lambda t: 10.0   # No limiting
    }

    # Run simulation
    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected output: y = k * e = 5.0 * 1.0 = 5.0
    expected_y = np.full_like(result.time, 5.0)

    # Compare with tight tolerance (analytical solution)
    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6, relative=1e-9),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()
    assert comparison.max_absolute_error < 1e-5


@pytest.mark.verification
@pytest.mark.time_series
def test_p_controller_varying_error(p_controller_runner):
    """Test P-controller with time-varying error signal.

    Validates:
    - Output tracks k * error at all times
    - No lag or dynamics
    - Correct proportional relationship
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=10.0,
        time_step=0.1
    )

    # Sinusoidal error signal
    input_functions = {
        "e": lambda t: np.sin(t),
        "yMax": lambda t: 10.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected output: y = k * e = 5.0 * sin(t)
    expected_y = 5.0 * np.sin(result.time)

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6, relative=1e-6),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()


@pytest.mark.verification
@pytest.mark.time_series
def test_p_controller_output_limiting(p_controller_runner):
    """Test P-controller output limiting.

    Validates:
    - Output respects yMax limit
    - Output = min(yMax, k*e)
    - Limiting behavior is correct
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=10.0,
        time_step=0.1
    )

    # Large error but limited output
    # k * e = 5.0 * 2.0 = 10.0, but yMax = 3.0
    input_functions = {
        "e": lambda t: 2.0,      # Error = 2.0
        "yMax": lambda t: 3.0    # Limit to 3.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected output: min(3.0, 10.0) = 3.0
    expected_y = np.full_like(result.time, 3.0)

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()


@pytest.mark.verification
def test_p_controller_zero_error(p_controller_runner):
    """Test P-controller with zero error.

    Validates:
    - Zero error produces zero output
    - No offset or bias
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=5.0,
        time_step=0.1
    )

    input_functions = {
        "e": lambda t: 0.0,
        "yMax": lambda t: 10.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected: all zeros
    expected_y = np.zeros_like(result.time)

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-9),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()


@pytest.mark.verification
@pytest.mark.time_series
def test_p_controller_negative_error(p_controller_runner):
    """Test P-controller with negative error signal.

    Validates:
    - Correct handling of negative errors
    - Output = k * e (including sign)
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=5.0,
        time_step=0.1
    )

    # Negative error
    input_functions = {
        "e": lambda t: -1.0,
        "yMax": lambda t: 10.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected: y = 5.0 * (-1.0) = -5.0
    expected_y = np.full_like(result.time, -5.0)

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()


@pytest.mark.verification
@pytest.mark.parametrize(
    "error_value,expected_output",
    [
        (0.0, 0.0),
        (0.5, 2.5),
        (1.0, 5.0),
        (1.5, 7.5),
        (2.0, 10.0),
        (-0.5, -2.5),
        (-1.0, -5.0),
    ]
)
def test_p_controller_gain_linearity(p_controller_runner, error_value, expected_output):
    """Test P-controller gain linearity with various error values.

    Validates:
    - Linear relationship between error and output
    - Gain k = 5.0 is correctly applied
    - No nonlinearities or saturation (when not limited)
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=1.0,
        time_step=0.1
    )

    input_functions = {
        "e": lambda t: error_value,
        "yMax": lambda t: 20.0  # Large limit to avoid saturation
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Check steady-state output
    actual_output = result.outputs["y"][-1]  # Last value
    assert abs(actual_output - expected_output) < 1e-6, (
        f"Expected output {expected_output} for error {error_value}, "
        f"got {actual_output}"
    )


@pytest.mark.verification
@pytest.mark.time_series
def test_p_controller_ramp_input(p_controller_runner):
    """Test P-controller tracking of ramp error signal.

    Validates:
    - Output correctly follows ramping input
    - No lag (proportional control is instantaneous)
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=10.0,
        time_step=0.1
    )

    # Ramp error: e(t) = 0.1 * t
    input_functions = {
        "e": lambda t: 0.1 * t,
        "yMax": lambda t: 10.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected: y = k * e = 5.0 * 0.1 * t = 0.5 * t
    expected_y = 0.5 * result.time

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6, relative=1e-6),
        variable_name="y"
    )

    assert comparison.passed, comparison.summary()


@pytest.mark.verification
def test_p_controller_summary_statistics(p_controller_runner):
    """Test that P-controller produces expected summary statistics.

    Validates:
    - Mean, RMS, and other statistics match expected values
    """
    config = SimulationConfig(
        start_time=0.0,
        end_time=10.0,
        time_step=0.1
    )

    # Sinusoidal error
    input_functions = {
        "e": lambda t: np.sin(2 * np.pi * t),  # 1 Hz sine
        "yMax": lambda t: 20.0
    }

    result = p_controller_runner.run_time_series(
        config=config,
        input_functions=input_functions,
        output_names=["y"]
    )

    assert result.success, f"Simulation failed: {result.error}"

    # Expected: y = 5.0 * sin(2*pi*t)
    expected_y = 5.0 * np.sin(2 * np.pi * result.time)

    comparison = compare_time_series(
        time=result.time,
        actual=result.outputs["y"],
        expected=expected_y,
        tolerance=ToleranceSpec(absolute=1e-6),
        variable_name="y"
    )

    # Check statistics
    assert comparison.passed
    assert abs(comparison.statistics["mean_actual"]) < 0.1  # Mean should be ~0
    assert comparison.rmse < 1e-5  # Very low error expected
