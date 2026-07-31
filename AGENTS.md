# AGENTS.md

Orientation for agents (and humans) working *in* this repo. Read this first,
then load the `know-how/` doc that matches your task.

If you are an agent *using* prism to draw a picture rather than working on it,
you want `SKILL.md` (or `docs/agents.qmd`) instead — that is the consumer-facing
vocabulary, and nothing here applies to it.

## What prism is

A library that turns one declarative YAML spec into one well-designed SVG
diagram. You describe what a picture *means* — steps in a pipeline, levels of a
pyramid, items in a quadrant — and prism decides geometry, spacing, typography
and colour.

The bet is that most explanatory pictures are **not graphs**. Mermaid, D2 and
Graphviz model topology and do it well; they have no vocabulary for a funnel or
a 2×2. prism ships ten opinionated archetypes instead of a graph engine.

`README.md` is the user view; `docs/specs/2026-07-29-declarative-diagrams-design.md`
is the full design and the *why* behind most constraints below.

**Not to be confused with** the older typed-YAML *artifact* engine that used to
own this name (pptx / html / infographic renderers). That code now lives at
`ainbox/packages/prism` and serves `apps/peacock`; `syalia-srl/prism` is
archived. Nothing is shared between the two but the word.

## The pipeline (the mental model)

```
YAML → load_spec → Envelope ─┬→ registry.get(type) → archetype.build(spec, ctx) → Group
                             └→ load_theme(theme, tokens) → Theme ──┘
                                                                     ↓
                                        frame(body, envelope, ctx) → Canvas → SVG
                                                                     ↓
                                                        with_accessibility(svg)
```

- **`envelope.py`** — the shell every spec shares: `type`, `theme`, `title`,
  `subtitle`, `caption`, `width`, `tokens`. Extras are *ignored* here because
  the archetype's payload keys sit alongside them in the same mapping.
- **`registry.py`** — `name → Archetype` (a `Protocol`: `name`, `spec_model`,
  `build`). Importing `prism.archetypes` registers the whole catalog as a side
  effect, which is why `__init__.py` imports it with a `noqa: F401`.
- **`theme.py`** — themes are **data**, a validated token set loaded from YAML.
  Also holds `scaffold_theme` behind `prism new-theme`.
- **`typography.py`** — measure and wrap text against vendored advance-width
  tables. The reason prism exists in the shape it does; see
  `know-how/typography-and-icons.md`.
- **`text.py`** — `MeasuredText` / `TextBlock`, the wrapped-text shapes that
  report true bounds to the layout engine.
- **`nodes.py`** — `Node`, the rich node shape shared by all ten archetypes.
- **`nodebox.py`** — how a `Node` is *drawn* (label, sublabel, icon, accent,
  emphasis), plus `RenderContext` (`theme`, `width`, `rng`).
- **`connectors.py`** — `connect(a, b, side, side, theme)` and prism's own
  themed arrowhead marker.
- **`icons.py`** — `IconShape`, backed by 1756 vendored Lucide outlines.
- **`frame.py`** — wraps an archetype's `Group` with title / subtitle / caption,
  fits the canvas, paints the surface, injects `role`/`<title>`/`<desc>`.
- **`archetypes/<name>/`** — `schema.py` (pydantic model), `build.py` (compose
  tesserax shapes), `__init__.py` (calls `register`). Ten of them.
- **`cli.py`** — `render`, `themes`, `icons`, `archetypes`, `new-theme`,
  `schema`.

Everything renders through `render_str`, including the CLI, the docs and the
tests. There is no second code path.

## Conventions

- Python 3.12+, `uv`, English throughout. One logical change per commit
  (conventional commits). Commit straight to `main`.
- **`uv run python -m pytest` and `uv run ruff check .` must both pass before a
  commit lands.** `uv run ruff format .` for formatting — path-scoped if the
  tree has drift you did not cause.
- **Runtime dependencies are exactly `tesserax`, `pyyaml`, `pydantic>=2`.**
  Nothing else, ever. `fonttools` and the Liberation fonts are build-time only,
  used by a script and never imported at runtime. The `export` extra adds
  `tesserax[export]` for PNG.
- Distribution name is `prism-svg`; import name is `prism`.
- **A literal colour, font size or gap inside an archetype is a bug.** Read
  `theme.color(...)`, `theme.size(role)`, `theme.weight(role)`,
  `theme.geometry.*`. That indirection is what makes four themes work with no
  per-theme special casing.
- **Rendering is deterministic and network-free.** Any randomness comes from
  `ctx.rng`, seeded by a blake2b hash of the canonical spec, so the same spec
  renders byte-identically forever. `test_golden.py` enforces this.
- **Errors are written to be read by a model.** Raise `PrismError` subclasses;
  the `_UnknownName` family does difflib "did you mean" suggestions for free.
  Every spec model is `extra="forbid"` so a typo fails loudly instead of
  silently rendering the wrong picture.
- **`docs/catalog.qmd` and `docs/themes.qmd` are generated** by
  `scripts/build_gallery.py`, as is everything under `docs/gallery/`. Editing
  them by hand is always wrong — change the script, the examples or the blurbs
  and regenerate.
- **Verify visual work visually.** A green suite and a valid SVG do not catch a
  label crossing its border, a misaligned icon or an arrow landing in the middle
  of a box. Render it and open it.

## Sharp edges

Three tesserax behaviours that already cost debugging time, all documented at
their call site:

- **`Group.stack` is a class-level global.** Constructing a tesserax shape
  auto-attaches it to the innermost active `with Group(...)`, so `render_str`
  saves and clears the stack — and must keep it cleared through SVG *generation*
  too, because `Line`/`Arrow` build their `Path` lazily at render time.
- **`Shape.anchor()` returns world coordinates; `Shape.bounds()` returns the
  parent's space.** Connectors are siblings of the layout holding the boxes, so
  `anchor()` applies the parent transform twice. Use `bounds()`.
- **`texture: sketch` is deliberately rejected.** tesserax's `Sketch` flattens a
  shape tree but drops each group's own transform, which collapses every nested
  layout onto the origin. Accepting the token without honouring it would be
  worse than refusing it.

And one of our own: **`GroupSpec` and `Link` are declared but never drawn.**
They validate and are then silently ignored. Do not advertise them in
agent-facing docs until a builder actually reads them —
`tests/test_docs.py::test_agent_docs_only_advertise_rendered_node_fields` is the
guard. (`Node.badge` and `Node.note` were in this list until 2026-07-31; see
`docs/specs/2026-07-31-node-badge-and-note-design.md` for how they got out.)

**A note is placed by the archetype, a badge by the node box.** A badge is a
flow-layout sibling of the label, so the box grows around it and every archetype
gets one for free. A note must *not* be inside the box — folding it in would
grow the bounds that `connect()` reads for arrow attachment and that every row
reads for alignment. `place_note` positions it against `box.bounds()` as a
sibling of the layout, exactly like a connector. Only `flow` and `timeline`
place notes today; each archetype declares `supports_note` explicitly and a note
on one that answers `False` raises rather than vanishing.

## Know-how index — match your task, then load the doc

- Adding a new archetype, or changing an existing one's schema or layout →
  `know-how/adding-an-archetype.md`
- Theme tokens, a colour/spacing change, branding a document set →
  `know-how/authoring-a-theme.md`
- Text overflowing a box, font metrics, icons, regenerating vendored data →
  `know-how/typography-and-icons.md`
- Cutting a release, PyPI, the docs site →
  `know-how/releasing.md`
