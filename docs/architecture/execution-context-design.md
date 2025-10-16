# Python CDL - Execution Context Architecture

## Overview

This document defines the execution context architecture for running CDL control sequences in Python. The execution context manages block instances, signal flow, state management, and provides runtime services for CDL models.

## Design Goals

1. **Execution Isolation**: Each model instance has isolated state
2. **Efficient Evaluation**: Minimize overhead for large models with many blocks
3. **Signal Tracing**: Support debugging and monitoring of signal values
4. **Time Management**: Handle discrete and continuous time semantics
5. **State Persistence**: Save/restore execution state
6. **Extensibility**: Easy integration of custom blocks and operators

## Core Architecture Components

### 1. Execution Context

The execution context is the runtime environment for a CDL model.

```python
from typing import Protocol, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

@dataclass
class ExecutionConfig:
    """Configuration for execution context"""
    # Time stepping
    step_size: timedelta = field(default_factory=lambda: timedelta(seconds=1))
    start_time: datetime | None = None
    stop_time: datetime | None = None

    # Numerical settings
    tolerance: float = 1e-6
    max_iterations: int = 100

    # Runtime features
    enable_tracing: bool = False
    enable_validation: bool = True
    strict_mode: bool = True  # Strict type/connection checking

    # Logging
    log_level: int = logging.INFO

@dataclass
class ExecutionState:
    """Current state of execution"""
    current_time: datetime
    step_count: int = 0
    is_initialized: bool = False
    is_running: bool = False
    last_error: Exception | None = None

class ExecutionContext:
    """Runtime execution environment for CDL models"""

    def __init__(
        self,
        model: ClassDefinition,
        config: ExecutionConfig | None = None
    ) -> None:
        self.model = model
        self.config = config or ExecutionConfig()
        self.state = ExecutionState(
            current_time=self.config.start_time or datetime.now()
        )

        # Runtime data structures
        self._instances: dict[str, BlockInstance] = {}
        self._signals: SignalGraph = SignalGraph()
        self._evaluator: BlockEvaluator = BlockEvaluator()
        self._logger = logging.getLogger(f"cdl.context.{model.class_name}")

        # Performance tracking
        self._metrics = ExecutionMetrics()

    def initialize(self) -> None:
        """Initialize execution context"""
        self._logger.info(f"Initializing context for {self.model.class_name}")

        # Build instance tree
        self._build_instances()

        # Build signal graph
        self._build_signal_graph()

        # Validate model
        if self.config.enable_validation:
            self._validate_model()

        # Initialize block instances
        for instance in self._instances.values():
            instance.initialize(self)

        self.state.is_initialized = True
        self._logger.info("Context initialized successfully")

    def step(self) -> None:
        """Execute one time step"""
        if not self.state.is_initialized:
            raise RuntimeError("Context not initialized")

        self.state.is_running = True

        try:
            # Evaluate blocks in topological order
            for instance_name in self._signals.evaluation_order:
                instance = self._instances[instance_name]
                self._evaluator.evaluate(instance, self)

            # Advance time
            self.state.current_time += self.config.step_size
            self.state.step_count += 1

        except Exception as e:
            self.state.last_error = e
            self._logger.error(f"Error during step {self.state.step_count}: {e}")
            raise
        finally:
            self.state.is_running = False

    def run(self, steps: int | None = None) -> None:
        """Run simulation for specified steps or until stop_time"""
        if not self.state.is_initialized:
            self.initialize()

        max_steps = steps if steps else float("inf")
        step_count = 0

        while step_count < max_steps:
            if self.config.stop_time and self.state.current_time >= self.config.stop_time:
                break

            self.step()
            step_count += 1

        self._logger.info(f"Simulation completed: {step_count} steps")

    def get_signal_value(self, instance: str, connector: str) -> float | int | bool:
        """Get current value of a signal"""
        return self._signals.get_value(instance, connector)

    def set_signal_value(self, instance: str, connector: str, value: float | int | bool) -> None:
        """Set value of a signal (for inputs)"""
        self._signals.set_value(instance, connector, value)

    def get_instance(self, name: str) -> "BlockInstance":
        """Get block instance by name"""
        return self._instances[name]

    def snapshot(self) -> "ExecutionSnapshot":
        """Create snapshot of current state"""
        return ExecutionSnapshot.from_context(self)

    def restore(self, snapshot: "ExecutionSnapshot") -> None:
        """Restore state from snapshot"""
        snapshot.restore_to_context(self)

    # Private methods
    def _build_instances(self) -> None:
        """Build block instances from model"""
        for block in self.model.instances:
            instance = BlockInstanceFactory.create(block, self)
            self._instances[block.instance_name] = instance

    def _build_signal_graph(self) -> None:
        """Build signal dependency graph"""
        self._signals.build_from_connections(
            self.model.connections,
            self._instances
        )

    def _validate_model(self) -> None:
        """Validate model semantics"""
        validator = CDLValidator()
        errors = validator.validate_connections(self.model)
        if errors:
            raise ValueError(f"Model validation failed: {errors}")
```

### 2. Block Instance Runtime

```python
from abc import ABC, abstractmethod
from typing import Any

class BlockInstance(ABC):
    """Runtime instance of a CDL block"""

    def __init__(self, definition: ElementaryBlock | CompositeBlock) -> None:
        self.definition = definition
        self.name = definition.instance_name

        # Runtime state
        self._inputs: dict[str, Any] = {}
        self._outputs: dict[str, Any] = {}
        self._parameters: dict[str, Any] = {}
        self._state_vars: dict[str, Any] = {}

        # Metadata
        self._initialized = False
        self._last_update: datetime | None = None

    @abstractmethod
    def initialize(self, context: ExecutionContext) -> None:
        """Initialize block instance"""
        pass

    @abstractmethod
    def evaluate(self, context: ExecutionContext) -> None:
        """Evaluate block (compute outputs from inputs)"""
        pass

    def set_input(self, name: str, value: Any) -> None:
        """Set input value"""
        self._inputs[name] = value

    def get_output(self, name: str) -> Any:
        """Get output value"""
        return self._outputs.get(name)

    def get_parameter(self, name: str) -> Any:
        """Get parameter value"""
        return self._parameters.get(name)

    def set_parameter(self, name: str, value: Any) -> None:
        """Set parameter value"""
        self._parameters[name] = value

    def get_state(self, name: str) -> Any:
        """Get state variable"""
        return self._state_vars.get(name)

    def set_state(self, name: str, value: Any) -> None:
        """Set state variable"""
        self._state_vars[name] = value

class ElementaryBlockInstance(BlockInstance):
    """Instance of elementary (built-in) block"""

    def __init__(self, definition: ElementaryBlock) -> None:
        super().__init__(definition)
        self.definition: ElementaryBlock = definition

        # Load block implementation
        self._impl = BlockRegistry.get_implementation(definition.class_name)

    def initialize(self, context: ExecutionContext) -> None:
        """Initialize elementary block"""
        # Load parameters
        for name, param in self.definition.parameters.items():
            self._parameters[name] = param.value

        # Initialize implementation
        self._impl.initialize(self, context)
        self._initialized = True

    def evaluate(self, context: ExecutionContext) -> None:
        """Evaluate elementary block"""
        self._impl.evaluate(self, context)
        self._last_update = context.state.current_time

class CompositeBlockInstance(BlockInstance):
    """Instance of composite (user-defined) block"""

    def __init__(self, definition: CompositeBlock) -> None:
        super().__init__(definition)
        self.definition: CompositeBlock = definition

        # Nested context for internal model
        self._internal_context: ExecutionContext | None = None

    def initialize(self, context: ExecutionContext) -> None:
        """Initialize composite block"""
        # Create internal execution context
        # This involves recursively creating instances for nested blocks
        # Implementation depends on having the class definition
        self._initialized = True

    def evaluate(self, context: ExecutionContext) -> None:
        """Evaluate composite block by running internal context"""
        if self._internal_context:
            self._internal_context.step()

class BlockInstanceFactory:
    """Factory for creating block instances"""

    @staticmethod
    def create(
        definition: ElementaryBlock | CompositeBlock,
        context: ExecutionContext
    ) -> BlockInstance:
        """Create appropriate instance type"""
        if isinstance(definition, ElementaryBlock):
            return ElementaryBlockInstance(definition)
        else:
            return CompositeBlockInstance(definition)
```

### 3. Signal Graph and Data Flow

```python
from collections import defaultdict, deque
from typing import Iterator

@dataclass
class Signal:
    """Signal connecting blocks"""
    source: ConnectorReference  # Producer
    sinks: list[ConnectorReference]  # Consumers
    value: float | int | bool | None = None
    type_kind: CDLTypeKind = CDLTypeKind.REAL

class SignalGraph:
    """Directed graph of signal connections"""

    def __init__(self) -> None:
        # Adjacency lists for dependencies
        self._dependencies: dict[str, set[str]] = defaultdict(set)  # instance -> dependencies
        self._dependents: dict[str, set[str]] = defaultdict(set)  # instance -> dependents

        # Signal storage
        self._signals: dict[tuple[str, str], Signal] = {}  # (instance, connector) -> Signal

        # Cached evaluation order
        self._evaluation_order: list[str] = []

    def build_from_connections(
        self,
        connections: list[Connection],
        instances: dict[str, BlockInstance]
    ) -> None:
        """Build graph from connection list"""
        for conn in connections:
            # Add edge: from_instance -> to_instance
            from_inst = conn.from_ref.instance
            to_inst = conn.to_ref.instance

            self._dependencies[to_inst].add(from_inst)
            self._dependents[from_inst].add(to_inst)

            # Create or update signal
            signal_key = (from_inst, conn.from_ref.connector)
            if signal_key not in self._signals:
                self._signals[signal_key] = Signal(
                    source=conn.from_ref,
                    sinks=[]
                )
            self._signals[signal_key].sinks.append(conn.to_ref)

        # Compute evaluation order (topological sort)
        self._evaluation_order = self._topological_sort()

    def _topological_sort(self) -> list[str]:
        """Compute topological evaluation order using Kahn's algorithm"""
        # Calculate in-degrees
        in_degree: dict[str, int] = defaultdict(int)
        all_instances = set(self._dependencies.keys()) | set(self._dependents.keys())

        for instance in all_instances:
            in_degree[instance] = len(self._dependencies[instance])

        # Queue of instances with no dependencies
        queue = deque([inst for inst in all_instances if in_degree[inst] == 0])
        order = []

        while queue:
            instance = queue.popleft()
            order.append(instance)

            # Reduce in-degree for dependents
            for dependent in self._dependents[instance]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(order) != len(all_instances):
            # Find cycle for error message
            cycle = self._find_cycle()
            raise ValueError(f"Algebraic loop detected: {' -> '.join(cycle)}")

        return order

    def _find_cycle(self) -> list[str]:
        """Find a cycle in the dependency graph for error reporting"""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependents[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self._dependencies.keys():
            if node not in visited:
                result = dfs(node)
                if result:
                    return result

        return []

    def get_value(self, instance: str, connector: str) -> Any:
        """Get signal value"""
        signal = self._signals.get((instance, connector))
        return signal.value if signal else None

    def set_value(self, instance: str, connector: str, value: Any) -> None:
        """Set signal value"""
        signal_key = (instance, connector)
        if signal_key not in self._signals:
            # Create new signal (for inputs)
            self._signals[signal_key] = Signal(
                source=ConnectorReference(instance=instance, connector=connector),
                sinks=[]
            )
        self._signals[signal_key].value = value

    @property
    def evaluation_order(self) -> list[str]:
        """Get cached evaluation order"""
        return self._evaluation_order
```

### 4. Block Evaluator

```python
class BlockEvaluator:
    """Evaluates block instances"""

    def evaluate(self, instance: BlockInstance, context: ExecutionContext) -> None:
        """Evaluate a block instance"""
        # Fetch input values from signal graph
        self._fetch_inputs(instance, context)

        # Execute block logic
        instance.evaluate(context)

        # Publish output values to signal graph
        self._publish_outputs(instance, context)

    def _fetch_inputs(self, instance: BlockInstance, context: ExecutionContext) -> None:
        """Fetch input values from connected signals"""
        # For each input connector, get value from signal graph
        # and set on instance
        pass

    def _publish_outputs(self, instance: BlockInstance, context: ExecutionContext) -> None:
        """Publish output values to signal graph"""
        # For each output connector, get value from instance
        # and set in signal graph
        pass
```

### 5. State Management and Persistence

```python
from typing import Any
import pickle

@dataclass
class ExecutionSnapshot:
    """Snapshot of execution state"""
    timestamp: datetime
    step_count: int
    signal_values: dict[tuple[str, str], Any]
    instance_states: dict[str, dict[str, Any]]

    @classmethod
    def from_context(cls, context: ExecutionContext) -> "ExecutionSnapshot":
        """Create snapshot from context"""
        return cls(
            timestamp=context.state.current_time,
            step_count=context.state.step_count,
            signal_values={
                key: signal.value
                for key, signal in context._signals._signals.items()
            },
            instance_states={
                name: instance._state_vars.copy()
                for name, instance in context._instances.items()
            }
        )

    def restore_to_context(self, context: ExecutionContext) -> None:
        """Restore snapshot to context"""
        context.state.current_time = self.timestamp
        context.state.step_count = self.step_count

        # Restore signal values
        for key, value in self.signal_values.items():
            context._signals.set_value(key[0], key[1], value)

        # Restore instance states
        for name, state in self.instance_states.items():
            instance = context._instances[name]
            instance._state_vars = state.copy()

    def save(self, file_path: Path) -> None:
        """Save snapshot to file"""
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, file_path: Path) -> "ExecutionSnapshot":
        """Load snapshot from file"""
        with open(file_path, "rb") as f:
            return pickle.load(f)
```

### 6. Execution Metrics and Monitoring

```python
from dataclasses import dataclass, field
from time import perf_counter

@dataclass
class ExecutionMetrics:
    """Performance metrics for execution"""
    total_steps: int = 0
    total_time: float = 0.0
    avg_step_time: float = 0.0
    block_evaluations: dict[str, int] = field(default_factory=dict)
    block_times: dict[str, float] = field(default_factory=dict)

    def record_step(self, duration: float) -> None:
        """Record step execution time"""
        self.total_steps += 1
        self.total_time += duration
        self.avg_step_time = self.total_time / self.total_steps

    def record_block_evaluation(self, block_name: str, duration: float) -> None:
        """Record block evaluation"""
        self.block_evaluations[block_name] = \
            self.block_evaluations.get(block_name, 0) + 1
        self.block_times[block_name] = \
            self.block_times.get(block_name, 0.0) + duration
```

## Usage Examples

### Basic Execution

```python
# Load CDL model
model = load_cdl_document(Path("model.json")).main_class

# Create execution context
config = ExecutionConfig(
    step_size=timedelta(seconds=0.1),
    stop_time=datetime.now() + timedelta(minutes=10)
)
context = ExecutionContext(model, config)

# Run simulation
context.run()

# Get results
output_value = context.get_signal_value("controller", "y")
```

### Real-time Execution with External I/O

```python
# Create context
context = ExecutionContext(model)
context.initialize()

# Real-time loop
while True:
    # Read sensor
    sensor_value = read_sensor()
    context.set_signal_value("sensor_input", "u", sensor_value)

    # Execute step
    context.step()

    # Write actuator
    actuator_value = context.get_signal_value("controller", "y")
    write_actuator(actuator_value)

    time.sleep(0.1)  # 10 Hz update rate
```

### State Persistence

```python
# Run simulation and checkpoint
context = ExecutionContext(model)
context.run(steps=1000)

# Save state
snapshot = context.snapshot()
snapshot.save(Path("checkpoint.pkl"))

# Later: restore and continue
snapshot = ExecutionSnapshot.load(Path("checkpoint.pkl"))
context = ExecutionContext(model)
context.initialize()
context.restore(snapshot)
context.run(steps=1000)  # Continue from checkpoint
```

## Integration Points

1. **I/O Adapters**: Connect to real hardware, databases, message queues
2. **Logging**: Structured logging of signals and events
3. **Tracing**: Record signal values over time for analysis
4. **Debugging**: Step through execution, inspect state
5. **Testing**: Inject test inputs, verify outputs

## Next Steps

1. Implement `ExecutionContext` core functionality
2. Build `SignalGraph` with topological sorting
3. Create `BlockInstance` base classes
4. Implement elementary block registry
5. Add state persistence
6. Create execution monitoring and tracing
