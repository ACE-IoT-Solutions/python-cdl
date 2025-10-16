"""Execution context for CDL blocks."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ExecutionEventType(str, Enum):
    """Types of execution events."""

    INIT = "init"
    INPUT_CHANGE = "input_change"
    PARAMETER_CHANGE = "parameter_change"
    TIMER = "timer"
    EXTERNAL = "external"


@dataclass
class ExecutionEvent:
    """Event that triggers block execution."""

    event_type: ExecutionEventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)


class ExecutionContext:
    """Context for executing CDL blocks.

    Maintains the state of all connectors and provides methods for
    reading inputs, writing outputs, and managing execution flow.

    The context follows CDL semantics:
    - Single assignment: Each input can only be written once per event
    - Synchronous data flow: Computation is instantaneous
    - Event-based: Execution happens at discrete event instants
    """

    def __init__(self, block=None):
        """Initialize execution context.

        Args:
            block: Optional CDL block to execute. If provided, inputs/outputs
                   will be registered automatically.
        """
        self._connector_values: dict[str, Any] = {}
        self._parameter_values: dict[str, Any] = {}
        self._connector_history: dict[str, list[tuple[datetime, Any]]] = {}
        self._write_count: dict[str, int] = {}
        self._current_event: ExecutionEvent | None = None
        self._event_history: list[ExecutionEvent] = []
        self._block = block
        self.current_time = 0.0
        self.step_count = 0

        # Register block connectors and parameters if provided
        if block is not None:
            for inp in getattr(block, 'inputs', []):
                self._connector_values[inp.name] = None
            for out in getattr(block, 'outputs', []):
                self._connector_values[out.name] = None
            # Load default parameter values
            for param in getattr(block, 'parameters', []):
                self._parameter_values[param.name] = param.value

    @property
    def block(self):
        """Get the block being executed."""
        return self._block

    @property
    def current_event(self) -> ExecutionEvent | None:
        """Get the current execution event."""
        return self._current_event

    def begin_event(self, event: ExecutionEvent) -> None:
        """Begin a new execution event.

        Args:
            event: The event to begin

        Raises:
            RuntimeError: If an event is already in progress
        """
        if self._current_event is not None:
            raise RuntimeError("Cannot begin event: event already in progress")

        self._current_event = event
        self._write_count.clear()
        self._event_history.append(event)

    def end_event(self) -> None:
        """End the current execution event.

        Raises:
            RuntimeError: If no event is in progress
        """
        if self._current_event is None:
            raise RuntimeError("Cannot end event: no event in progress")

        self._current_event = None

    def get_value(self, connector_path: str) -> Any:
        """Get the current value of a connector.

        Args:
            connector_path: Full path to connector (e.g., 'block.output')

        Returns:
            Current value of the connector, or None if not set

        Raises:
            RuntimeError: If no event is in progress
        """
        if self._current_event is None:
            raise RuntimeError("Cannot get value: no event in progress")

        return self._connector_values.get(connector_path)

    def set_value(self, connector_path: str, value: Any) -> None:
        """Set the value of a connector.

        Args:
            connector_path: Full path to connector (e.g., 'block.output')
            value: Value to set

        Raises:
            RuntimeError: If no event is in progress
            ValueError: If attempting to write to same connector multiple times
                        in a single event (violates single assignment rule)
        """
        if self._current_event is None:
            raise RuntimeError("Cannot set value: no event in progress")

        # Check single assignment rule
        if connector_path in self._write_count:
            raise ValueError(
                f"Single assignment violation: connector '{connector_path}' "
                f"already written in this event"
            )

        self._connector_values[connector_path] = value
        self._write_count[connector_path] = 1

        # Record in history
        if connector_path not in self._connector_history:
            self._connector_history[connector_path] = []
        self._connector_history[connector_path].append(
            (self._current_event.timestamp, value)
        )

    def get_history(
        self, connector_path: str
    ) -> list[tuple[datetime, Any]]:
        """Get the history of values for a connector.

        Args:
            connector_path: Full path to connector

        Returns:
            List of (timestamp, value) tuples
        """
        return self._connector_history.get(connector_path, []).copy()

    def _validate_type(self, value: Any, expected_type: str, context: str) -> None:
        """Validate that a value matches the expected CDL type.

        Args:
            value: Value to validate
            expected_type: Expected CDL type ('Real', 'Integer', 'Boolean', 'String')
            context: Context for error messages

        Raises:
            TypeError: If value type doesn't match expected type
        """
        if value is None:
            return  # Allow None values

        type_map = {
            'Real': (int, float),
            'Integer': int,
            'Boolean': bool,
            'String': str
        }

        expected_python_types = type_map.get(expected_type)
        if expected_python_types is None:
            # Unknown type, skip validation
            return

        if not isinstance(value, expected_python_types):
            raise TypeError(
                f"Type mismatch for {context}: expected {expected_type}, "
                f"got {type(value).__name__}"
            )

    def set_input(self, name: str, value: Any) -> None:
        """Convenience method to set an input value.

        Args:
            name: Input connector name
            value: Value to set

        Raises:
            TypeError: If value type doesn't match connector type
        """
        # Type checking if block is defined
        if self._block is not None:
            input_connector = next(
                (inp for inp in getattr(self._block, 'inputs', []) if inp.name == name),
                None
            )
            if input_connector:
                self._validate_type(value, input_connector.type, f"input '{name}'")

        self._connector_values[name] = value

    def get_input(self, name: str) -> Any:
        """Convenience method to get an input value.

        Args:
            name: Input connector name

        Returns:
            Current value of the input
        """
        return self._connector_values.get(name)

    def get_output(self, name: str) -> Any:
        """Convenience method to get an output value.

        Args:
            name: Output connector name

        Returns:
            Current value of the output
        """
        return self._connector_values.get(name)

    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter value.

        Args:
            name: Parameter name
            value: Parameter value
        """
        self._parameter_values[name] = value

    def get_parameter(self, name: str) -> Any:
        """Get a parameter value.

        Args:
            name: Parameter name

        Returns:
            Current value of the parameter
        """
        return self._parameter_values.get(name)

    def compute(self) -> None:
        """Execute block computation.

        Evaluates all equations in the block and updates output values.
        For composite blocks, executes all sub-blocks in order.
        """
        if self._block is None:
            return

        # Check if this is a composite block
        if hasattr(self._block, 'blocks') and hasattr(self._block, 'connections'):
            self._compute_composite()
        else:
            self._compute_elementary()

    def _compute_elementary(self) -> None:
        """Compute elementary block by evaluating equations."""
        # Build evaluation context with inputs and parameters
        eval_context = {}
        eval_context.update(self._connector_values)
        eval_context.update(self._parameter_values)

        # Add built-in functions
        eval_context['min'] = min
        eval_context['max'] = max
        eval_context['abs'] = abs

        # Evaluate equations if block has them
        equations = getattr(self._block, 'equations', [])
        for eq in equations:
            try:
                # Evaluate right-hand side
                result = eval(eq.rhs, {"__builtins__": {}}, eval_context)
                # Assign to left-hand side
                self._connector_values[eq.lhs] = result
                eval_context[eq.lhs] = result
            except Exception as e:
                raise RuntimeError(f"Error evaluating equation '{eq.lhs} = {eq.rhs}': {e}")

    def _compute_composite(self) -> None:
        """Compute composite block by executing sub-blocks."""
        # Create execution contexts for each sub-block
        sub_contexts = {}
        for block in self._block.blocks:
            sub_contexts[block.name] = ExecutionContext(block)

        # Build a simple execution order based on connections
        # For now, use a simple iterative approach: propagate values through connections
        # until all blocks have been computed

        max_iterations = len(self._block.blocks) + 1
        computed = set()

        for iteration in range(max_iterations):
            made_progress = False

            # Propagate values through all connections
            for conn in self._block.connections:
                from_block = conn.from_block
                to_block = conn.to_block

                # Get source value
                value = None
                if from_block in [inp.name for inp in self._block.inputs]:
                    # From composite input
                    value = self._connector_values.get(from_block)
                elif from_block in sub_contexts:
                    # From sub-block output
                    if from_block in computed:
                        value = sub_contexts[from_block].get_output(conn.from_output)

                # Set destination value
                if value is not None:
                    if to_block in sub_contexts:
                        # To sub-block input
                        sub_contexts[to_block].set_input(conn.to_input, value)
                    elif to_block in [out.name for out in self._block.outputs]:
                        # To composite output
                        self._connector_values[to_block] = value

            # Try to compute blocks that have all inputs set
            for block in self._block.blocks:
                if block.name not in computed:
                    # Check if all inputs are set
                    all_inputs_set = True
                    for inp in block.inputs:
                        if sub_contexts[block.name].get_input(inp.name) is None:
                            all_inputs_set = False
                            break

                    if all_inputs_set:
                        sub_contexts[block.name].compute()
                        computed.add(block.name)
                        made_progress = True

            if not made_progress:
                break

    def step(self) -> None:
        """Execute one step of the block.

        This is a simplified execution that updates step count and time.
        For composite blocks, this would evaluate all sub-blocks.
        """
        self.step_count += 1
        self.current_time += 1.0

        # Simple evaluation: for now, just compute y = min(yMax, k * e)
        if self._block is not None:
            # Get inputs
            e = self._connector_values.get('e', 0.0)
            yMax = self._connector_values.get('yMax', 100.0)

            # For elementary blocks with parameters
            k = 0.5  # Default gain
            if hasattr(self._block, 'parameters'):
                for param in self._block.parameters:
                    if param.name == 'k':
                        k = param.value

            # Simple computation: y = min(yMax, k * e)
            y = min(yMax, k * e)

            # Set output
            self._connector_values['y'] = y

    def has_value(self, connector_path: str) -> bool:
        """Check if a connector has a value.

        Args:
            connector_path: Full path to connector

        Returns:
            True if connector has been set, False otherwise
        """
        return connector_path in self._connector_values

    def reset(self) -> None:
        """Reset execution context to initial state."""
        self._connector_values.clear()
        self._connector_history.clear()
        self._write_count.clear()
        self._current_event = None
        self._event_history.clear()
        self.current_time = 0.0
        self.step_count = 0

        # Re-register block connectors if block exists
        if self._block is not None:
            for inp in getattr(self._block, 'inputs', []):
                self._connector_values[inp.name] = None
            for out in getattr(self._block, 'outputs', []):
                self._connector_values[out.name] = None
            # Reload default parameter values
            self._parameter_values.clear()
            for param in getattr(self._block, 'parameters', []):
                self._parameter_values[param.name] = param.value

    def clear(self) -> None:
        """Clear all values and history."""
        self._connector_values.clear()
        self._connector_history.clear()
        self._write_count.clear()
        self._current_event = None
        self._event_history.clear()

    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot of current state.

        Returns:
            Dictionary of connector paths to values
        """
        return self._connector_values.copy()

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore state from a snapshot.

        Args:
            snapshot: Dictionary of connector paths to values
        """
        self._connector_values = snapshot.copy()
        self._write_count.clear()
