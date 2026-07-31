# Drawing `Node.badge` and `Node.note`

**Status:** approved 2026-07-31, implementation in progress.

`Node` has declared `badge` and `note` since v0.1.0. Both validate, both appear
in `prism schema`, and no builder reads either — so an agent that emits one gets
a byte-identical SVG back and no signal that it was ignored. `v0.1.0` papered
over this by deleting them from the agent-facing vocabulary and adding a drift
guard (`tests/test_docs.py::test_agent_docs_only_advertise_rendered_node_fields`)
to keep them out. This slice draws them instead, and lets the guard pass on its
own terms.

The original design (`2026-07-29-declarative-diagrams-design.md`, lines 222–228)
specifies both:

```yaml
badge: "1"                  # optional; short marker, <= 4 chars
note: "runs nightly"        # optional; rendered as marginal annotation
```

Every bundled theme already carries the tokens — `scale.badge: 10 / weight 700`
and `scale.note: 10 / weight 400`. Nothing about themes changes here.

## The asymmetry that shapes this design

A badge lives **inside** the node; a note lives **outside** it. That single
difference decides everything below.

Because a badge is inside, it can be a plain flow-layout sibling of the label:
the box grows to hold it, `Container` bounds stay correct by construction, and
`connect()` keeps attaching arrows to the real border. No archetype has to know
it exists. All seven archetypes that route through `build_node_box` get badges
for free.

A note cannot work that way. Rendering it below the box would grow the node's
outer bounds downward, which means arrows start landing on the annotation's
bottom edge instead of the box's, and a noted node becomes taller than its
unnoted siblings — breaking middle-alignment in every row and column. A note is
therefore **positioned by the archetype**, after layout, against the box's
`bounds()`, and deliberately kept out of the shape whose bounds the layout reads.

## Badge

Rendered in `build_node_box`, as the right-hand item of a top-aligned row:

```
RowLayout([body, badge], align="start")
```

The pill is a `Container` holding one `MeasuredText`, with
`corner_radius=theme.geometry.radius` so it echoes the node box, filled with the
node's accent (or `ink` when it has none, `muted` when the node is muted) and
lettered in `surface` for contrast. Size and weight come from the `badge` role.

The four-character cap is already enforced by the schema, so the pill never
wraps and never needs its own overflow rule.

## Note

Rendered by `build_note`, which returns an unparented left-anchored `TextBlock`
in `note` type and `muted` colour, and by `place_note`, which moves it against a
box's `bounds()`.

**Placement rule: a note goes on the side away from the connective tissue.**
That is the whole rule, and it falls out of each archetype's geometry:

| Archetype | Spine / arrows run | Note lands |
|---|---|---|
| `flow`, `direction: right` | horizontally between boxes | below the box |
| `flow`, `direction: down` | vertically between boxes | right of the box |
| `timeline`, horizontal | spine above the track | below the box |
| `timeline`, vertical | spine left of the track | right of the box |

Below-notes wrap to the box's own width, so the annotation reads as belonging to
that node. Right-notes wrap to a fixed 120pt column, which is the width a
short annotation wants before it starts competing with the label.

## Only `flow` and `timeline`, and loudly so

The other eight archetypes do not place notes in this slice. `cycle` and `hub`
are radial, so "beside the box" is a direction that changes per node; `hierarchy`
would collide a note with the subtree beneath it; `comparison` and `matrix` are
grids with no margin between cells; `pyramid`, `quadrant` and `stack` never build
a node box at all.

A note on any of those raises `SpecError` rather than being silently dropped.
This is the same reasoning that makes every spec model `extra="forbid"`: a field
that quietly does nothing is worse than one that fails, because the failure is
the only thing that tells an agent to stop emitting it.

Each archetype declares its own answer as a class attribute on the `Archetype`
protocol:

```python
class FlowArchetype:
    name = "flow"
    spec_model = FlowSpec
    supports_note = True
```

All ten set it explicitly — no `getattr` default — so adding archetype #11
forces the author to decide rather than inherit a silent `False`.

The check runs once in `render_str`, after spec validation, over every `Node`
reachable in the spec. `hierarchy` nests nodes through `children`, so the walk
is recursive over pydantic models rather than a scan of one known list.

## Testing

- **Badge.** Present in the SVG; absent when unset; widens the box; picks up the
  accent colour; still renders when the node also carries an icon and a sublabel.
- **Note.** Present in the SVG for `flow` and `timeline`; sits *outside* the box
  bounds, on the expected side for each direction and orientation; wraps to the
  box width when below.
- **The bounds invariant, which is the whole risk of this slice.** A `flow`
  whose steps carry notes must place its boxes at the same coordinates as the
  identical flow without them — the assertion that a note cannot disturb layout
  or connector attachment. Same for badges not perturbing *other* nodes.
- **Rejection.** A note on each of the eight unsupported archetypes raises
  `SpecError` naming the archetype and the offending node.
- **The docs guard flips.** `_rendered_node_fields()` must now report `badge` and
  `note`, letting `SKILL.md` and `docs/agents.qmd` advertise them again.
- **Golden.** Determinism is unchanged; goldens are regenerated for the two
  examples that gain the fields.

## Out of scope

`GroupSpec` and `Link` remain declared and undrawn. They are a larger problem —
both imply a layout engine decision rather than an annotation — and the drift
guard keeps them out of the vocabulary until then.
