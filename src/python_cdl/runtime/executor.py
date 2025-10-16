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

        try:
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
            elif isinstance(block, ElementaryBlock):
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

            self.context.end_event()

            # Calculate execution time
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()

            return result

        except Exception as e:
            # Ensure event is ended even on error
            if self.context.current_event is not None:
                self.context.end_event()

            end_time = datetime.now()
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=(end_time - start_time).total_seconds(),
            )

    def _execute_elementary(self, block: ElementaryBlock) -> ExecutionResult:
        """Execute an elementary block.

        Elementary blocks should have custom implementations registered.
        This is a placeholder that demonstrates the structure.
        """
        # In a real implementation, you would look up and call
        # the registered implementation for this block type
        return ExecutionResult(
            success=True,
            blocks_executed=[block.name],
        )

    def _execute_composite(self, block: CompositeBlock) -> ExecutionResult:
        """Execute a generic composite block.

        Executes all child blocks respecting connections.
        """
        executed = []

        # Execute child blocks (simplified - real implementation would
        # need to respect connection dependencies)
        for child in block.blocks:
            child_result = self._execute_child(child, block)
            executed.append(child.name)

            if not child_result.success:
                return ExecutionResult(
                    success=False,
                    error=f"Child block {child.name} failed: {child_result.error}",
                    blocks_executed=executed,
                )

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
        # Collect inputs from connections
        inputs = {}
        for conn in parent.connections:
            if conn.to_block == child.name:
                source_path = f"{parent.name}.{conn.from_block}.{conn.from_output}"
                if self.context.has_value(source_path):
                    inputs[conn.to_input] = self.context.get_value(source_path)

        # Execute child (recursively handles nested composite blocks)
        return self.execute(child, inputs)
