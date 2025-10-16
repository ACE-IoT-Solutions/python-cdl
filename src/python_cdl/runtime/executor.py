"""Block executor for running CDL blocks."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from python_cdl.models.blocks import (
    Block,
    CompositeBlock,
    ElementaryBlock,
    IfBlock,
    ParallelBlock,
    SequenceBlock,
    WhileBlock,
)
from python_cdl.runtime.context import ExecutionContext, ExecutionEvent


@dataclass
class ExecutionResult:
    """Result of block execution."""

    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time: float = 0.0
    blocks_executed: list[str] = field(default_factory=list)


class BlockExecutor:
    """Executor for CDL blocks.

    Handles execution of elementary, composite, and control flow blocks
    according to CDL semantics.
    """

    def __init__(self, context: ExecutionContext | None = None):
        """Initialize executor.

        Args:
            context: Execution context to use (creates new if None)
        """
        self.context = context or ExecutionContext()

    def execute(
        self,
        block: Block,
        inputs: dict[str, Any] | None = None,
        event: ExecutionEvent | None = None,
    ) -> ExecutionResult:
        """Execute a block.

        Args:
            block: Block to execute
            inputs: Input values (connector name -> value)
            event: Execution event (creates default if None)

        Returns:
            ExecutionResult containing outputs and status
        """
        start_time = datetime.now()

        # Set up execution event
        if event is None:
            from python_cdl.runtime.context import ExecutionEventType

            event = ExecutionEvent(
                event_type=ExecutionEventType.EXTERNAL, data=inputs or {}
            )

        # Check if we're already in an event (nested execution)
        already_in_event = self.context.current_event is not None

        try:
            if not already_in_event:
                self.context.begin_event(event)

            # Set input values in context
            if inputs:
                for input_name, value in inputs.items():
                    connector_path = f"{block.name}.{input_name}"
                    self.context.set_value(connector_path, value)

            # Execute based on block type
            if isinstance(block, SequenceBlock):
                result = self._execute_sequence(block)
            elif isinstance(block, ParallelBlock):
                result = self._execute_parallel(block)
            elif isinstance(block, IfBlock):
                result = self._execute_if(block)
            elif isinstance(block, WhileBlock):
                result = self._execute_while(block)
            elif isinstance(block, CompositeBlock):
                result = self._execute_composite(block)
            elif isinstance(block, ElementaryBlock) or block.block_type == 'elementary':
                result = self._execute_elementary(block)
            else:
                result = ExecutionResult(
                    success=False,
                    error=f"Unsupported block type: {type(block).__name__}",
                )

            # Collect output values
            for output in block.outputs:
                connector_path = f"{block.name}.{output.name}"
                if self.context.has_value(connector_path):
                    result.outputs[output.name] = self.context.get_value(
                        connector_path
                    )

            # Only end event if we started it
            if not already_in_event:
                self.context.end_event()

            # Calculate execution time
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()

            return result

        except Exception as e:
            # Ensure event is ended even on error (only if we started it)
            if not already_in_event and self.context.current_event is not None:
                self.context.end_event()

            end_time = datetime.now()
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=(end_time - start_time).total_seconds(),
            )

    def _execute_elementary(self, block: ElementaryBlock | Block) -> ExecutionResult:
        """Execute an elementary block.

        Executes equations in order, evaluating expressions and storing results.
        """
        try:
            # Create local namespace with parameters and inputs
            namespace = {}

            # Add parameters
            for param in getattr(block, 'parameters', []):
                param_value = self.context.get_parameter(param.name)
                namespace[param.name] = param_value if param_value is not None else param.value

            # Add input values
            for inp in getattr(block, 'inputs', []):
                connector_path = f"{block.name}.{inp.name}"
                if self.context.has_value(connector_path):
                    namespace[inp.name] = self.context.get_value(connector_path)

            # Execute equations in order
            # Provide safe built-in functions for control algorithms
            safe_builtins = {
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sum': sum,
                'len': len,
                'range': range,
                'int': int,
                'float': float,
                'bool': bool,
                'str': str,
            }

            for eq in getattr(block, 'equations', []):
                # Evaluate right-hand side
                try:
                    result_value = eval(eq.rhs, {"__builtins__": safe_builtins}, namespace)
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Error evaluating equation '{eq.lhs} = {eq.rhs}': {e}",
                        blocks_executed=[block.name],
                    )

                # Store result in namespace for subsequent equations
                namespace[eq.lhs] = result_value

                # If this is an output, set it in context
                output_names = [out.name for out in getattr(block, 'outputs', [])]
                if eq.lhs in output_names:
                    connector_path = f"{block.name}.{eq.lhs}"
                    self.context.set_value(connector_path, result_value)

            return ExecutionResult(
                success=True,
                blocks_executed=[block.name],
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Elementary block execution failed: {e}",
                blocks_executed=[block.name],
            )

    def _execute_composite(self, block: CompositeBlock) -> ExecutionResult:
        """Execute a generic composite block.

        Executes all child blocks respecting connections.
        """
        executed = []

        # Build dependency graph from connections
        child_names = {child.name for child in block.blocks}
        dependencies = {child.name: set() for child in block.blocks}

        for conn in block.connections:
            # Only track dependencies between child blocks
            if conn.to_block in child_names and conn.from_block in child_names:
                # to_block depends on from_block
                dependencies[conn.to_block].add(conn.from_block)

        # Topological sort to determine execution order
        execution_order = []
        remaining = set(child_names)

        while remaining:
            # Find blocks with no remaining dependencies
            ready = [
                name for name in remaining
                if not dependencies[name] or dependencies[name].issubset(execution_order)
            ]

            if not ready:
                # Circular dependency detected
                return ExecutionResult(
                    success=False,
                    error=f"Circular dependency detected among blocks: {remaining}",
                    blocks_executed=executed,
                )

            # Execute ready blocks
            for block_name in ready:
                child = next((b for b in block.blocks if b.name == block_name), None)
                if not child:
                    return ExecutionResult(
                        success=False,
                        error=f"Block {block_name} not found",
                        blocks_executed=executed,
                    )

                child_result = self._execute_child(child, block)
                executed.append(child.name)
                execution_order.append(child.name)

                if not child_result.success:
                    return ExecutionResult(
                        success=False,
                        error=f"Child block {child.name} failed: {child_result.error}",
                        blocks_executed=executed,
                    )

                remaining.remove(block_name)

        # Map child outputs to parent outputs based on connections
        for conn in block.connections:
            # Check if this connection maps a child output to a parent output
            # Pattern: from_block is a child, to_block is NOT a child (it's a parent output)
            if conn.from_block in child_names and conn.to_block not in child_names:
                # This is a child -> parent output connection
                source_path = f"{block.name}.{conn.from_block}.{conn.from_output}"
                target_path = f"{block.name}.{conn.to_block}"

                if self.context.has_value(source_path):
                    value = self.context.get_value(source_path)
                    self.context.set_value(target_path, value)

        return ExecutionResult(success=True, blocks_executed=executed)

    def _execute_sequence(self, block: SequenceBlock) -> ExecutionResult:
        """Execute a sequence block.

        Executes blocks in the specified order.
        """
        executed = []

        # Execute in order
        for block_name in block.execution_order:
            child = next((b for b in block.blocks if b.name == block_name), None)
            if not child:
                return ExecutionResult(
                    success=False,
                    error=f"Block {block_name} not found in sequence",
                    blocks_executed=executed,
                )

            child_result = self._execute_child(child, block)
            executed.append(child.name)

            if not child_result.success:
                return ExecutionResult(
                    success=False,
                    error=f"Sequence failed at {child.name}: {child_result.error}",
                    blocks_executed=executed,
                )

        return ExecutionResult(success=True, blocks_executed=executed)

    def _execute_parallel(self, block: ParallelBlock) -> ExecutionResult:
        """Execute a parallel block.

        In a synchronous model, this executes blocks that don't depend
        on each other in any order (simulated parallelism).
        """
        executed = []

        # Execute all blocks (in practice, would execute independent groups)
        for child in block.blocks:
            child_result = self._execute_child(child, block)
            executed.append(child.name)

            if not child_result.success:
                return ExecutionResult(
                    success=False,
                    error=f"Parallel block {child.name} failed: {child_result.error}",
                    blocks_executed=executed,
                )

        return ExecutionResult(success=True, blocks_executed=executed)

    def _execute_if(self, block: IfBlock) -> ExecutionResult:
        """Execute an if block.

        Executes then or else branch based on condition.
        """
        executed = []

        # Get condition value
        condition_path = f"{block.name}.{block.condition_input}"
        if not self.context.has_value(condition_path):
            return ExecutionResult(
                success=False,
                error=f"Condition input {block.condition_input} not set",
                blocks_executed=executed,
            )

        condition = self.context.get_value(condition_path)

        # Execute appropriate branch
        branch = block.then_blocks if condition else block.else_blocks

        for block_name in branch:
            child = next((b for b in block.blocks if b.name == block_name), None)
            if not child:
                return ExecutionResult(
                    success=False,
                    error=f"Block {block_name} not found in if branch",
                    blocks_executed=executed,
                )

            child_result = self._execute_child(child, block)
            executed.append(child.name)

            if not child_result.success:
                return ExecutionResult(
                    success=False,
                    error=f"If branch failed at {child.name}: {child_result.error}",
                    blocks_executed=executed,
                )

        return ExecutionResult(success=True, blocks_executed=executed)

    def _execute_while(self, block: WhileBlock) -> ExecutionResult:
        """Execute a while loop block.

        Executes loop body while condition is true.
        """
        executed = []
        iterations = 0
        max_iter = block.max_iterations or 1000  # Default safety limit

        while iterations < max_iter:
            # Check condition
            condition_path = f"{block.name}.{block.condition_input}"
            if not self.context.has_value(condition_path):
                return ExecutionResult(
                    success=False,
                    error=f"Condition input {block.condition_input} not set",
                    blocks_executed=executed,
                )

            condition = self.context.get_value(condition_path)
            if not condition:
                break

            # Execute loop body
            for block_name in block.loop_blocks:
                child = next(
                    (b for b in block.blocks if b.name == block_name), None
                )
                if not child:
                    return ExecutionResult(
                        success=False,
                        error=f"Block {block_name} not found in loop",
                        blocks_executed=executed,
                    )

                child_result = self._execute_child(child, block)
                executed.append(child.name)

                if not child_result.success:
                    return ExecutionResult(
                        success=False,
                        error=f"Loop failed at {child.name}: {child_result.error}",
                        blocks_executed=executed,
                    )

            iterations += 1

        if iterations >= max_iter:
            return ExecutionResult(
                success=False,
                error=f"While loop exceeded maximum iterations: {max_iter}",
                blocks_executed=executed,
            )

        return ExecutionResult(success=True, blocks_executed=executed)

    def _execute_child(
        self, child: Block, parent: CompositeBlock
    ) -> ExecutionResult:
        """Execute a child block within a composite block.

        Args:
            child: Child block to execute
            parent: Parent composite block

        Returns:
            ExecutionResult for the child execution
        """
        # Get list of child block names to distinguish from parent inputs
        child_names = {block.name for block in parent.blocks}

        # Collect inputs from connections and set them in context
        for conn in parent.connections:
            if conn.to_block == child.name:
                # Determine if source is a parent input or another child block
                # Check if from_output is empty (indicates parent input)
                if not conn.from_output or conn.from_output == "":
                    # Connection from parent input
                    source_path = f"{parent.name}.{conn.from_block}"
                elif conn.from_block in child_names:
                    # Connection from another child block
                    source_path = f"{parent.name}.{conn.from_block}.{conn.from_output}"
                else:
                    # Connection from parent input with explicit connector
                    source_path = f"{parent.name}.{conn.from_block}"

                if self.context.has_value(source_path):
                    # Set the value with the full path including parent
                    target_path = f"{parent.name}.{conn.to_block}.{conn.to_input}"
                    value = self.context.get_value(source_path)
                    self.context.set_value(target_path, value)

        # Execute child directly without creating a new event
        # The child's name needs to be fully qualified with parent
        if isinstance(child, ElementaryBlock) or child.block_type == 'elementary':
            return self._execute_elementary_child(child, parent)
        elif isinstance(child, CompositeBlock):
            return self._execute_composite_child(child, parent)
        else:
            return ExecutionResult(
                success=False,
                error=f"Unsupported child block type: {type(child).__name__}",
            )

    def _execute_elementary_child(self, child: ElementaryBlock | Block, parent: CompositeBlock) -> ExecutionResult:
        """Execute an elementary child block within a composite block."""
        try:
            # Create local namespace with parameters and inputs
            namespace = {}

            # Add parameters
            for param in getattr(child, 'parameters', []):
                param_value = self.context.get_parameter(param.name)
                namespace[param.name] = param_value if param_value is not None else param.value

            # Add input values (with full path)
            for inp in getattr(child, 'inputs', []):
                connector_path = f"{parent.name}.{child.name}.{inp.name}"
                if self.context.has_value(connector_path):
                    namespace[inp.name] = self.context.get_value(connector_path)

            # Execute equations with safe built-ins
            safe_builtins = {
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sum': sum,
                'len': len,
                'range': range,
                'int': int,
                'float': float,
                'bool': bool,
                'str': str,
            }

            for eq in getattr(child, 'equations', []):
                # Evaluate right-hand side
                try:
                    result_value = eval(eq.rhs, {"__builtins__": safe_builtins}, namespace)
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Error evaluating equation '{eq.lhs} = {eq.rhs}': {e}",
                        blocks_executed=[child.name],
                    )

                # Store result in namespace for subsequent equations
                namespace[eq.lhs] = result_value

                # If this is an output, set it in context (with full path)
                output_names = [out.name for out in getattr(child, 'outputs', [])]
                if eq.lhs in output_names:
                    connector_path = f"{parent.name}.{child.name}.{eq.lhs}"
                    self.context.set_value(connector_path, result_value)

            return ExecutionResult(
                success=True,
                blocks_executed=[child.name],
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Elementary child block execution failed: {e}",
                blocks_executed=[child.name],
            )

    def _execute_composite_child(self, child: CompositeBlock, parent: CompositeBlock) -> ExecutionResult:
        """Execute a composite child block within another composite block."""
        # For nested composites, we need to handle them differently
        # For now, just return an error as this is a complex case
        return ExecutionResult(
            success=False,
            error="Nested composite blocks not yet fully implemented",
        )
