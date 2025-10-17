"""Main visualization interface for CDL blocks."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from python_cdl.models.blocks import Block, CompositeBlock, ElementaryBlock


class VisualizationStyle(str, Enum):
    """Visualization style options."""

    DETAILED = "detailed"  # Show all connectors, parameters, equations
    SIMPLE = "simple"      # Show only block names and connections
    COMPACT = "compact"    # Minimal view with just block types


@dataclass
class BlockVisualizer:
    """Main interface for visualizing CDL blocks.

    Provides a unified API for creating visual representations of CDL blocks
    using different rendering backends (Graphviz, Matplotlib).

    Examples:
        >>> visualizer = BlockVisualizer()
        >>> visualizer.render(composite_block, style="detailed")
        >>> visualizer.save("block_diagram.png")

        >>> # With matplotlib backend
        >>> visualizer = BlockVisualizer(backend="matplotlib")
        >>> fig = visualizer.render_to_figure(block)
        >>> fig.show()
    """

    backend: Literal["graphviz", "matplotlib"] = "matplotlib"
    style: VisualizationStyle = VisualizationStyle.DETAILED
    show_parameters: bool = True
    show_equations: bool = True
    show_types: bool = True

    def render(self, block: Block, output_file: str | None = None, **kwargs):
        """Render a block to a visualization.

        Args:
            block: Block to visualize
            output_file: Optional file to save to (extension determines format)
            **kwargs: Additional rendering options

        Returns:
            Renderer-specific output (Figure for matplotlib, Digraph for graphviz)
        """
        if self.backend == "graphviz":
            from .graphviz_renderer import GraphvizRenderer
            renderer = GraphvizRenderer(
                style=self.style,
                show_parameters=self.show_parameters,
                show_equations=self.show_equations,
                show_types=self.show_types
            )
        else:
            from .matplotlib_renderer import MatplotlibRenderer
            renderer = MatplotlibRenderer(
                style=self.style,
                show_parameters=self.show_parameters,
                show_equations=self.show_equations,
                show_types=self.show_types
            )

        result = renderer.render(block, **kwargs)

        if output_file:
            renderer.save(result, output_file)

        return result

    def render_to_figure(self, block: Block, **kwargs):
        """Render to matplotlib figure (convenience method).

        Args:
            block: Block to visualize
            **kwargs: Additional rendering options

        Returns:
            matplotlib Figure object
        """
        if self.backend != "matplotlib":
            raise ValueError("render_to_figure only works with matplotlib backend")

        return self.render(block, **kwargs)

    def render_to_svg(self, block: Block, **kwargs) -> str:
        """Render to SVG string.

        Args:
            block: Block to visualize
            **kwargs: Additional rendering options

        Returns:
            SVG as string
        """
        if self.backend == "graphviz":
            from .graphviz_renderer import GraphvizRenderer
            renderer = GraphvizRenderer(
                style=self.style,
                show_parameters=self.show_parameters,
                show_equations=self.show_equations,
                show_types=self.show_types
            )
            graph = renderer.render(block, **kwargs)
            return graph.pipe(format='svg').decode('utf-8')
        else:
            raise NotImplementedError("SVG export only supported with graphviz backend")
