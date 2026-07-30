# Typography and icons

**When to reach for this:** a label overflows or wraps wrongly, a box is
absurdly padded, an icon renders at the wrong size or stroke weight, or you need
to regenerate the vendored metric / icon data.

## Why prism owns text measurement

tesserax estimates text width as `len(text) * size * 0.6`. For a proportional
font that is wrong in both directions — real advances run from ~0.22em to
~0.94em, so the estimate is **+116% on `lllll`** and **−28% on `MMMMM`**. Boxes
come out either grotesquely padded or with the label crossing the border.

So prism measures instead. `prism/typography.py` loads a vendored advance-width
table per family and weight and sums real advances:

```python
# width in user units
measure("Ingest", size=13, family="grotesque", weight=700)
# -> list[str], one per line
wrap(text, max_width, size, family, weight)
```

`wrap` is greedy, honours existing `\n` as paragraph breaks, and falls back to
`_break_word` for a single word too long for any line (so a URL degrades rather
than overflowing). `load_metrics` is `@cache`d; measurement is not a hot path
worth optimising further.

`prism/text.py` wraps that into shapes: `MeasuredText` (one line, true bounds)
and `TextBlock` (a `ColumnLayout` of them). Because they report honest bounds,
tesserax's layout engine does the right thing with no help.

**This is the whole reason the theme model restricts fonts.** `grotesque` /
`serif` / `mono` are the three stacks with metric-compatible clones everywhere
(Arial, Times New Roman, Courier New), and 400/700 are the weights whose tables
we ship. Offering a fourth family would quietly reintroduce the overflow for
every reader who does not have it.

### The regression guard

`tests/test_golden.py::test_every_label_fits_its_box` builds a node box for a
handful of adversarial labels (`WWWWW MMMMM`, `lllll iiiii`,
`Supercalifragilisticexpialidocious`) and asserts the longest measured line fits
inside the box minus padding. If you touch measuring, wrapping, `nodebox.py` or
the padding tokens, that is the test that will catch you.

### Debugging an overflow

1. Reproduce at the measurement layer first — `measure(label, size, family,
   weight)` against `box.local().width - 2 * pad`. If measurement is right, the
   bug is in layout, not typography.
2. Check the *weight* being passed. `theme.weight("label")` is 700 in every
   bundled theme; measuring a bold label against the 400 table under-reports by
   a few percent, which shows up only on long labels.
3. Check what `max_width` the archetype passed. `build_node_box` defaults to
   160; an archetype that computes its own (as `pyramid` does with
   `natural_width`) can pass something narrower than one character.

## Regenerating the metrics

```bash
sudo apt install fonts-liberation          # Debian/Ubuntu
uv run python scripts/build_metrics.py
```

Writes `prism/vendor/metrics/{grotesque,serif,mono}-{400,700}.json`. Extracts
ASCII printable + Latin-1 supplement + the typographic punctuation real prose
uses (en/em dash, curly quotes, ellipsis, euro), and records `?`'s advance as
the fallback for anything outside that set.

**`fontTools` is a dev dependency and must never be imported at runtime.** The
script runs on a developer's machine; the JSON is what ships. If you find
yourself wanting fontTools inside `prism/`, the answer is another vendored
table.

Regenerating changes measured widths, which shifts geometry, which fails
`test_golden.py::test_example_matches_golden`. That is the test doing its job —
read the diff before regenerating the golden.

## Icons

1756 Lucide outlines, vendored as normalised path `d` strings in
`prism/vendor/lucide/icons.json` (ISC licence ships alongside at
`prism/vendor/lucide/LICENSE`).

`IconShape` is a tesserax `Visual` rather than a `Path` because tesserax's `Path`
has no raw-`d` constructor. Two details matter:

- Bounds are **exact without parsing the path**, because every Lucide icon has a
  known 24×24 viewBox. `local()` just returns a `size`-square centred on origin.
- The stroke width is divided by the scale factor inside `_render`, so it lands
  at the requested width *after* the group transform. Skip that and every icon's
  outline thins as it scales up.

Icons inherit theme ink and stroke like any other geometry — they are outlines,
never raster, never filled.

An unknown name raises `UnknownIcon`, which suggests near matches by difflib.

### Regenerating the icon set

```bash
uv run python scripts/build_icons.py
```

Downloads the pinned Lucide release (`VERSION` at the top of the script),
converts each icon's `<circle>` / `<rect>` / `<line>` / `<polyline>` children to
a single path string, and rewrites `icons.json` and `LICENSE`. Bumping `VERSION`
is the only supported way to update; do not hand-edit `icons.json`.

Two doc guards keep the curated shortlists honest after a bump:
`test_agent_shortlist_icons_all_exist` (`docs/agents.qmd`) and
`test_skill_file_names_only_real_icons` (`SKILL.md`). If Lucide renames an icon,
those fail rather than shipping a name that raises for every user.
