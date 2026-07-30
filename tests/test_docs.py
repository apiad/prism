"""Guards against documentation drifting from the code it documents."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from prism.icons import icon_names
from prism.nodes import Node
from prism.registry import names
from prism.theme import bundled_themes

ROOT = Path(__file__).parent.parent
PACKAGE = ROOT / "prism"
DOCS = ROOT / "docs"
GALLERY = DOCS / "gallery"
EXAMPLES = ROOT / "examples"
README = ROOT / "README.md"
SKILL = ROOT / "SKILL.md"

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


def test_skill_file_covers_every_archetype():
    """The agent-facing skill must document the whole catalog."""
    skill = (ROOT / "SKILL.md").read_text()
    for name in names():
        assert f"type: {name}" in skill, f"SKILL.md does not document {name}"


def test_skill_file_names_only_real_icons():
    skill = (ROOT / "SKILL.md").read_text()
    shortlist = skill.split("## Icons")[1].split("## Rules")[0]
    known = set(icon_names())
    named = set(re.findall(r"`([a-z][a-z0-9-]+)`", shortlist))
    assert named, "shortlist parsed as empty"
    assert named <= known, f"SKILL.md names unknown icons: {sorted(named - known)}"


def test_skill_file_names_only_real_themes():
    skill = SKILL.read_text()
    for theme in bundled_themes():
        assert theme in skill


def _advertised_node_fields(markdown: str) -> set[str]:
    """The keys of the YAML block under the doc's 'shared node' heading."""
    section = markdown.split("## The shared node", 1)[1].split("\n## ", 1)[0]
    block = section.split("```yaml", 1)[1].split("```", 1)[0]
    return set(re.findall(r"^([a-z_]+):", block, flags=re.MULTILINE))


def _rendered_node_fields() -> set[str]:
    """Node fields some builder actually reads, so they reach the SVG."""
    sources = [
        path.read_text()
        for path in PACKAGE.rglob("*.py")
        if path.name != "nodes.py"  # the declaration is not a use
    ]
    return {
        field
        for field in Node.model_fields
        if any(re.search(rf"\.{field}\b", source) for source in sources)
    }


@pytest.mark.parametrize("doc", [SKILL, DOCS / "agents.qmd"])
def test_agent_docs_only_advertise_rendered_node_fields(doc):
    """A documented field that nothing draws is worse than no field at all.

    It validates, it shows up in `prism schema`, an agent emits it — and the
    output is silently identical. `badge` and `note` are declared on Node and
    read by no builder, so they must stay out of the consumer vocabulary until
    one of them draws it.
    """
    advertised = _advertised_node_fields(doc.read_text())
    assert advertised, f"{doc.name}: shared-node block parsed as empty"

    unknown = advertised - set(Node.model_fields)
    assert not unknown, f"{doc.name} documents non-existent Node fields: {unknown}"

    dead = advertised - _rendered_node_fields()
    assert not dead, (
        f"{doc.name} advertises Node fields no builder reads: {sorted(dead)} — "
        "either render them or drop them from the vocabulary"
    )


def test_readme_prose_links_to_the_published_docs():
    """GitHub renders a .qmd as raw source, so prose must not link to one."""
    readme = README.read_text()
    qmd_links = re.findall(r"\]\((?:\./)?docs/[^)]+\.qmd\)", readme)
    assert not qmd_links, (
        f"README links to unrendered Quarto sources: {qmd_links} — "
        "link to https://apiad.github.io/prism/<page>.html instead"
    )
