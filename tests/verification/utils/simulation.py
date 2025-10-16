"""Simulation runner for time-series execution of CDL blocks.

This module provides utilities for running CDL blocks over time series inputs
and collecting outputs for verification testing.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from pydantic import BaseModel, Field

from python_cdl.models.blocks import Block
from python_cdl.runtime.context import ExecutionContext, ExecutionEvent, ExecutionEventType
from python_cdl.runtime.executor import BlockExecutor


class SimulationConfig(BaseModel):
    """Configuration for time-series simulation."""

    start_time: float = Field(default=0.0, description="Simulation start time")
    end_time: float = Field(gt=0.0, description="Simulation end time")
    time_step: float = Field(gt=0.0, description="Fixed time step for simulation")
    output_interval: float | None = Field(
        default=None,
        description="Interval for recording outputs (defaults to time_step)",
    )

    def time_points(self) -> np.ndarray:
        """Generate array of time points for simulation."""
        return np.arange(self.start_time, self.end_time + self.time_step, self.time_step)

    def output_times(self) -> np.ndarray:
        """Generate array of output recording times."""
        interval = self.output_interval or self.time_step
        return np.arange(self.start_time, self.end_time + interval, interval)


@dataclass
class SimulationResult:
    """Result of time-series simulation."""

    time: np.ndarray
    outputs: dict[str, np.ndarray]
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    def get_output(self, name: str) -> np.ndarray:
        """Get output values by name.

        Args:
            name: Output variable name

        Returns:
            Array of output values over time

        Raises:
            KeyError: If output name not found
        """
        if name not in self.outputs:
            raise KeyError(
                f"Output '{name}' not found. Available outputs: {list(self.outputs.keys())}"
            )
        return self.outputs[name]


class SimulationRunner:
    """Run CDL blocks over time series for verification testing.

    This class provides utilities for executing CDL blocks with time-varying
    inputs and collecting outputs for comparison with reference data.
    """

    def __init__(self, block: Block):
        """Initialize simulation runner.

        Args:
            block: CDL block to simulate
        """
        self.block = block
        self.context = ExecutionContext(block)
        self.executor = BlockExecutor(self.context)

    def run_time_series(
        self,
        config: SimulationConfig,
        input_functions: dict[str, Callable[[float], Any]],
        output_names: list[str] | None = None,
    ) -> SimulationResult:
        """Run simulation with time-varying inputs.

        Args:
            config: Simulation configuration
            input_functions: Dictionary mapping input names to functions of time
            output_names: List of output names to record (defaults to all outputs)

        Returns:
            SimulationResult containing time and output arrays

        Example:
            >>> runner = SimulationRunner(my_block)
            >>> config = SimulationConfig(end_time=10.0, time_step=0.1)
            >>> inputs = {"u": lambda t: np.sin(t)}
            >>> result = runner.run_time_series(config, inputs, ["y"])
        """
        # Determine outputs to record
        if output_names is None:
            output_names = [output.name for output in self.block.outputs]

        # Generate time points
        time_points = config.time_points()
        output_times = config.output_times()

        # Initialize output arrays
        outputs = {name: [] for name in output_names}

        try:
            # Reset context
            self.context.reset()

            # Simulate each time step
            for t in time_points:
                # Evaluate input functions at current time
                inputs = {name: func(t) for name, func in input_functions.items()}

                # Create execution event
                event = ExecutionEvent(
                    event_type=ExecutionEventType.INPUT_CHANGE,
                    data={"time": t, **inputs},
                )

                # Execute block
                result = self.executor.execute(self.block, inputs, event)

                if not result.success:
                    return SimulationResult(
                        time=time_points,
                        outputs={},
                        success=False,
                        error=f"Execution failed at t={t}: {result.error}",
                    )

                # Record outputs if at output time
                if t in output_times or np.isclose(t, output_times).any():
                    for name in output_names:
                        value = result.outputs.get(name)
                        outputs[name].append(value if value is not None else np.nan)

            # Convert lists to numpy arrays
            output_arrays = {name: np.array(values) for name, values in outputs.items()}

            # Calculate metadata
            metadata = {
                "total_steps": len(time_points),
                "output_points": len(output_times),
                "time_step": config.time_step,
                "duration": config.end_time - config.start_time,
            }

            return SimulationResult(
                time=output_times,
                outputs=output_arrays,
                metadata=metadata,
                success=True,
            )

        except Exception as e:
            return SimulationResult(
                time=time_points,
                outputs={},
                success=False,
                error=f"Simulation error: {str(e)}",
            )

    def run_from_arrays(
        self,
        time: np.ndarray,
        inputs: dict[str, np.ndarray],
        output_names: list[str] | None = None,
    ) -> SimulationResult:
        """Run simulation with pre-defined input arrays.

        Args:
            time: Array of time points
            inputs: Dictionary mapping input names to value arrays
            output_names: List of output names to record (defaults to all outputs)

        Returns:
            SimulationResult containing time and output arrays

        Raises:
            ValueError: If input arrays have inconsistent shapes
        """
        # Validate inputs
        if not all(len(arr) == len(time) for arr in inputs.values()):
            raise ValueError("All input arrays must have same length as time array")

        # Determine outputs to record
        if output_names is None:
            output_names = [output.name for output in self.block.outputs]

        # Initialize output arrays
        outputs = {name: [] for name in output_names}

        try:
            # Reset context
            self.context.reset()

            # Simulate each time step
            for i, t in enumerate(time):
                # Get inputs at current time
                current_inputs = {name: float(arr[i]) for name, arr in inputs.items()}

                # Create execution event
                event = ExecutionEvent(
                    event_type=ExecutionEventType.INPUT_CHANGE,
                    data={"time": t, **current_inputs},
                )

                # Execute block
                result = self.executor.execute(self.block, current_inputs, event)

                if not result.success:
                    return SimulationResult(
                        time=time,
                        outputs={},
                        success=False,
                        error=f"Execution failed at t={t}: {result.error}",
                    )

                # Record outputs
                for name in output_names:
                    value = result.outputs.get(name)
                    outputs[name].append(value if value is not None else np.nan)

            # Convert lists to numpy arrays
            output_arrays = {name: np.array(values) for name, values in outputs.items()}

            # Calculate metadata
            metadata = {
                "total_steps": len(time),
                "time_step": float(np.mean(np.diff(time))) if len(time) > 1 else 0.0,
                "duration": float(time[-1] - time[0]) if len(time) > 1 else 0.0,
            }

            return SimulationResult(
                time=time,
                outputs=output_arrays,
                metadata=metadata,
                success=True,
            )

        except Exception as e:
            return SimulationResult(
                time=time,
                outputs={},
                success=False,
                error=f"Simulation error: {str(e)}",
            )

    def run_steady_state(
        self,
        inputs: dict[str, Any],
        output_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run single execution for steady-state analysis.

        Args:
            inputs: Dictionary of input values
            output_names: List of output names to return (defaults to all outputs)

        Returns:
            Dictionary of output values

        Raises:
            RuntimeError: If execution fails
        """
        # Reset context
        self.context.reset()

        # Create execution event
        event = ExecutionEvent(
            event_type=ExecutionEventType.EXTERNAL,
            data=inputs,
        )

        # Execute block
        result = self.executor.execute(self.block, inputs, event)

        if not result.success:
            raise RuntimeError(f"Steady-state execution failed: {result.error}")

        # Return requested outputs
        if output_names is None:
            return result.outputs

        return {name: result.outputs.get(name) for name in output_names}
