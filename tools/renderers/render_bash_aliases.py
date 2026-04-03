#!/usr/bin/env python3
"""render_bash_aliases.py — Generate ~/.bash_aliases from Jinja2 template.

Requires db_name (runtime) passed via --extra or in the params dict.

CLI:    python3 render_bash_aliases.py --params params.json --extra db_name=DBNAME
Module: from tools.renderers.render_bash_aliases import render
"""

from pathlib import Path
try:
    from tools.renderers._base import render_template, cli_main
except ImportError:
    from _base import render_template, cli_main

_HERE = Path(__file__).parent
_TEMPLATES = _HERE.parent.parent / "platforms" / "kvm" / "templates"

DEFAULT_TEMPLATE = _TEMPLATES / "bash_aliases.j2"
DEFAULT_OUTPUT = Path("/home/erpadm/.bash_aliases")
DEFAULT_PARAMS = Path("/tmp/params.json")


def render(params, template_path=DEFAULT_TEMPLATE, output_path=DEFAULT_OUTPUT):
    """Module-mode entry point. Returns rendered string."""
    return render_template(template_path, params, output_path)


if __name__ == "__main__":
    cli_main(
        description="Render ~/.bash_aliases",
        default_template=DEFAULT_TEMPLATE,
        default_output=DEFAULT_OUTPUT,
        default_params=DEFAULT_PARAMS,
    )
