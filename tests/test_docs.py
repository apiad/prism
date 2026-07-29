"""Guards against documentation drifting from the code it documents."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from prism.icons import icon_names
from prism.registry import names
from prism.theme import bundled_themes

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
GALLERY = DOCS / "gallery"
EXAMPLES = ROOT / "examples"
README = ROOT / "README.md"

REGENERATE = "uv run python scripts/build_gallery.py"


def test_every_archetype_has_an_example():
    assert sorted(p.stem for p in EXAMPLES.glob("*.yaml")) == names()


@pytest.mark.parametrize("archetype", names())
@pytest.mark.parametrize("theme", bundled_themes())
def test_gallery_is_complete(archetype, theme):
    target = GALLERY / f"{archetype}-{theme}.svg"
    assert target.exists(), f"missing {target.name}; regenerate with: {REGENERATE}"


def test_catalog_documents_every_archetype():
    catalog = (DOCS / "catalog.qmd").read_text()
    for name in names():
        assert f"## `{name}`" in catalog, f"catalog missing {name}; run {REGENERATE}"


def test_themes_page_shows_every_theme():
    page = (DOCS / "themes.qmd").read_text()
    for theme in bundled_themes():
        assert f"<code>{theme}</code>" in page, f"themes page missing {theme}"


def _local_images(markdown: str) -> list[str]:
    inline = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)
    html = re.findall(r'<img[^>]+src="([^"]+)"', markdown)
    return [src for src in inline + html if not src.startswith("http")]


def test_readme_images_all_exist():
    for src in _local_images(README.read_text()):
        assert (ROOT / src).exists(), f"README references missing image {src}"


def test_doc_page_images_all_exist():
    for page in DOCS.glob("*.qmd"):
        for src in _local_images(page.read_text()):
            assert (DOCS / src).exists(), f"{page.name} references missing {src}"


def test_agent_shortlist_icons_all_exist():
    """The curated vocabulary must not name an icon we do not ship."""
    page = (DOCS / "agents.qmd").read_text()
    shortlist = page.split("An unknown icon name fails")[0].split("prism icons`")[1]
    known = set(icon_names())
    named = set(re.findall(r"`([a-z][a-z0-9-]+)`", shortlist))
    assert named, "shortlist parsed as empty"
    assert named <= known, f"agents.qmd names unknown icons: {sorted(named - known)}"
