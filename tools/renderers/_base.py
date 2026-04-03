"""Shared rendering logic for config artifact renderers.

Provides render_template(), load_params(), and cli_main() used by every
render_*.py script. Requires jinja2.
"""

import argparse
import json
import sys
from pathlib import Path

import jinja2


def render_template(template_path, params, output_path=None, *, file_mode=None):
    """Load a Jinja2 template, render with params, optionally write to output_path.

    Args:
        template_path: Path to the .j2 template file.
        params: dict of template variables.
        output_path: If given, write rendered content to this path.
        file_mode: If given, chmod the output file (e.g. 0o644).

    Returns:
        The rendered string.
    """
    template_path = Path(template_path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent)),
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    rendered = env.get_template(template_path.name).render(**params)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        if file_mode is not None:
            output_path.chmod(file_mode)

    return rendered


def load_params(path):
    """Load a JSON params file and return a dict."""
    with open(path) as f:
        return json.load(f)


def cli_main(description, default_template, default_output, default_params=None,
             *, file_mode=None):
    """Standard argparse entrypoint reused by every renderer CLI.

    Parses --template, --params, --output, --extra KEY=VALUE, renders, and writes.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--template", type=Path, default=default_template,
                        help=f"Jinja2 template (default: {default_template})")
    parser.add_argument("--params", type=Path, default=default_params,
                        help="JSON params file")
    parser.add_argument("--output", type=Path, default=default_output,
                        help=f"Output file (default: {default_output})")
    parser.add_argument("--extra", nargs="*", metavar="KEY=VALUE",
                        help="Extra params as key=value pairs (override JSON)")
    args = parser.parse_args()

    if args.params and args.params.exists():
        params = load_params(args.params)
    elif args.params:
        print(f"ERROR: params file not found: {args.params}", file=sys.stderr)
        sys.exit(1)
    else:
        params = {}

    if args.extra:
        for kv in args.extra:
            k, _, v = kv.partition("=")
            if not k:
                print(f"ERROR: invalid --extra format: {kv!r} (use KEY=VALUE)", file=sys.stderr)
                sys.exit(1)
            params[k] = v

    render_template(args.template, params, args.output, file_mode=file_mode)
    print(f"[OK] {args.output}")
