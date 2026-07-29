---
name: prism-diagrams
description: Use when you need to produce a diagram — a process, hierarchy, cycle, timeline, comparison, quadrant, pyramid, funnel, tier stack, hub-and-spoke, or a matrix of values. Emit a prism YAML spec and render it to SVG. Do not hand-write SVG, and do not reach for Mermaid unless the content is genuinely a node-edge graph.
---

# Writing prism specs

prism turns a YAML spec into a designed SVG diagram. You decide **what the
picture means**; prism decides geometry, spacing, typography and colour. Never
hand-place coordinates — there are none to place.

## Procedure

1. Decide the *shape of the meaning* (see the table below) — not the subject.
2. Write the spec. Keep it to 3–7 nodes; a diagram with twelve boxes explains
   less than two diagrams with six.
3. Render: `prism render spec.yaml -o out.svg`, or in Python
   `prism.render("spec.yaml", "out.svg")`.
4. If it errors, read the message — it names the bad value and suggests valid
   neighbours — and fix the spec. Do not work around an error by changing
   archetype.

## Choosing the archetype

| If the content is… | Use |
|---|---|
| ordered steps, a process, a pipeline | `flow` |
| containment, reporting structure, decomposition | `hierarchy` |
| a process that returns to its start | `cycle` |
| events in time | `timeline` |
| two or more options weighed against each other | `comparison` |
| items placed against two independent dimensions | `quadrant` |
| layers of magnitude, or stages that shed volume | `pyramid` |
| tiers of a system, bottom to top | `stack` |
| one centre with several dependents | `hub` |
| values at the intersection of two lists | `matrix` |

When two fit, choose the one that puts fewer nodes on screen.

## The envelope

```yaml
type: flow                   # required: the archetype
theme: default               # default | dark | paper | mono, or a path
title: "Ingestion pipeline"  # optional
subtitle: "as of Q3"         # optional
caption: "Source: review"    # optional
width: 900                   # optional layout hint
```

## The shared node

Identical across all ten archetypes:

```yaml
id: ingest              # only needed when something references it
label: "Ingest"         # required
sublabel: "S3 + Kafka"  # optional
icon: database          # optional, Lucide name
badge: "1"              # optional, <= 4 chars
accent: 0               # optional, ramp index 0-5, or a palette token name
emphasis: normal        # strong | normal | muted
```

## The archetypes

```yaml
type: flow
direction: right          # right | down
steps: [<node>, ...]      # at least 1
```

```yaml
type: hierarchy
direction: down           # down | right
root: {<node>, children: [{<node>, children: [...]}, ...]}
```

```yaml
type: cycle
direction: clockwise      # clockwise | counterclockwise
center: <node>            # optional label in the middle
steps: [<node>, ...]      # at least 2
```

```yaml
type: timeline
orientation: horizontal   # horizontal | vertical
events: [{<node>, when: "2024 Q2"}, ...]
eras: [{label: "Beta", span: [<event id>, <event id>], accent: 1}]
```

```yaml
type: comparison
criteria: ["Cost", "Speed"]        # optional; if set, every column needs
columns:                           # exactly one item per criterion, in order
  - header: <node>
    items: [<node>, ...]
```

```yaml
type: quadrant
axes:
  x: {label: "Effort", low: "Low", high: "High"}
  y: {label: "Impact", low: "Low", high: "High"}
quadrant_labels: ["top-left", "top-right", "bottom-left", "bottom-right"]
items: [{<node>, x: 0.8, y: 0.3}, ...]     # x and y in 0..1, y is up
```

```yaml
type: pyramid
invert: false                       # narrow at top by default
levels: [{<node>, value: 1200}, ...]  # values, if given on every level,
                                      # set the widths and make it a funnel
```

```yaml
type: stack
order: top_down           # top_down | bottom_up
layers: [{<node>, side: "L7"}, ...]
```

```yaml
type: hub
center: <node>
spokes: [<node>, ...]     # at least 2
ring: false               # join the spokes with a ring
```

```yaml
type: matrix
rows: [{id: emea, label: "EMEA"}, ...]
columns: [{id: q1, label: "Q1"}, ...]
cells: [{row: emea, column: q1, label: "1.2M", accent: 0}, ...]   # sparse
```

## Icons

Prefer this shortlist; run `prism icons` only if nothing fits.

`activity` `archive` `bell` `book` `box` `brain` `briefcase` `building`
`calendar` `chart-line` `chart-pie` `check` `circle-check` `clock` `cloud`
`code` `cog` `compass` `cpu` `credit-card` `database` `eye` `file-text` `flag`
`flask-conical` `folder` `funnel` `gauge` `git-branch` `globe` `hammer` `heart`
`key-round` `layers` `lightbulb` `link` `lock` `mail` `map-pin`
`message-circle` `package` `pencil` `phone` `play` `plug` `rocket` `search`
`send` `server` `settings` `shield` `shield-check` `shopping-cart` `sparkles`
`sprout` `star` `target` `terminal` `trending-up` `triangle-alert` `truck`
`upload` `users` `wallet` `wrench` `zap`

## Rules

- **One diagram per spec.** Two ideas means two specs.
- **Never invent fields.** Every archetype rejects unknown keys. Check with
  `prism schema <archetype>`.
- **Never set colours directly.** Use `accent` with a ramp index; the theme owns
  the palette. Change the look with `theme:`, not per-node colours.
- **Keep labels short.** Two or three words. Detail belongs in `sublabel`.
- **Do not nest archetypes.** Only `hierarchy` recurses, through `children`.
