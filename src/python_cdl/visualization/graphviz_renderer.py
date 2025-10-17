"""Graphviz-based renderer for CDL blocks."""

from dataclasses import dataclass
from typing import Any

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

from python_cdl.models.blocks import Block, CompositeBlock, ElementaryBlock
from .block_visualizer import VisualizationStyle


@dataclass
class GraphvizRenderer:
    """Render CDL blocks using Graphviz.

    Creates hierarchical block diagrams with automatic layout.
    Requires graphviz to be installed.
    """

    style: VisualizationStyle = VisualizationStyle.DETAILED
    show_parameters: bool = True
    show_equations: bool = True
    show_types: bool = True
    rankdir: str = "LR"  # Left to right layout

    def __post_init__(self):
        if not GRAPHVIZ_AVAILABLE:
            raise ImportError(
                "graphviz is required for GraphvizRenderer. "
                "Install with: pip install graphviz"
            )

    def render(self, block: Block, **kwargs) -> 'graphviz.Digraph':
        """Render a block to a Graphviz directed graph.

        Args:
            block: Block to visualize
            **kwargs: Additional graphviz options

        Returns:
            graphviz.Digraph object
        """
        graph = graphviz.Digraph(
            name=block.name,
            graph_attr={'rankdir': self.rankdir, 'splines': 'ortho'},
            node_attr={'shape': 'box', 'style': 'rounded,filled'},
            **kwargs
        )

        if isinstance(block, CompositeBlock):
            self._render_composite(graph, block)
        elif isinstance(block, ElementaryBlock) or block.block_type == 'elementary':
            self._render_elementary(graph, block)
        else:
            self._render_elementary(graph, block)

        return graph

    def _render_composite(self, graph: 'graphviz.Digraph', block: CompositeBlock):
        """Render a composite block."""
        # Add inputs
        for inp in block.inputs:
            label = self._format_connector_label(inp, 'input')
            graph.node(f"input_{inp.name}", label=label,
                      fillcolor='lightblue', shape='ellipse')

        # Add child blocks
        for child in block.blocks:
            label = self._format_block_label(child)
            color = 'lightcoral' if isinstance(child, CompositeBlock) else 'lightgreen'
            graph.node(child.name, label=label, fillcolor=color)

        # Add outputs
        for out in block.outputs:
            label = self._format_connector_label(out, 'output')
            graph.node(f"output_{out.name}", label=label,
                      fillcolor='lightyellow', shape='ellipse')

        # Add connections
        for conn in block.connections:
            from_node = f"input_{conn.from_block}" if not conn.from_output else conn.from_block
            to_node = f"output_{conn.to_block}" if not conn.to_input else conn.to_block

            label = ""
            if conn.from_output:
                label += conn.from_output
            if conn.to_input:
                label += f" → {conn.to_input}" if label else conn.to_input

            graph.edge(from_node, to_node, label=label)

    def _render_elementary(self, graph: 'graphviz.Digraph', block: Block):
        """Render an elementary block."""
        # Add inputs
        for inp in block.inputs:
            label = self._format_connector_label(inp, 'input')
            graph.node(f"input_{inp.name}", label=label,
                      fillcolor='lightblue', shape='ellipse')
            graph.edge(f"input_{inp.name}", block.name, label=inp.name)

        # Add central block
        label = self._format_block_label(block)
        graph.node(block.name, label=label, fillcolor='lightgreen')

        # Add outputs
        for out in block.outputs:
            label = self._format_connector_label(out, 'output')
            graph.node(f"output_{out.name}", label=label,
                      fillcolor='lightyellow', shape='ellipse')
            graph.edge(block.name, f"output_{out.name}", label=out.name)

    def _format_block_label(self, block: Block) -> str:
        """Format label for a block node."""
        parts = [f"<b>{block.name}</b>"]

        if self.show_types:
            parts.append(f"<i>{block.block_type}</i>")

        if self.style == VisualizationStyle.DETAILED:
            if self.show_equations and hasattr(block, 'equations') and block.equations:
                eq_lines = [f"{eq.lhs} = {eq.rhs}" for eq in block.equations[:3]]
                if len(block.equations) > 3:
                    eq_lines.append("...")
                parts.append("<br/>".join(eq_lines))
            elif self.show_parameters and hasattr(block, 'parameters') and block.parameters:
                param_lines = [f"{p.name} = {p.value}" for p in block.parameters[:3]]
                if len(block.parameters) > 3:
                    param_lines.append("...")
                parts.append("<br/>".join(param_lines))

        return f"< {'<br/>'.join(parts)} >"

    def _format_connector_label(self, connector, conn_type: str) -> str:
        """Format label for a connector node."""
        label = connector.name

        if self.show_types and hasattr(connector, 'type'):
            label += f"\n:{connector.type}"

        if self.style == VisualizationStyle.DETAILED:
            if hasattr(connector, 'unit') and connector.unit:
                label += f"\n[{connector.unit}]"

        return label

    def save(self, graph: 'graphviz.Digraph', filename: str):
        """Save graph to file.

        Args:
            graph: Graphviz Digraph to save
            filename: Output filename (without extension)
        """
        # Determine format from filename
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            graph.render(name, format=ext, cleanup=True)
        else:
            graph.render(filename, cleanup=True)
