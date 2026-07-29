"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import render, render_str
from .errors import PrismError
from .icons import icon_names
from .registry import get
from .registry import names as archetype_names
from .theme import bundled_themes, scaffold_theme


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prism", description="Declarative YAML to SVG diagrams."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_cmd = sub.add_parser("render", help="render a spec to SVG")
    render_cmd.add_argument("spec", help="path to a YAML spec")
    render_cmd.add_argument(
        "-o", "--output", help="output path; writes to stdout when omitted"
    )

    sub.add_parser("themes", help="list bundled themes")
    sub.add_parser("icons", help="list available icon names")
    sub.add_parser("archetypes", help="list available archetypes")

    new_theme = sub.add_parser(
        "new-theme", help="scaffold an editable theme file from a bundled one"
    )
    new_theme.add_argument("name", help="name for the new theme")
    new_theme.add_argument(
        "--from",
        dest="source",
        default="default",
        metavar="THEME",
        help="bundled theme to copy (default: default)",
    )
    new_theme.add_argument(
        "-o", "--output", help="where to write it (default: <name>.yaml here)"
    )
    new_theme.add_argument(
        "--force", action="store_true", help="overwrite an existing file"
    )

    schema_cmd = sub.add_parser(
        "schema", help="print an archetype's JSON Schema for tool calling"
    )
    schema_cmd.add_argument("archetype", help="archetype name")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        match args.command:
            case "render":
                if args.output:
                    render(args.spec, args.output)
                else:
                    sys.stdout.write(render_str(args.spec))
            case "themes":
                print("\n".join(bundled_themes()))
            case "icons":
                print("\n".join(icon_names()))
            case "archetypes":
                print("\n".join(archetype_names()))
            case "new-theme":
                written = scaffold_theme(
                    args.name,
                    source=args.source,
                    out_path=args.output,
                    force=args.force,
                )
                print(f"wrote {written}")
                print(f"use it with:  theme: {written}")
            case "schema":
                schema = get(args.archetype).spec_model.model_json_schema()
                print(json.dumps(schema, indent=2))
    except PrismError as exc:
        print(f"prism: {exc}", file=sys.stderr)
        return 1

    return 0
