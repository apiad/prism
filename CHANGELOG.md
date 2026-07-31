# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **`Node.badge` is drawn.** A short marker — a step number, a version, a count
  — rendered as an accent-filled pill inside the top-right of the node, lettered
  in `surface` so it reads against its own fill. It is a flow-layout sibling of
  the label rather than an overlay, so the box grows to hold it and its bounds
  stay honest. Every archetype that builds a node box gets badges.

- **`Node.note` is drawn, by `flow` and `timeline`.** A marginal annotation in
  muted `note` type, placed *outside* the node box: below it when the layout
  runs left-to-right, beside it when the layout runs top-down — always on the
  side the spine and arrows do not use. Notes cannot disturb layout, and
  `tests/test_badge_and_note.py` asserts that a flow's arrows land in exactly
  the same place with and without them.

  On the other eight archetypes a note now raises `SpecError` naming the
  offending nodes, rather than validating and changing nothing. Each archetype
  declares `supports_note` explicitly — there is no default to inherit.

  Both fields are back in `SKILL.md` and the agent guide, which the drift guard
  had kept them out of while nothing read them.

### Fixed

- A timeline era band now encloses the notes of the events it spans, and takes
  its cross-axis extent from every event in the span rather than just the two
  endpoints. The old bound came from the endpoint boxes alone, so a band could
  stop above a note that belonged inside it — or clip a taller event in the
  middle of the span.

### Changed

- `badge` and `note` are no longer part of the documented node vocabulary in
  `SKILL.md` and the agent guide. Both are still accepted by the models — and
  still appear in `prism schema` — but no archetype draws them, so emitting one
  silently changed nothing. A drift guard now fails if the agent-facing docs
  advertise a `Node` field that no builder reads.
- README prose links point at the published docs site rather than at
  `docs/*.qmd`, which GitHub renders as raw Quarto source.

### Added

- `AGENTS.md` and `know-how/` — the repo's own orientation and procedure docs
  (adding an archetype, authoring a theme, typography and icons, releasing).

- `prism new-theme <name> [--from <theme>] [-o <path>] [--force]` — scaffolds an
  editable theme file from a bundled one, renames it, prepends a header
  explaining the family and weight constraints, and validates the result before
  writing it. Replaces the `python -c "... shutil.copy ..."` incantation the
  tutorial previously asked readers to type.

## [0.1.0] - 2026-07-29

First release. prism is now a declarative YAML → SVG diagram library built on
[tesserax](https://github.com/apiad/tesserax), replacing the artifact engine
that previously carried this name (now vendored into AI-n-Box).

### Added

- **Ten archetypes**: `flow`, `hierarchy`, `cycle`, `timeline`, `comparison`,
  `quadrant`, `pyramid` (invertible into a funnel), `stack`, `hub`, `matrix`.
- **Four themes**: `default`, `dark`, `paper`, `mono`. Themes are data — a token
  set in YAML covering palette, typography and geometry — with semantic tokens
  so dark mode requires no special casing. Per-spec overrides by dotted path.
- **prism-owned typography**: vendored advance-width tables for Arial, Times New
  Roman and Courier New (the three stacks with metric-compatible clones on every
  platform), greedy word-wrap, and a `MeasuredText` that hands true bounds to
  tesserax's layout engines.
- **1756 vendored Lucide icons** (ISC), normalised to path data, inheriting theme
  ink and stroke width.
- **Agent surface**: closed flat vocabulary, `prism schema <archetype>` for JSON
  Schema, and errors that name the offending value and suggest neighbours.
- **Python API** — `render`, `render_str`, `diagram` (self-displaying in Jupyter
  and Quarto) — and a CLI: `render`, `archetypes`, `themes`, `icons`, `schema`.
- Deterministic output: the same spec always produces byte-identical SVG.
- Accessibility: `role="img"` plus `<title>` and `<desc>` on every diagram.
- Documentation site (Quarto) with a gallery generated from the bundled
  examples, so the docs cannot drift from what actually renders.

### Known limitations

- `texture: sketch` is **not** implemented. tesserax's `Sketch` flattens a shape
  tree but drops each group's own transform, which collapses every nested layout
  onto the origin. The token is rejected rather than silently mis-rendered.
- Icons are drawn as raw path data rather than through `tesserax.Path`, which has
  no way to accept a `d` string. This is invisible today but means icons would
  not pick up a future sketch texture.
- `flow` implements the linear spine only. `branches`, `lanes`, `phases`, `links`
  and `groups` are designed but not yet built; they are additive, so no spec
  written today will break when they land.
- Deferred archetypes: `network`, `venn`, `journey`, `roadmap`, `sequence`.
