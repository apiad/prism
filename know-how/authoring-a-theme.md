# Authoring a theme

**When to reach for this:** you are adding a bundled theme, branding a document
set, or a colour / spacing change looks right in `default` and wrong in `dark`.

## Themes are data, never code

A theme is one YAML file validated into `prism.theme.Theme`. There is no hook,
no callback, no Python. Archetypes read *tokens* and nothing else, which is why
four themes need zero per-theme branching anywhere in the codebase.

`prism/themes/default.yaml` in full, as the reference:

```yaml
name: default
palette:
  surface: "#ffffff"          # page / box fill
  ink: "#111827"              # primary text
  muted: "#6b7280"            # secondary text, connectors, arrowheads
  line: "#d1d5db"             # default box border
  ramp: ["#0f766e", ...]      # >= 3 accents, indexed cyclically
  ok: "#15803d"
  warn: "#b45309"
  bad: "#b91c1c"
typography:
  family: grotesque           # grotesque | serif | mono — nothing else
  scale:  {title: 20, subtitle: 13, label: 13, sublabel: 11, note: 10, badge: 10}
  weight: {title: 700, subtitle: 400, label: 700, sublabel: 400, note: 400, badge: 700}
  line_height: 1.35
geometry:
  radius: 6                   # box corner
  stroke: 1.5                 # border / connector width
  gap: 24                     # between siblings, and the canvas padding
  pad: 12                     # inside a box
  arrow: standard             # standard | thin | block
texture: clean                # only value accepted; see below
```

Every model is `extra="forbid"`, so a misspelled token fails at load with a
"did you mean" suggestion rather than being silently ignored.

## Semantic tokens are why dark mode is free

`surface` / `ink` / `muted` / `line` name *roles*, not colours. `dark.yaml`
swaps `surface` to near-black and `ink` to near-white and every archetype
follows, because none of them ever asked for "white" or "black".

The corollary: if you find yourself wanting a fifth palette entry to make one
archetype look right, the archetype is probably reaching for a literal it should
be reading as a role.

## Two hard constraints, both enforced at load

- **`typography.family` ∈ {`grotesque`, `serif`, `mono`}** — the three stacks
  with metric-compatible clones on every platform (Arial / Helvetica, Times New
  Roman, Courier New).
- **`typography.weight.*` ∈ {400, 700}**.

These are not stylistic preferences. prism measures every label before it draws
a box, against advance-width tables it vendors; an unmeasured family or weight
would be synthesised by the viewer at a width prism never accounted for and
labels would overflow. See `know-how/typography-and-icons.md`.

`texture` accepts only `clean` for the same class of reason: tesserax's `Sketch`
drops each group's own transform when it flattens a tree, collapsing every
nested layout onto the origin. Honouring the token is a tesserax fix, not a
prism one.

## Writing one

```bash
prism new-theme house                    # copy of default, ./house.yaml
prism new-theme house --from paper       # start from the print theme
prism new-theme house -o themes/house.yaml
```

`scaffold_theme` renames the `name:` field, prepends a header explaining the two
constraints, and **loads the result before returning** — so a broken scaffold
fails immediately rather than the first time a reader renders with it.

Point a spec at it by path:

```yaml
type: flow
theme: ./house.yaml
```

`load_theme` treats a ref with no suffix as a bundled name and a ref with one as
a path, so `theme: paper` and `theme: ./paper.yaml` are different lookups.

## Per-spec overrides

For a one-off tweak, override individual tokens by dotted path instead of
forking a file:

```yaml
type: flow
theme: dark
tokens:
  palette.ink: "#f8fafc"
  geometry.radius: 2
```

The path must already exist in the theme — an unknown one raises `UnknownToken`
listing every valid path. Overrides are applied to the raw mapping *before*
validation, so they are subject to the same family/weight checks.

## Adding a bundled theme

1. Drop `prism/themes/<name>.yaml` in place. That is the whole registration —
   `bundled_themes()` globs the directory.
2. `uv run python scripts/build_gallery.py` — renders all ten archetypes in the
   new theme and regenerates `docs/themes.qmd`.
3. `uv run python -m pytest`. Four tests pick it up automatically:
   `test_bundled_theme_is_valid`, `test_sample_renders_in_every_theme`,
   `test_gallery_is_complete` and `test_themes_page_shows_every_theme`.
4. **Look at all ten diagrams.** The suite proves they render; only your eyes
   catch low contrast, an invisible border, or a `muted` that has vanished into
   the surface.

Do not hand-edit `docs/themes.qmd` — it is generated.
