# prism: declarative YAML → SVG diagrams

**Date:** 2026-07-29
**Status:** Implemented — v0.1.0 (`dcc1576`). Not yet on PyPI.
**Repo:** `apiad/prism` (new, public, MIT) — distribution `prism-svg`, import `prism`
**Depends on:** `tesserax` (`apiad/tesserax`, public, MIT), `pyyaml`, `pydantic>=2`
(pydantic earns its place by giving JSON Schema export for the agent surface for
free). Optional extra `export` pulls `tesserax[export]` for PNG. Dev-only:
`pytest`, `ruff`, `fonttools` (metric extraction, never imported at runtime).

## Goal

A standalone open-source Python library that turns a **declarative YAML spec into
a single, well-designed SVG diagram**. One spec, one diagram. The library ships a
catalog of opinionated diagram archetypes, a token-based theme system, and a
vendored icon set, so that an agent — or a human writing a book — can describe
the *meaning* of a picture and get a good picture back.

Three consumers from day one:

1. **Agents** emitting YAML into a rendering call (ultimately inside AI-n-Box).
2. **Books and Quarto** documents rendering figures from fenced blocks.
3. **Humans** who want a diagram without opening a canvas app.

## Context

### Lineage

The `prism` name and repo previously belonged to a typed-YAML *artifact* engine
(pptx / html / infographic / scheduler renderers). On 2026-07-29 that engine was
vendored into the AI-n-Box monorepo at `ainbox/packages/prism` via `git subtree`,
where it continues to serve `apps/peacock` — its only consumer. Its 61 commits of
history remain reachable there. The old standalone `syalia-srl/prism` and
`syalia-srl/peacock` repos are archived.

The name is therefore free, and is reused deliberately: what remains valuable in
"prism" is the idea of *one declarative spec dispatching to a deterministic
renderer*. Decks and HTML pages turned out to be commodity output — an agent
produces them with plain markup plus scriptorium. **Visual artifacts are the part
that actually needs a library.**

This project keeps the architecture (envelope + protocol registry + pydantic
schema per type) and throws away the renderers.

### The gap this fills

| Existing | What it is | Why it isn't this |
|---|---|---|
| Mermaid, PlantUML, D2, Graphviz | diagram-as-code, node-edge semantics | Graph topology only. No pyramid / funnel / quadrant / timeline / comparison vocabulary. Theming is an afterthought. Output reads as engineering diagram, not explainer visual. |
| [OpenArt](https://github.com/GaelGirodon/openart) | ~4 kB JS "SmartArt as code" | Closest conceptual match; a handful of templates, JS-only, minimal theming. Proof the idea is wanted, not a product. |
| [OpenNapkinAI](https://github.com/genaiwithshubham/opennapkinai) | React + Express + RoughJS | 39 stars, 5 commits, export still on the roadmap. |
| mingrammer `diagrams` | Python, cloud-architecture icons | One vertical, icon-driven, no concept vocabulary. |
| Napkin AI, Venngage, Lucidchart AI | commercial incumbents | Closed SaaS. No library surface, no agent API. |

Napkin AI's product is two separable halves: (a) classifying prose into a
rhetorical shape, and (b) a catalog of well-designed stylable templates that
render that shape. **(a) is commodity — any competent LLM does it. (b) is the
moat.** prism builds (b) and lets the agent do (a).

No serious, template-rich, themeable, agent-first, declarative concept-diagram
library exists in open source. That is the opening.

### Why tesserax makes this tractable

tesserax (v0.12, zero dependencies, pure Python) already provides the hard parts:
SVG emission, an anchor system for connecting shapes, `RowLayout` / `ColumnLayout`
/ `GridLayout` / `HierarchicalLayout` / `ForceLayout`, `Polyline` / `Path` /
`Arrow`, `Canvas.fit()`, and a `sketch` module for hand-drawn texture. Authoring an
archetype becomes *composition*, not pixel arithmetic.

## Non-goals

- **Not a general drawing API.** That is tesserax. prism is the declarative layer.
- **Not multi-diagram documents.** One spec renders one diagram.
- **Not charts.** Quantitative plots are tesserax's `chart` module or matplotlib.
- **Not prose-to-diagram.** prism never calls an LLM. The agent produces the spec;
  prism deterministically produces the picture.
- **Not decks, pages, or infographics.** Those live in `ainbox/packages/prism`.

## Decisions

### D1. Deep templates, not composable ones

One top-level archetype per spec. Complexity lives *inside* an archetype — rich
typed nodes, archetype-specific structural features (swimlanes, phase bands,
eras, axes), and one generic `groups:` construct that boxes and labels a subset
of nodes. **No template-in-template.**

Rationale: recursive schemas are where small models fail; prism's predecessor
demonstrated that 8–12B models emit valid specs first-try against a closed, flat
vocabulary. Nesting also explodes the layout problem — tesserax's layouts compose
mechanically, but *good-looking* nesting needs per-combination tuning that never
converges. Deep templates keep every spec renderable by a single tuned layout
pass.

Accepted cost: some diagrams become two diagrams, or motivate a new archetype.
Adding archetype #11 is cheap and each addition is *designed*, which is the point.

Note: `hierarchy` recursing through `children:` is **data** recursion within one
archetype, not template composition. That is allowed — it is what a tree is.

### D2. Themes are data, never code

A theme is a token set in YAML: palette, typography, geometry, texture.
Archetypes read tokens only, never literal colors or sizes. Users supply their own
theme file by path; any spec may override individual tokens inline.

Rationale: a Python-plugin theme could violate an archetype's layout invariants,
and could not cross the YAML boundary that an agent writes. Data-only themes also
allow mechanical palette validation (contrast, colorblind-safety) at load time.

Consequence: tokens are **semantic** (`ink`, `surface`, `muted`) not literal
(`black`, `white`), so dark mode falls out for free. Enforced from day one —
retrofitting semantic tokens is miserable.

### D3. prism owns typography

`tesserax.Text.local()` estimates width as `len(content) * size * 0.6` and
tesserax has no text wrapping. For a library where every node is a box that must
contain its label, that is fatal: real advance widths range from ~0.22em (`i`,
`l`) to ~0.94em (`W`, `M`), so `"Illicit"` gets a box twice as wide as needed and
`"WWW Gateway"` overflows its border. Across a twelve-node flow the output looks
broken — the exact failure that sends people back to Mermaid.

prism vendors per-character advance-width tables, implements greedy word-wrap,
and exposes a `MeasuredText` subclassing `tesserax.Text` with `local()` overridden
to return true bounds. tesserax's layout engines then compose correctly with **no
change to tesserax** — they simply consume the `Bounds` we hand them. Upstreaming
is possible later; a tesserax release is deliberately not on the critical path.

**Font choice is a correctness constraint, not taste.** Metrics only hold if the
viewer renders the font we measured. v1 vendors metrics for the three families
that have metric-compatible clones on every platform:

| Token | Stack | Metric-compatible everywhere via |
|---|---|---|
| `grotesque` | `Arial, Helvetica, sans-serif` | Helvetica (macOS), Liberation Sans / Arimo (Linux) |
| `serif` | `"Times New Roman", Times, serif` | Times (macOS), Liberation Serif / Tinos (Linux) |
| `mono` | `"Courier New", monospace` | Liberation Mono / Cousine (Linux) |

Custom families are permitted and documented as falling back to estimated metrics
with a widened safety pad. Georgia and Inter are deliberately excluded from v1:
neither has a metric-compatible clone in the standard Linux font set.

**Only weights 400 and 700 are permitted**, for the same reason. Metrics are
extracted from the Liberation faces, which ship Regular and Bold only; a token
asking for 600 would be synthesised by the viewer at an advance width we never
measured. The theme schema rejects any other value.

**Rejected:** converting text to outlines. Perfectly accurate, but kills
selectable, searchable, copyable text — unacceptable when the target is books.

**Deferred:** base64 `@font-face` embedding. It would allow a prettier default
with guaranteed metrics, but costs ~100 kB per file and Quarto's Typst path likely
will not honor it. Revisit after seeing real book output.

### D4. Icons from day one, vendored, never a dependency

[Lucide](https://github.com/lucide-icons/lucide) (ISC, 1600+ icons). Its geometry
is exactly right: uniform `viewBox="0 0 24 24"`, `fill="none"`,
`stroke="currentColor"`, `stroke-width="2"`, round caps and joins. Every icon is
pure outline stroke, so **icons inherit theme tokens for free** (ink color, stroke
width) and route through the `sketch` texture like any other geometry. Phosphor
and Material mix fill and stroke and would fight the token system.

A build script normalizes every icon to a single `d` string — converting `rect`,
`circle`, `line`, `polyline` and `polygon` children to path commands — into one
`icons.json`.

**Correction found during planning:** `tesserax.Path` has no raw `d` attribute. It
builds an internal command list through `jump_to` / `line_to` / `cubic_to` / `arc`
and derives bounds from the points it has seen, so prism cannot hand it a path
string. v1 therefore renders icons through a small `IconShape(Visual)` that emits
the `<path>` directly and reports exact bounds — which it can, because the source
viewBox is known to be 24×24. The consequence is that **`texture: sketch` does not
apply to icons in v1**, since tesserax's sketch pass works through `trace()`.
Revisit in VS2: either write a `d`-parser feeding a real `tesserax.Path`, or accept
clean icons inside sketch diagrams as a deliberate look.

An agent cannot reliably choose from 1600 names, so the shipped skill exposes a
**curated ~150-name concept vocabulary** (`users`, `database`, `shield`,
`git-branch`, `trending-up`, …) while the full set stays available to humans.
Unknown names fail at load with a did-you-mean.

The ISC notice is retained in `vendor/lucide/LICENSE`.

### D5. Rendering is deterministic

Byte-identical output for identical input. tesserax's `sketch` module is random by
nature; unseeded, re-rendering a book figure produces a different SVG every build,
churning git diffs and breaking snapshot tests. The RNG is seeded from a BLAKE2b
hash of the canonicalized spec, so `texture: sketch` is reproducible.

### D6. Accessibility is taken because it is free

`role="img"` plus `<title>` and `<desc>` generated from `title` / `caption`. Zero
cost, and it matters the moment these land in web output.

## Spec format

### Envelope

Inherited from the predecessor, with one change of meaning: `type` selects the
**archetype**, because the renderer is always SVG.

```yaml
type: flow                      # archetype discriminator (required)
theme: default                  # named theme, or path to a theme YAML
title: "Ingestion pipeline"     # optional
subtitle: "as of Q3"            # optional
caption: "Source: internal"     # optional
width: 900                      # layout hint in px; height derives from content
tokens:                         # optional per-spec token overrides,
  palette.ink: "#0b1020"        # addressed by dotted path into the theme
  geometry.radius: 2
```

### Node — shared by every archetype

```yaml
id: ingest                  # optional; required only if referenced
label: "Ingest"             # required
sublabel: "S3 + Kafka"      # optional
icon: database              # optional; Lucide name
badge: "1"                  # optional; short marker, <= 4 chars
accent: 2                   # optional; ramp index 0-5, or a token name
emphasis: normal            # strong | normal | muted
note: "runs nightly"        # optional; rendered as marginal annotation
```

### Groups — the single escape hatch

```yaml
groups:
  - label: "Backend"
    members: [ingest, transform]
    accent: 3
```

### Links — extra relations beyond an archetype's spine

```yaml
links:
  - from: verify
    to: ingest
    label: "on failure"
    style: dashed          # solid | dashed | dotted
    kind: back             # forward | back | bidirectional
```

## The v1 catalog

Ten archetypes. Every one accepts the shared Node, `groups:`, and the envelope.

### `flow` — steps, branches, decisions

```yaml
type: flow
direction: right                 # right | down
steps:
  - id: ingest
    label: "Ingest"
    branches:                    # optional fan-out of alternatives
      - label: "Reject"
lanes:                           # optional swimlanes
  - label: "Platform"
    members: [ingest]
phases:                          # optional bands spanning a step range
  - label: "Batch"
    span: [ingest, verify]
links: [...]
```

### `hierarchy` — tree, org chart, decomposition

```yaml
type: hierarchy
direction: down                  # down | right
root:
  label: "System"
  children:
    - label: "API"
      children:
        - label: "Auth"
```

Built on tesserax's `HierarchicalLayout`.

### `cycle` — closed loop, iterative process

```yaml
type: cycle
direction: clockwise             # clockwise | counterclockwise
center:                          # optional hub label
  label: "Kaizen"
steps: [Node, ...]
```

### `timeline` — chronology, milestones, eras

```yaml
type: timeline
orientation: horizontal          # horizontal | vertical
events:
  - id: launch
    when: "2024 Q1"              # free text; never parsed as a date
    label: "Launch"
eras:                            # optional bands
  - label: "Beta"
    span: [launch, ga]
    accent: 1
```

### `comparison` — side-by-side, before/after, pros/cons

```yaml
type: comparison
criteria: ["Cost", "Latency"]    # optional; when present, aligns rows
columns:
  - header: {label: "Managed", icon: cloud}
    items: [{label: "High"}, {label: "Low"}]
```

Validation: when `criteria` is present, every column's `items` must align 1:1.

### `quadrant` — 2×2 with named axes

```yaml
type: quadrant
axes:
  x: {label: "Effort", low: "Low", high: "High"}
  y: {label: "Impact", low: "Low", high: "High"}
quadrant_labels: ["Fill-ins", "Quick wins", "Thankless", "Big bets"]
items:
  - label: "Search rewrite"
    x: 0.8                       # 0..1
    y: 0.7
```

### `pyramid` — layered magnitude, invertible into a funnel

```yaml
type: pyramid
invert: false                    # true renders a funnel
levels:
  - label: "Self-actualization"
    value: 120                   # optional; when present on all levels,
                                 # widths scale proportionally
```

Without `value`, levels taper evenly.

### `stack` — tiers, layered architecture

```yaml
type: stack
order: top_down                  # top_down | bottom_up
layers:
  - label: "Application"
    side: "L7"                   # optional side annotation
```

### `hub` — hub-and-spoke, radial relations

```yaml
type: hub
center: {label: "Platform", icon: box}
spokes: [Node, ...]
ring: false                      # draw a connecting ring between spokes
links: [...]                     # optional spoke-to-spoke
```

### `matrix` — row × column headers with cell content

```yaml
type: matrix
rows: [{id: r1, label: "Q1"}]
columns: [{id: c1, label: "EMEA"}]
cells:
  - row: r1
    column: c1
    label: "€1.2M"
    accent: 0
```

Cells are sparse; missing combinations render empty.

## Theme tokens

```yaml
name: default
palette:
  surface: "#ffffff"
  ink: "#111827"
  muted: "#6b7280"
  line: "#d1d5db"
  ramp: ["#0f766e", "#b45309", "#4338ca", "#be123c", "#0369a1", "#65a30d"]
  ok: "#15803d"
  warn: "#b45309"
  bad: "#b91c1c"
typography:
  family: grotesque              # grotesque | serif | mono | <custom stack>
  scale: {title: 20, label: 13, sublabel: 11, note: 10, badge: 10}
  weight: {label: 700, sublabel: 400}   # 400 and 700 only — see below
  line_height: 1.35
geometry:
  radius: 6
  stroke: 1.5
  gap: 24
  pad: 12
  arrow: standard                # standard | thin | block
texture: clean                   # clean | sketch
```

v1 ships `default`, `dark`, `paper` (warm, serif, sketch texture), and `mono`.
Palette validation at load time checks ink/surface contrast and ramp
distinguishability.

## Architecture

Four layers, each independently testable:

```
prism/
├── envelope.py        # load YAML, read `type`, dispatch
├── registry.py        # Archetype protocol + self-registration
├── typography.py      # metrics, word-wrap, MeasuredText
├── theme.py           # token loading, validation, ramp resolution
├── icons.py           # Lucide lookup -> tesserax Path
├── errors.py          # agent-legible exceptions with did-you-mean
├── cli.py
├── archetypes/
│   ├── flow/          # schema.py + build.py, self-registering
│   └── ...            # nine more
├── themes/            # default.yaml, dark.yaml, paper.yaml, mono.yaml
└── vendor/lucide/     # icons.json + LICENSE
```

The `Archetype` protocol:

```python
class Archetype(Protocol):
    name: str
    spec_model: type[BaseModel]

    def build(self, spec: BaseModel, theme: Theme) -> tesserax.Canvas: ...
```

Adding an archetype touches no shared file — it registers itself, exactly as the
predecessor's renderers did.

Pipeline: YAML → envelope → pydantic validation against the archetype's model →
`build()` composes tesserax shapes → `Canvas.fit()` → SVG string.

## Agent surface

The part that makes this *for agents*, ported from what already worked:

- **`SKILL.md`** teaching the closed vocabulary — validated against
  `qwen/qwen3-32b`, the canonical local model, rather than a frontier model that
  would flatter the schema.
- **`prism schema <archetype>`** emits JSON Schema for tool-calling and structured
  output.
- **Errors written for a model, not a human.** Unknown archetype, unknown icon,
  unknown token, dangling group member, misaligned comparison rows — each names
  the offending value, lists valid neighbours, and suggests the closest match via
  `difflib`. An agent's recovery loop is only as good as the error string.

## Consumption surfaces

- **Python:** `prism.render(spec, out_path)` and `prism.render_str(spec)`.
- **CLI:** `prism render | themes | icons | archetypes | schema`.
- **Notebooks:** `_repr_svg_` on the result object, for Jupyter and Quarto.
- **Quarto:** an extension rendering ` ```{prism} ` fenced blocks to figures.
- **PNG:** via tesserax's `[export]` extra, as an optional prism extra.

## Testing

- **Golden SVG snapshots** with coordinates rounded to 2 decimals through a
  normalizer, killing float noise across platforms.
- **Matrix property test:** every archetype renders every theme × both textures
  without raising.
- **Text-fit assertion:** no measured label exceeds its container's inner width.
  This is the regression guard for D3 and the single most valuable test here.
- **Determinism test:** rendering the same spec twice is byte-identical, including
  `texture: sketch`.
- **Gallery script** rendering the full catalog to one page — doubles as README
  proof and docs-site content.

## Docs

A minimal Quarto site mirroring tesserax's (`docs/*.qmd`): index, catalog gallery,
theming, agent guide. Minimal in v1, but present — it is most of what makes a
public library adoptable.

## Build order

Vertical slices, thinnest end-to-end path first.

- **VS1 — `flow` end-to-end.** Envelope, registry, one theme, typography for one
  family, a small icon subset, the `flow` archetype, CLI `render`, SVG out, golden
  test, README example. Proves the entire stack on one archetype.
- **VS2 — the systems.** Full theme system (all tokens, four themes, dark, sketch
  texture), full Lucide vendoring plus the curated list, determinism seeding,
  accessibility.
- **VS3 — the catalog.** The remaining nine archetypes. Mostly schema plus builder
  once VS1 and VS2 exist.
- **VS4 — the agent surface.** `SKILL.md`, JSON Schema export, error quality, and
  the `qwen/qwen3-32b` validation harness.
- **VS5 — distribution.** Quarto extension, notebook repr, PNG extra, docs site
  and gallery, PyPI release as `prism-svg`.

## Deferred to v2

Archetypes: `network` (free-form graph via `ForceLayout` — the escape hatch back
to node-edge, and the one place Mermaid and Graphviz already win), `venn`,
`journey`, `roadmap`, `sequence`.

Also: font embedding; icon sets beyond Lucide; an MCP server; animation (tesserax
can animate — a future `animate: true` for `cycle` and `flow`); and any form of
template nesting.

## References

- tesserax — `repos/tesserax`, https://github.com/apiad/tesserax
- Lucide icons (ISC) — https://github.com/lucide-icons/lucide
- OpenArt — https://github.com/GaelGirodon/openart
- OpenNapkinAI — https://github.com/genaiwithshubham/opennapkinai
- Predecessor architecture — `ainbox/packages/prism` (`envelope.py`, `registry.py`)
