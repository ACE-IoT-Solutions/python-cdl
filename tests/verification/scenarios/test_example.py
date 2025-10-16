"""Example verification test demonstrating the framework.

This test shows how to use the verification framework utilities
for comparing simulation results with reference data.
"""

import numpy as np
import pytest

from tests.verification.utils import (
    ToleranceSpec,
    compare_time_series,
)


@pytest.mark.verification
@pytest.mark.time_series
def test_framework_example(simulation_runner, default_tolerance):
    """Example test showing verification framework usage.

    This is a simplified example that demonstrates the core workflow:
    1. Create a simple test block
    2. Generate reference data analytically
    3. Run simulation
    4. Compare results with tolerance checking

    Note: This is a demonstration test. Real verification tests will
    load actual reference data from Modelica or other sources.
    """
    # For this example, we'll create a simple test scenario
    # Real tests would load blocks from JSON and reference data from CSV/JSON

    # 1. Generate "reference" data analytically
    # For demo: y = 0.5 * u (simple gain block)
    time = np.linspace(0.0, 10.0, 101)  # 0 to 10 seconds, 0.1s step
    input_u = np.sin(time)  # Sinusoidal input
    expected_y = 0.5 * input_u  # Expected output with gain=0.5

    # 2. Simulate with input data
    # Note: This example assumes we have a simple gain block
    # In real tests, you would:
    #   - Load block: block = load_from_json("blocks/my_block.json")
    #   - Create runner: runner = simulation_runner(block)
    #   - Run simulation: result = runner.run_from_arrays(time, {"u": input_u})

    # For this demo, we'll create simulated output with small noise
    # to demonstrate the tolerance checking
    noise = np.random.normal(0, 1e-7, len(time))
    simulated_y = expected_y + noise

    # 3. Compare results with tolerance
    comparison = compare_time_series(
        time=time,
        actual=simulated_y,
        expected=expected_y,
        tolerance=default_tolerance,
        variable_name="y",
    )

    # 4. Assert and report
    assert comparison.passed, comparison.summary()

    # Additional assertions on metrics
    assert comparison.pass_rate > 99.0  # Should pass almost all points
    assert comparison.max_absolute_error < 1e-5  # Max error should be tiny


@pytest.mark.verification
def test_tolerance_modes():
    """Test different tolerance combination modes."""
    time = np.array([0.0, 1.0, 2.0])
    actual = np.array([1.0, 2.0, 3.0])
    expected = np.array([1.001, 2.001, 3.001])  # 0.001 absolute error

    # OR mode: passes if either tolerance is met
    tol_or = ToleranceSpec(absolute=1e-2, relative=1e-6, mode="or")
    result_or = compare_time_series(time, actual, expected, tol_or)
    assert result_or.passed  # Passes because absolute tolerance is met

    # AND mode: requires both tolerances
    tol_and = ToleranceSpec(absolute=1e-2, relative=1e-6, mode="and")
    result_and = compare_time_series(time, actual, expected, tol_and)
    assert not result_and.passed  # Fails because relative tolerance not met


@pytest.mark.verification
def test_failed_points_diagnostics():
    """Test that failed points are properly reported."""
    time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    expected = np.array([1.0, 2.0, 3.1, 4.0, 5.0])  # One point differs

    tolerance = ToleranceSpec(absolute=1e-3)
    result = compare_time_series(time, actual, expected, tolerance)

    assert not result.passed
    assert result.points_failed == 1
    assert result.points_passed == 4
    assert len(result.failed_points) == 1
    assert result.failed_points[0].time == 2.0


@pytest.mark.verification
@pytest.mark.parametrize(
    "absolute,relative,should_pass",
    [
        (1e-6, 1e-4, True),  # Strict tolerances, should pass for small errors
        (1e-9, 1e-9, False),  # Very strict, should fail with any error
        (1e-2, 1e-2, True),  # Relaxed, should pass for moderate errors
    ],
)
def test_tolerance_sensitivity(absolute, relative, should_pass):
    """Test sensitivity to different tolerance settings."""
    time = np.linspace(0, 1, 11)
    expected = np.sin(time)
    # Add small numerical error
    actual = expected + np.random.normal(0, 1e-8, len(time))

    tolerance = ToleranceSpec(absolute=absolute, relative=relative, mode="or")
    result = compare_time_series(time, actual, expected, tolerance)

    if should_pass:
        assert result.passed, f"Expected to pass with tol={absolute}/{relative}"
    else:
        assert not result.passed, f"Expected to fail with tol={absolute}/{relative}"


@pytest.mark.verification
def test_statistics_calculation():
    """Test that comparison statistics are correctly calculated."""
    time = np.array([0.0, 1.0, 2.0, 3.0])
    actual = np.array([1.0, 2.0, 3.0, 4.0])
    expected = np.array([1.1, 2.1, 3.1, 4.1])  # Constant 0.1 error

    tolerance = ToleranceSpec(absolute=1.0)  # Large tolerance to pass
    result = compare_time_series(time, actual, expected, tolerance)

    # Check statistics
    assert result.mean_absolute_error == pytest.approx(0.1, abs=1e-10)
    assert result.max_absolute_error == pytest.approx(0.1, abs=1e-10)
    assert result.rmse == pytest.approx(0.1, abs=1e-10)


@pytest.mark.verification
def test_summary_output():
    """Test that summary output is generated correctly."""
    time = np.array([0.0, 1.0])
    actual = np.array([1.0, 2.0])
    expected = np.array([1.0, 2.5])

    tolerance = ToleranceSpec(absolute=0.1)
    result = compare_time_series(time, actual, expected, tolerance, variable_name="test_var")

    summary = result.summary()

    # Check summary contains key information
    assert "test_var" in summary
    assert "FAILED" in summary  # Should fail because error is 0.5 > 0.1
    assert "Max absolute error" in summary
    assert "Mean absolute error" in summary
