"""Matplotlib-based renderer for CDL blocks."""

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.figure import Figure

from python_cdl.models.blocks import Block, CompositeBlock, ElementaryBlock
from .block_visualizer import VisualizationStyle


@dataclass
class MatplotlibRenderer:
    """Render CDL blocks using matplotlib.

    Creates clean, publication-quality diagrams with customizable styling.
    """

    style: VisualizationStyle = VisualizationStyle.DETAILED
    show_parameters: bool = True
    show_equations: bool = True
    show_types: bool = True
    figsize: tuple[float, float] = (14, 10)
    dpi: int = 150

    # Color scheme
    input_color: str = 'lightblue'
    output_color: str = 'lightyellow'
    elementary_color: str = 'lightgreen'
    composite_color: str = 'lightcoral'
    connection_color: str = 'black'

    def render(self, block: Block, **kwargs) -> Figure:
        """Render a block to a matplotlib figure.

        Args:
            block: Block to visualize
            **kwargs: Additional rendering options

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        if isinstance(block, CompositeBlock):
            self._render_composite(ax, block)
        elif isinstance(block, ElementaryBlock) or block.block_type == 'elementary':
            self._render_elementary(ax, block)
        else:
            self._render_elementary(ax, block)

        # Add title
        title = f"{block.name}"
        if self.show_types:
            title += f" ({block.block_type})"
        ax.text(5, 9.5, title, ha='center', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return fig

    def _render_composite(self, ax, block: CompositeBlock):
        """Render a composite block with child blocks and connections."""
        # Calculate layout
        num_blocks = len(block.blocks)
        num_inputs = len(block.inputs)
        num_outputs = len(block.outputs)

        # Position inputs on left
        input_positions = {}
        input_y_start = 5 + (num_inputs - 1) * 0.5
        for i, inp in enumerate(block.inputs):
            y = input_y_start - i * 1.0
            input_positions[inp.name] = (1, y)
            self._draw_connector(ax, 1, y, inp.name, 'input', inp.type if hasattr(inp, 'type') else '')

        # Position outputs on right
        output_positions = {}
        output_y_start = 5 + (num_outputs - 1) * 0.5
        for i, out in enumerate(block.outputs):
            y = output_y_start - i * 1.0
            output_positions[out.name] = (9, y)
            self._draw_connector(ax, 9, y, out.name, 'output', out.type if hasattr(out, 'type') else '')

        # Position child blocks in middle
        child_positions = {}
        child_y_start = 5 + (num_blocks - 1) * 0.75
        for i, child in enumerate(block.blocks):
            x = 3 + (i % 2) * 2.5  # Alternate between two columns
            y = child_y_start - (i // 2) * 1.5
            child_positions[child.name] = (x, y)
            self._draw_block(ax, x, y, child)

        # Draw connections
        self._draw_connections(ax, block, input_positions, output_positions, child_positions)

    def _render_elementary(self, ax, block: Block):
        """Render an elementary block with inputs, outputs, and optionally equations."""
        # Draw central block
        self._draw_block(ax, 5, 5, block, width=2.5, height=2.0)

        # Position inputs on left
        num_inputs = len(block.inputs)
        input_y_start = 5 + (num_inputs - 1) * 0.4
        for i, inp in enumerate(block.inputs):
            y = input_y_start - i * 0.8
            self._draw_connector(ax, 2, y, inp.name, 'input', inp.type if hasattr(inp, 'type') else '')
            # Draw arrow to block
            ax.add_patch(FancyArrowPatch((2.7, y), (3.5, 5),
                                        arrowstyle='->', lw=2, color=self.connection_color))

        # Position outputs on right
        num_outputs = len(block.outputs)
        output_y_start = 5 + (num_outputs - 1) * 0.4
        for i, out in enumerate(block.outputs):
            y = output_y_start - i * 0.8
            self._draw_connector(ax, 8, y, out.name, 'output', out.type if hasattr(out, 'type') else '')
            # Draw arrow from block
            ax.add_patch(FancyArrowPatch((6.5, 5), (7.3, y),
                                        arrowstyle='->', lw=2, color=self.connection_color))

    def _draw_block(self, ax, x: float, y: float, block: Block, width: float = 1.5, height: float = 1.2):
        """Draw a block box."""
        is_composite = isinstance(block, CompositeBlock)
        color = self.composite_color if is_composite else self.elementary_color

        # Draw box
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                            boxstyle="round,pad=0.1",
                            facecolor=color, edgecolor='black', linewidth=2.5)
        ax.add_patch(box)

        # Block name
        ax.text(x, y + 0.15, block.name, ha='center', va='center',
               fontsize=11, fontweight='bold')

        # Block type or equations
        if self.style == VisualizationStyle.DETAILED:
            if self.show_equations and hasattr(block, 'equations') and block.equations:
                # Show first equation as example
                eq = block.equations[0]
                eq_text = f"{eq.lhs} = {eq.rhs}"
                if len(eq_text) > 20:
                    eq_text = eq_text[:17] + "..."
                ax.text(x, y - 0.15, eq_text, ha='center', va='center',
                       fontsize=8, style='italic')
            elif self.show_parameters and hasattr(block, 'parameters') and block.parameters:
                # Show first parameter
                param = block.parameters[0]
                param_text = f"{param.name}={param.value}"
                ax.text(x, y - 0.15, param_text, ha='center', va='center',
                       fontsize=8, style='italic')

    def _draw_connector(self, ax, x: float, y: float, name: str,
                       conn_type: str, data_type: str = ''):
        """Draw an input or output connector."""
        color = self.input_color if conn_type == 'input' else self.output_color
        size = 0.4

        # Draw box
        box = FancyBboxPatch((x - size/2, y - size/2), size, size,
                            boxstyle="round,pad=0.05",
                            facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(box)

        # Label
        label = name
        if self.show_types and data_type:
            label += f"\n:{data_type}"

        ha = 'right' if conn_type == 'input' else 'left'
        x_offset = -0.3 if conn_type == 'input' else 0.3
        ax.text(x + x_offset, y, label, ha=ha, va='center', fontsize=9)

    def _draw_connections(self, ax, block: CompositeBlock,
                         input_pos: dict, output_pos: dict, child_pos: dict):
        """Draw connection arrows between blocks."""
        for conn in block.connections:
            # Determine source position
            if not conn.from_output:  # Parent input
                from_pos = input_pos.get(conn.from_block)
                from_x = from_pos[0] + 0.3 if from_pos else 1
                from_y = from_pos[1] if from_pos else 5
            elif conn.from_block in child_pos:  # Child block
                from_pos = child_pos[conn.from_block]
                from_x = from_pos[0] + 0.8
                from_y = from_pos[1]
            else:
                continue

            # Determine target position
            if not conn.to_input:  # Parent output
                to_pos = output_pos.get(conn.to_block)
                to_x = to_pos[0] - 0.3 if to_pos else 9
                to_y = to_pos[1] if to_pos else 5
            elif conn.to_block in child_pos:  # Child block
                to_pos = child_pos[conn.to_block]
                to_x = to_pos[0] - 0.8
                to_y = to_pos[1]
            else:
                continue

            # Draw arrow
            arrow = FancyArrowPatch((from_x, from_y), (to_x, to_y),
                                   arrowstyle='->', lw=2, color=self.connection_color,
                                   connectionstyle="arc3,rad=0.1")
            ax.add_patch(arrow)

    def save(self, fig: Figure, filename: str):
        """Save figure to file.

        Args:
            fig: matplotlib Figure to save
            filename: Output filename (extension determines format)
        """
        fig.savefig(filename, dpi=self.dpi, bbox_inches='tight')
        plt.close(fig)
