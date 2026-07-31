# Adding (or changing) an archetype

**When to reach for this:** you are adding an eleventh diagram type, adding a
field to one of the ten that ship, or chasing a layout bug inside a `build.py`.

## What an archetype is

Three files under `prism/archetypes/<name>/`, and nothing else:

| File | Holds |
|---|---|
| `schema.py` | one pydantic model, `extra="forbid"` |
| `build.py` | a class with `name`, `spec_model`, `supports_note`, and `build(spec, ctx) -> Group` |
| `__init__.py` | `register(TheArchetype())` |

`flow` is the whole pattern in 56 lines across the three — read it first.
`pyramid` is the one to read when your layout is not a stock tesserax
`RowLayout` / `ColumnLayout`.

The registry is a `Protocol`, not a base class. There is nothing to inherit; if
your object has the four members it *is* an archetype.

`supports_note` has no default on purpose, and
`tests/test_badge_and_note.py::test_every_archetype_declares_whether_it_places_notes`
fails if you leave it out. Answer `True` only if your layout has a margin the
annotation can live in *without* being folded into the node box — see
`docs/specs/2026-07-31-node-badge-and-note-design.md` for why that distinction
is not cosmetic. Answering `False` is a fine answer; it makes a note on your
archetype a loud error rather than a silent no-op.

## The procedure

1. **Reuse `Node` before inventing a shape.** Every archetype consumes the same
   node vocabulary (`label`, `sublabel`, `icon`, `accent`, `emphasis`), and that
   sameness is most of what makes the library learnable. Need one extra field?
   Subclass — `pyramid` does exactly that:

   ```python
   class Level(Node):
       value: float | None = None
   ```

   Do not redefine `label` or copy the field list.

2. **Write the schema.** `model_config = ConfigDict(extra="forbid")` is not
   optional — it is what turns an agent's typo into a loud `SpecError` instead
   of a quietly wrong picture. Use `Field(min_length=...)` for collections that
   are meaningless when empty. Every field needs a default or the spec becomes
   hostile to write by hand.

3. **Register in two places.** `__init__.py` calls `register(...)`, and the
   archetype's module must be listed in `prism/archetypes/__init__.py` — that
   import *is* the registration, and it is what makes the CLI, the schema
   command and the docs see it.

4. **Build with tokens only.** Read `theme.color(...)`, `theme.size(role)`,
   `theme.weight(role)`, `theme.geometry.{gap,pad,radius,stroke}`. A literal
   `"#333"` or `gap=24` in a `build.py` is a bug: it is the one thing that makes
   a diagram render wrong in `dark` while looking fine in `default`.

5. **Prefer the shared helpers over raw tesserax.** `prism/nodebox.py` and
   `prism/shapes.py` already solve the recurring problems:

   - `build_node_box(node, ctx, max_width=...)` — the standard bordered box.
   - `text_stack(node, ctx, max_width)` / `natural_width(node, ctx)` — a
     label+sublabel column, and how wide it *wants* to be. `natural_width` is
     how `pyramid` decides whether a label fits inside its band or must go
     alongside it.
   - `at(shape, x, y)`, `centered`, `bar`, `trapezoid`, `union_width`,
     `measured_height`, `bounds_of`.
   - `connect(a, b, side_from, side_to, theme)` for a themed arrow.

6. **Return one `Group`.** Do not build a `Canvas`, do not set a title, do not
   add padding for the caption — `frame.py` owns all of that, uniformly, for
   every archetype.

7. **Add the sample and the example.** Two files, both enforced by tests:

   - `tests/samples.py` — a `SAMPLES[name]` entry, or
     `test_every_registered_archetype_has_a_sample` fails.
   - `examples/<name>.yaml` — or `test_every_archetype_has_an_example` fails.

   Adding those two gets you, for free: renders-to-SVG, deterministic,
   non-degenerate size, and renders-in-all-four-themes.

8. **Add a blurb and regenerate the docs.**

   ```bash
   # add BLURBS["<name>"] in scripts/build_gallery.py first
   uv run python scripts/build_gallery.py
   ```

   That writes `docs/gallery/*.svg` plus the generated `docs/catalog.qmd` and
   `docs/themes.qmd`. **Never hand-edit those two pages.**

9. **Document it for consumers.** `SKILL.md` must contain a `type: <name>`
   block (`test_skill_file_covers_every_archetype` checks), and only real icon
   names may appear in its shortlist.

10. **Look at it.** `prism render examples/<name>.yaml -o /tmp/x.svg` and open
    it, in at least `default` and `dark`. The suite proves the SVG is valid and
    non-degenerate; it does not prove the picture is good. Check labels inside
    their borders, arrows meeting box edges, and nothing overlapping.

## Changing an existing archetype

- **Adding an optional field is safe.** Adding a required one, renaming, or
  changing a `Literal`'s members is a breaking change for every spec in the
  wild — including the examples, the samples and the golden file.
- **`tests/golden/flow.svg` will fail** for any change that shifts geometry in
  `flow`. If the change is intentional, the failure message prints the exact
  regeneration command. Read the diff before accepting it; that test is the only
  thing standing between a refactor and a silently uglier diagram.
- Grep for the field name across `SKILL.md`, `docs/agents.qmd` and
  `docs/catalog.qmd` before you finish. The consumer docs are the contract.

## The trap

**A field on the model that no builder reads is worse than no field at all.**
It validates, it appears in `prism schema`, an agent emits it — and nothing is
drawn, with no error. `Node.badge` and `Node.note` are in exactly that state
today, which is why
`tests/test_docs.py::test_agent_docs_only_advertise_rendered_node_fields`
exists: it fails if the agent-facing docs advertise a `Node` field that no
builder consumes. Either draw the field or leave it out of the docs.
