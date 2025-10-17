"""Tests for visualization module."""

import pytest
from python_cdl.models.blocks import Block, CompositeBlock
from python_cdl.models.connectors import RealInput, RealOutput
from python_cdl.models.parameters import Parameter
from python_cdl.models.equations import Equation
from python_cdl.models.connections import Connection
from python_cdl.visualization import BlockVisualizer, VisualizationStyle


@pytest.fixture
def simple_elementary_block():
    """Create a simple elementary block for testing."""
    return Block(
        name="TestController",
        block_type="elementary",
        parameters=[Parameter(name="k", type="Real", value=2.0)],
        inputs=[
            RealInput(name="u_s", description="Setpoint"),
            RealInput(name="u_m", description="Measurement"),
        ],
        outputs=[RealOutput(name="y", description="Output")],
        equations=[
            Equation(lhs="e", rhs="u_s - u_m"),
            Equation(lhs="y", rhs="k * e"),
        ]
    )


@pytest.fixture
def simple_composite_block(simple_elementary_block):
    """Create a simple composite block for testing."""
    gain = Block(
        name="gain",
        block_type="elementary",
        parameters=[Parameter(name="k", type="Real", value=5.0)],
        inputs=[RealInput(name="u")],
        outputs=[RealOutput(name="y")],
        equations=[Equation(lhs="y", rhs="k * u")]
    )

    limiter = Block(
        name="limiter",
        block_type="elementary",
        inputs=[
            RealInput(name="u1"),
            RealInput(name="u2"),
        ],
        outputs=[RealOutput(name="y")],
        equations=[Equation(lhs="y", rhs="min(u1, u2)")]
    )

    return CompositeBlock(
        name="TestComposite",
        block_type="composite",
        inputs=[
            RealInput(name="input"),
            RealInput(name="limit"),
        ],
        outputs=[RealOutput(name="output")],
        blocks=[gain, limiter],
        connections=[
            Connection(from_block="input", from_output="", to_block="gain", to_input="u"),
            Connection(from_block="limit", from_output="", to_block="limiter", to_input="u1"),
            Connection(from_block="gain", from_output="y", to_block="limiter", to_input="u2"),
            Connection(from_block="limiter", from_output="y", to_block="output", to_input=""),
        ]
    )


class TestBlockVisualizer:
    """Test BlockVisualizer class."""

    def test_create_visualizer_default(self):
        """Test creating visualizer with defaults."""
        viz = BlockVisualizer()
        assert viz.backend == "matplotlib"
        assert viz.style == VisualizationStyle.DETAILED
        assert viz.show_parameters is True

    def test_create_visualizer_custom(self):
        """Test creating visualizer with custom settings."""
        viz = BlockVisualizer(
            backend="matplotlib",
            style=VisualizationStyle.SIMPLE,
            show_parameters=False
        )
        assert viz.backend == "matplotlib"
        assert viz.style == VisualizationStyle.SIMPLE
        assert viz.show_parameters is False

    def test_render_elementary_block(self, simple_elementary_block):
        """Test rendering an elementary block."""
        viz = BlockVisualizer(backend="matplotlib")
        fig = viz.render(simple_elementary_block)

        assert fig is not None
        assert hasattr(fig, 'savefig')  # matplotlib Figure

    def test_render_composite_block(self, simple_composite_block):
        """Test rendering a composite block."""
        viz = BlockVisualizer(backend="matplotlib")
        fig = viz.render(simple_composite_block)

        assert fig is not None
        assert hasattr(fig, 'savefig')

    def test_render_different_styles(self, simple_elementary_block):
        """Test rendering with different styles."""
        for style in VisualizationStyle:
            viz = BlockVisualizer(backend="matplotlib", style=style)
            fig = viz.render(simple_elementary_block)
            assert fig is not None

    def test_render_to_figure(self, simple_elementary_block):
        """Test render_to_figure convenience method."""
        viz = BlockVisualizer(backend="matplotlib")
        fig = viz.render_to_figure(simple_elementary_block)

        assert fig is not None
        assert hasattr(fig, 'savefig')

    def test_render_to_figure_wrong_backend(self, simple_elementary_block):
        """Test render_to_figure fails with graphviz backend."""
        viz = BlockVisualizer(backend="graphviz")
        with pytest.raises(ValueError, match="only works with matplotlib"):
            viz.render_to_figure(simple_elementary_block)


class TestGraphvizRenderer:
    """Test Graphviz renderer (if available)."""

    def test_render_with_graphviz(self, simple_elementary_block):
        """Test rendering with graphviz backend."""
        try:
            import graphviz
        except ImportError:
            pytest.skip("graphviz not installed")

        viz = BlockVisualizer(backend="graphviz")
        result = viz.render(simple_elementary_block)

        # Check it's a graphviz object
        assert hasattr(result, 'pipe')  # Graphviz Digraph
        assert hasattr(result, 'render')
