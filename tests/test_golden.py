import random
import re
from pathlib import Path

import prism
from prism.nodebox import RenderContext, build_node_box
from prism.nodes import Node
from prism.text import TextBlock
from prism.theme import load_theme
from prism.typography import measure

EXAMPLE = Path(__file__).parent.parent / "examples" / "flow.yaml"
GOLDEN = Path(__file__).parent / "golden" / "flow.svg"

_NUMBER = re.compile(r"-?\d+\.\d+")

REGENERATE = (
    'uv run python -c "import prism, pathlib; '
    "pathlib.Path('tests/golden/flow.svg').write_text("
    "prism.render_str('examples/flow.yaml'))\""
)


def normalize(svg: str) -> str:
    """Round every float to 2 decimals so platform noise cannot fail the test."""
    return _NUMBER.sub(lambda m: f"{float(m.group()):.2f}", svg)


def test_example_matches_golden():
    actual = normalize(prism.render_str(EXAMPLE))
    expected = normalize(GOLDEN.read_text())
    assert actual == expected, (
        f"Rendered output changed. If intentional, regenerate with:\n  {REGENERATE}"
    )


def _text_blocks(shape):
    """Walk a shape tree yielding every TextBlock, wherever it was nested."""
    if isinstance(shape, TextBlock):
        yield shape
        return
    for child in getattr(shape, "shapes", []):
        yield from _text_blocks(child)


def test_every_label_fits_its_box():
    """The regression guard for prism-owned typography."""
    theme = load_theme("default")
    ctx = RenderContext(theme=theme, width=900, rng=random.Random(0))
    labels = [
        "Ingest",
        "WWWWW MMMMM",
        "lllll iiiii",
        "Publish to the warehouse",
        "Supercalifragilisticexpialidocious",
    ]
    for label in labels:
        box = build_node_box(Node(label=label), ctx, max_width=160)
        inner = box.local().width - 2 * theme.geometry.pad
        blocks = list(_text_blocks(box))
        assert blocks, "node box contains no TextBlock"
        longest = max(
            measure(line, theme.size("label"), weight=theme.weight("label"))
            for block in blocks
            for line in block.lines
        )
        assert longest <= inner + 0.01, f"{label!r} overflows its box"
