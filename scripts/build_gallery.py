"""Render every bundled example and generate the pages that show them.

    uv run python scripts/build_gallery.py

Writes docs/gallery/*.svg plus the generated docs/catalog.qmd and
docs/themes.qmd. Generating those pages keeps the documentation honest: it can
only ever show examples that actually render.
"""

from __future__ import annotations

from pathlib import Path

import prism
from prism.registry import get
from prism.theme import bundled_themes

ROOT = Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"
DOCS = ROOT / "docs"
GALLERY = DOCS / "gallery"

DEFAULT_THEME = "default"

BLURBS = {
    "flow": "Steps, in order. The workhorse: pipelines, processes, decisions.",
    "hierarchy": "A tree — org charts, decomposition, taxonomies. The one "
    "archetype whose data is recursive.",
    "cycle": "A closed loop. Iterative processes that return to their start.",
    "timeline": "Chronology, with optional era bands spanning a range of events.",
    "comparison": "Side-by-side columns. Add `criteria` to align the rows.",
    "quadrant": "A 2x2 field with named axes and items placed by coordinate.",
    "pyramid": "Layered magnitude. Give the levels `value` and it reads as a funnel.",
    "stack": "Tiers, drawn as full-width bars, with optional side annotations.",
    "hub": "A centre and its spokes.",
    "matrix": "Row and column headers with sparse cells.",
}

CATALOG_HEADER = """---
title: "Catalog"
subtitle: "Every archetype prism ships, with the spec that produced it"
---

prism ships {count} archetypes. Each one is opinionated: you describe the
*meaning* of the picture and prism decides the geometry, spacing and colour.

Every diagram below is generated from the YAML shown beside it, by the same
code path the library exposes. If an example stopped rendering, this page
could not be built.

"""

THEMES_HEADER = """---
title: "Themes"
subtitle: "One spec, four looks"
---

A theme is **data, not code** — a token set in YAML covering palette,
typography and geometry. Archetypes read tokens only; a literal colour
anywhere in an archetype is a bug.

Because the tokens are semantic (`ink`, `surface`, `muted`) rather than
literal (`black`, `white`), dark mode falls out for free.

```bash
prism themes           # list what ships
prism render d.yaml    # honours the spec's `theme:` field
```

Any spec can also override individual tokens inline by dotted path:

```yaml
type: flow
theme: dark
tokens:
  palette.ink: "#f8fafc"
  geometry.radius: 2
steps:
  - {label: Draft}
  - {label: Ship}
```

Or point `theme:` at your own YAML file, which is how you brand a whole
document set.

"""


def write_gallery(themes: list[str]) -> int:
    GALLERY.mkdir(parents=True, exist_ok=True)
    written = 0
    for example in sorted(EXAMPLES.glob("*.yaml")):
        spec = example.read_text()
        for theme in themes:
            themed = spec.replace("type:", f"theme: {theme}\ntype:", 1)
            (GALLERY / f"{example.stem}-{theme}.svg").write_text(
                prism.render_str(themed), encoding="utf-8"
            )
            written += 1
    return written


def write_catalog(names: list[str]) -> None:
    parts = [CATALOG_HEADER.format(count=len(names))]
    for name in names:
        spec = (EXAMPLES / f"{name}.yaml").read_text().strip()
        blurb = BLURBS.get(name, "")
        parts.append(
            f"## `{name}`\n\n{blurb}\n\n"
            f"![](gallery/{name}-{DEFAULT_THEME}.svg)\n\n"
            f"```yaml\n{spec}\n```\n\n"
            f"See the full field list with `prism schema {name}`.\n"
        )
    (DOCS / "catalog.qmd").write_text("\n".join(parts), encoding="utf-8")


def write_themes(themes: list[str], showcase: str = "flow") -> None:
    parts = [THEMES_HEADER]
    parts.append("## The bundled themes\n")
    parts.append("::: {.theme-grid}\n")
    for theme in themes:
        parts.append(
            f"<figure>\n"
            f'<img src="gallery/{showcase}-{theme}.svg" alt="{theme} theme">\n'
            f"<figcaption><code>{theme}</code></figcaption>\n"
            f"</figure>\n"
        )
    parts.append(":::\n")

    parts.append(
        "\n## The same catalog, themed\n\n"
        "Every archetype renders in every theme. A few, side by side:\n"
    )
    for name in ["hierarchy", "pyramid", "quadrant"]:
        parts.append(f"\n### `{name}`\n")
        parts.append("\n::: {.theme-grid}\n")
        for theme in themes:
            parts.append(
                f"<figure>\n"
                f'<img src="gallery/{name}-{theme}.svg" alt="{name}, {theme}">\n'
                f"<figcaption><code>{theme}</code></figcaption>\n"
                f"</figure>\n"
            )
        parts.append(":::\n")

    parts.append(
        "\n## Writing your own\n\n"
        "Copy a bundled theme and edit the tokens. Two constraints are"
        " enforced at load time:\n\n"
        "- `typography.family` must be `grotesque`, `serif` or `mono` — the"
        " three stacks whose font metrics prism vendors.\n"
        "- `typography.weight.*` must be `400` or `700`, for the same reason."
        " A weight prism has not measured would be synthesised by the viewer"
        " at a width prism never accounted for, and labels would overflow"
        " their boxes.\n"
    )
    (DOCS / "themes.qmd").write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    themes = bundled_themes()
    names = sorted(path.stem for path in EXAMPLES.glob("*.yaml"))
    missing = [name for name in names if get(name) is None]
    if missing:
        raise SystemExit(f"examples without an archetype: {missing}")

    count = write_gallery(themes)
    write_catalog(names)
    write_themes(themes)
    print(f"wrote {count} SVGs, catalog.qmd and themes.qmd")


if __name__ == "__main__":
    main()
