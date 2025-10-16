"""Graph validator for detecting cycles and validating connections."""

from collections import defaultdict, deque

from python_cdl.models.blocks import CompositeBlock


def detect_cycles(block: CompositeBlock) -> list[list[str]]:
    """Detect cycles in block connection graph.

    CDL requires directed acyclic graphs (DAGs). This function detects
    any cycles in the connection graph.

    Args:
        block: Composite block to check

    Returns:
        List of cycles, where each cycle is a list of block names
    """
    # Build adjacency list
    graph: dict[str, list[str]] = defaultdict(list)

    for conn in block.connections:
        graph[conn.from_block].append(conn.to_block)

    # Get all block names
    all_blocks = {b.name for b in block.blocks}

    # Detect cycles using DFS
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> bool:
        """DFS to detect cycles."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
                return True

        path.pop()
        rec_stack.remove(node)
        return False

    # Check each block
    for block_name in all_blocks:
        if block_name not in visited:
            dfs(block_name)

    return cycles


def validate_connections(block: CompositeBlock) -> list[str]:
    """Validate connection rules for a composite block.

    CDL rules:
    1. Each input must connect to exactly one output
    2. An output can connect to multiple inputs
    3. No dangling connections

    Args:
        block: Composite block to validate

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    # Track input connections
    input_connections: dict[str, list[str]] = defaultdict(list)

    for conn in block.connections:
        input_key = f"{conn.to_block}.{conn.to_input}"
        output_key = f"{conn.from_block}.{conn.from_output}"
        input_connections[input_key].append(output_key)

    # Check each input has exactly one connection
    for child in block.blocks:
        for inp in child.inputs:
            input_key = f"{child.name}.{inp.name}"
            conn_count = len(input_connections.get(input_key, []))

            if conn_count == 0:
                # This is a warning, not necessarily an error
                # (could be an external input)
                pass
            elif conn_count > 1:
                errors.append(
                    f"Input '{input_key}' has multiple connections: "
                    f"{input_connections[input_key]}"
                )

    return errors


def topological_sort(block: CompositeBlock) -> list[str] | None:
    """Perform topological sort on block connections.

    Returns execution order if graph is acyclic, None if cycles exist.

    Args:
        block: Composite block to sort

    Returns:
        List of block names in execution order, or None if cycles exist
    """
    # Build graph
    graph: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = defaultdict(int)

    all_blocks = {b.name for b in block.blocks}

    for block_name in all_blocks:
        if block_name not in in_degree:
            in_degree[block_name] = 0

    for conn in block.connections:
        graph[conn.from_block].append(conn.to_block)
        in_degree[conn.to_block] += 1

    # Kahn's algorithm
    queue = deque([b for b in all_blocks if in_degree[b] == 0])
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)

        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If not all blocks processed, there's a cycle
    if len(result) != len(all_blocks):
        return None

    return result


class GraphValidator:
    """Validator for block connection graphs."""

    @staticmethod
    def validate(block: CompositeBlock) -> tuple[bool, list[str]]:
        """Validate block graph.

        Args:
            block: Composite block to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Check for cycles
        cycles = detect_cycles(block)
        if cycles:
            for cycle in cycles:
                errors.append(f"Cycle detected: {' -> '.join(cycle)}")

        # Check connection rules
        conn_errors = validate_connections(block)
        errors.extend(conn_errors)

        return len(errors) == 0, errors

    @staticmethod
    def get_execution_order(block: CompositeBlock) -> list[str] | None:
        """Get valid execution order for blocks.

        Args:
            block: Composite block

        Returns:
            List of block names in valid execution order, or None if cycles exist
        """
        return topological_sort(block)
