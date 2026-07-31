"""Chronology: a spine, a marker per event, and optional era bands."""

from __future__ import annotations

from tesserax import Circle, Group, Line, Rect
from tesserax.core import Bounds, Point, Shape
from tesserax.layout import ColumnLayout, RowLayout

from ...errors import SpecError
from ...nodebox import NoteSide, RenderContext, build_node_box, place_note
from ...shapes import at
from ...text import MeasuredText
from .schema import Era, TimelineSpec

DOT_RADIUS = 5.0
ERA_OPACITY = 0.10


def note_side(spec: TimelineSpec) -> NoteSide:
    """The spine sits above a horizontal track and left of a vertical one, so
    the free margin is on the opposite side in each case."""
    return "below" if spec.orientation == "horizontal" else "right"


class TimelineArchetype:
    name = "timeline"
    spec_model = TimelineSpec
    supports_note = True

    def build(self, spec: TimelineSpec, ctx: RenderContext) -> Group:
        theme = ctx.theme
        horizontal = spec.orientation == "horizontal"
        boxes = [build_node_box(event, ctx, max_width=140) for event in spec.events]

        if horizontal:
            track = RowLayout(boxes, align="start", gap=theme.geometry.gap)
        else:
            track = ColumnLayout(boxes, align="start", gap=theme.geometry.gap)

        span = track.local()
        offset = theme.geometry.gap * 1.4
        # The spine sits above a horizontal track, and left of a vertical one.
        spine_at = span.y - offset if horizontal else span.x - offset

        marks: list[Shape] = []
        for event, box in zip(spec.events, boxes, strict=True):
            bounds = box.bounds()
            centre = (
                Point(bounds.x + bounds.width / 2, spine_at)
                if horizontal
                else Point(spine_at, bounds.y + bounds.height / 2)
            )
            dot = Circle(
                DOT_RADIUS,
                fill=theme.color(event.accent if event.accent is not None else "ink"),
                stroke=theme.color("surface"),
                width=theme.geometry.stroke,
            )
            at(dot, centre.x, centre.y)
            marks.append(dot)

            if event.when:
                stamp = MeasuredText(
                    event.when,
                    size=theme.size("note"),
                    fill=theme.color("muted"),
                    family=theme.typography.family,
                    weight=theme.weight("note"),
                    anchor="middle" if horizontal else "end",
                )
                gap = theme.geometry.pad
                if horizontal:
                    at(
                        stamp,
                        centre.x,
                        centre.y - gap - stamp.local().height / 2,
                    )
                else:
                    at(
                        stamp,
                        centre.x - gap - stamp.local().width / 2,
                        centre.y,
                    )
                marks.append(stamp)

        first, last = marks[0].bounds(), None
        for shape in marks:
            if isinstance(shape, Circle):
                last = shape.bounds()
        spine = Line(
            Point(first.x + first.width / 2, spine_at)
            if horizontal
            else Point(spine_at, first.y + first.height / 2),
            Point(last.x + last.width / 2, spine_at)
            if horizontal
            else Point(spine_at, last.y + last.height / 2),
            stroke=theme.color("line"),
            width=theme.geometry.stroke * 1.5,
        )

        side = note_side(spec)
        notes: list[Shape] = []
        # An era band has to enclose everything its events own, annotations
        # included — a band whose edge slices through a note reads as excluding
        # it from the era it belongs to.
        footprints: list[Bounds] = []
        for event, box in zip(spec.events, boxes, strict=True):
            note = place_note(event, box, ctx, side)
            if note is None:
                footprints.append(box.bounds())
            else:
                notes.append(note)
                footprints.append(Bounds.union(box.bounds(), note.bounds()))

        marks_bounds = Bounds.union(*[m.bounds() for m in marks])
        bands = self._era_bands(spec, footprints, ctx, horizontal, marks_bounds)

        return Group([*bands, spine, track, *marks, *notes])

    def _era_bands(
        self,
        spec: TimelineSpec,
        footprints: list[Bounds],
        ctx: RenderContext,
        horizontal: bool,
        marks: Bounds,
    ) -> list[Shape]:
        if not spec.eras:
            return []

        theme = ctx.theme
        index_by_id = {
            event.id: position for position, event in enumerate(spec.events) if event.id
        }

        bands: list[Shape] = []
        for index, era in enumerate(spec.eras):
            first_i, last_i = self._resolve(era, index_by_id)
            a, b = footprints[first_i], footprints[last_i]
            # The tallest event in the span need not be an endpoint, so the
            # cross-axis extent comes from every event the era covers.
            lo, hi = min(first_i, last_i), max(first_i, last_i)
            span = Bounds.union(*footprints[lo : hi + 1])
            accent = era.accent if era.accent is not None else index
            pad = theme.geometry.pad

            # Leave a row for the era caption above (or beside) everything
            # the spine already carries, so it cannot collide with a date.
            caption_room = theme.size("note") * 1.8

            if horizontal:
                left = a.x - pad
                right = b.x + b.width + pad
                top = marks.y - caption_room
                bottom = span.y + span.height + pad
            else:
                top = a.y - pad
                bottom = b.y + b.height + pad
                left = marks.x - caption_room
                right = span.x + span.width + pad

            width, height = right - left, bottom - top
            centre = Point(left + width / 2, top + height / 2)

            band = Rect(
                width,
                height,
                fill=theme.color(accent),
                stroke=theme.color(accent),
                width=theme.geometry.stroke,
                opacity=ERA_OPACITY,
            )
            at(band, centre.x, centre.y)
            bands.append(band)

            tag = MeasuredText(
                era.label,
                size=theme.size("note"),
                fill=theme.color(accent),
                family=theme.typography.family,
                weight=theme.weight("badge"),
                anchor="start",
            )
            at(
                tag,
                left + tag.local().width / 2 + theme.geometry.pad / 2,
                top + tag.local().height / 2 + theme.geometry.pad / 3,
            )
            bands.append(tag)

        return bands

    @staticmethod
    def _resolve(era: Era, index_by_id: dict[str, int]) -> tuple[int, int]:
        missing = [key for key in era.span if key not in index_by_id]
        if missing:
            raise SpecError(
                f"era {era.label!r} spans unknown event id(s) {missing}; "
                f"known ids: {sorted(index_by_id) or 'none — give your events an id'}"
            )
        return index_by_id[era.span[0]], index_by_id[era.span[1]]
