"""Validator for CDL blocks."""

from dataclasses import dataclass, field

from python_cdl.models.blocks import Block, CompositeBlock


class ValidationError(Exception):
    """Exception raised when validation fails."""

    pass


@dataclass
class ValidationMessage:
    """A validation error or warning message."""

    message: str
    severity: str = "error"  # "error" or "warning"
    context: str | None = None

    def __str__(self) -> str:
        """String representation of the validation message."""
        return self.message


@dataclass
class ValidationResult:
    """Result of block validation."""

    valid: bool
    errors: list[ValidationMessage] = field(default_factory=list)
    warnings: list[ValidationMessage] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Alias for valid attribute for consistency."""
        return self.valid


class BlockValidator:
    """Validator for CDL blocks.

    Ensures blocks comply with CDL rules:
    - Unique names within a composite block
    - Valid connections
    - Input/output type compatibility
    - Acyclic dependency graphs
    """

    def validate(self, block: Block) -> ValidationResult:
        """Validate a block.

        Args:
            block: Block to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # Check basic block properties
        if not block.name or not block.name.strip():
            result.errors.append(ValidationMessage(message="Block name cannot be empty"))
            result.valid = False

        # Validate composite blocks
        if isinstance(block, CompositeBlock):
            self._validate_composite(block, result)

        # Validate connectors
        self._validate_connectors(block, result)

        # Set overall validity
        result.valid = len(result.errors) == 0

        return result

    def _validate_composite(
        self, block: CompositeBlock, result: ValidationResult
    ) -> None:
        """Validate composite block specific rules."""
        # Check for unique child block names
        child_names = [b.name for b in block.blocks]
        duplicates = [name for name in child_names if child_names.count(name) > 1]

        if duplicates:
            result.errors.append(
                ValidationMessage(
                    message=f"Duplicate child block names in {block.name}: {set(duplicates)}",
                    context=block.name
                )
            )

        # Validate connections
        # Build list of valid connection endpoints (child blocks + composite boundary)
        input_names = {inp.name for inp in block.inputs}
        output_names = {out.name for out in block.outputs}

        for conn in block.connections:
            # Check source exists (can be child block or composite input)
            source_block = None
            source_is_boundary = conn.from_block in input_names

            if not source_is_boundary:
                source_block = next(
                    (b for b in block.blocks if b.name == conn.from_block), None
                )
                if not source_block:
                    result.errors.append(
                        ValidationMessage(
                            message=f"Connection source block '{conn.from_block}' not found in {block.name}",
                            context=f"{block.name}.{conn.from_block}"
                        )
                    )
                    continue

            # Check target exists (can be child block or composite output)
            target_block = None
            target_is_boundary = conn.to_block in output_names

            if not target_is_boundary:
                target_block = next(
                    (b for b in block.blocks if b.name == conn.to_block), None
                )
                if not target_block:
                    result.errors.append(
                        ValidationMessage(
                            message=f"Connection target block '{conn.to_block}' not found in {block.name}",
                            context=f"{block.name}.{conn.to_block}"
                        )
                    )
                    continue

            # Validate connectors if not boundary connections
            if not source_is_boundary and source_block:
                # Check source output exists
                source_output = source_block.get_output(conn.from_output)
                if not source_output:
                    result.errors.append(
                        ValidationMessage(
                            message=f"Output '{conn.from_output}' not found in block '{conn.from_block}'",
                            context=f"{conn.from_block}.{conn.from_output}"
                        )
                    )
                    continue

            if not target_is_boundary and target_block:
                # Check target input exists
                target_input = target_block.get_input(conn.to_input)
                if not target_input:
                    result.errors.append(
                        ValidationMessage(
                            message=f"Input '{conn.to_input}' not found in block '{conn.to_block}'",
                            context=f"{conn.to_block}.{conn.to_input}"
                        )
                    )
                    continue

                # Check type compatibility (if we have both connectors)
                if not source_is_boundary and source_block:
                    source_output = source_block.get_output(conn.from_output)
                    if source_output and source_output.type != target_input.type:
                        result.warnings.append(
                            ValidationMessage(
                                message=f"Type mismatch in connection: {conn.from_path} "
                                f"({source_output.type}) -> {conn.to_path} ({target_input.type})",
                                severity="warning",
                                context=f"{conn.from_path} -> {conn.to_path}"
                            )
                        )

        # Recursively validate child blocks
        for child in block.blocks:
            child_result = self.validate(child)
            result.errors.extend(child_result.errors)
            result.warnings.extend(child_result.warnings)

    def _validate_connectors(self, block: Block, result: ValidationResult) -> None:
        """Validate connector rules."""
        # Check for unique input names
        input_names = [inp.name for inp in block.inputs]
        duplicates = [name for name in input_names if input_names.count(name) > 1]
        if duplicates:
            result.errors.append(
                ValidationMessage(
                    message=f"Duplicate input names in {block.name}: {set(duplicates)}",
                    context=block.name
                )
            )

        # Check for unique output names
        output_names = [out.name for out in block.outputs]
        duplicates = [name for name in output_names if output_names.count(name) > 1]
        if duplicates:
            result.errors.append(
                ValidationMessage(
                    message=f"Duplicate output names in {block.name}: {set(duplicates)}",
                    context=block.name
                )
            )

        # Check for name conflicts between inputs and outputs
        name_conflicts = set(input_names) & set(output_names)
        if name_conflicts:
            result.warnings.append(
                ValidationMessage(
                    message=f"Name conflicts between inputs and outputs in {block.name}: {name_conflicts}",
                    severity="warning",
                    context=block.name
                )
            )
