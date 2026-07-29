import json
from pathlib import Path

import pytest

METRICS_DIR = Path(__file__).parent.parent / "prism" / "vendor" / "metrics"
EXPECTED = [
    "grotesque-400",
    "grotesque-700",
    "serif-400",
    "serif-700",
    "mono-400",
    "mono-700",
]


@pytest.mark.parametrize("stem", EXPECTED)
def test_metrics_file_is_well_formed(stem):
    data = json.loads((METRICS_DIR / f"{stem}.json").read_text())
    family, weight = stem.rsplit("-", 1)
    assert data["family"] == family
    assert data["weight"] == int(weight)
    assert data["units_per_em"] > 0
    assert data["default_advance"] > 0
    # ASCII printable range must be fully covered.
    for codepoint in range(32, 127):
        assert str(codepoint) in data["advances"]


def test_proportional_font_has_varying_advances():
    data = json.loads((METRICS_DIR / "grotesque-400.json").read_text())
    assert data["advances"][str(ord("i"))] < data["advances"][str(ord("W"))]


def test_mono_font_has_uniform_advances():
    data = json.loads((METRICS_DIR / "mono-400.json").read_text())
    assert data["advances"][str(ord("i"))] == data["advances"][str(ord("W"))]
