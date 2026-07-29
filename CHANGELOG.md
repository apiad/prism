# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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
