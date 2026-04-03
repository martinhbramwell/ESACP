#!/usr/bin/env python3
"""render_gh_askpass.py — Generate SSH_ASKPASS script from Jinja2 template.

CLI:    python3 render_gh_askpass.py --params params.json
Module: from tools.renderers.render_gh_askpass import render
"""

from pathlib import Path
try:
    from tools.renderers._base import render_template, cli_main
except ImportError:
    from _base import render_template, cli_main

_HERE = Path(__file__).parent
_TEMPLATES = _HERE.parent.parent / "platforms" / "kvm" / "templates"

DEFAULT_TEMPLATE = _TEMPLATES / "gh_askpass.sh.j2"
DEFAULT_OUTPUT = Path("/home/erpadm/.ssh/gh_askpass.sh")
DEFAULT_PARAMS = Path("/tmp/params.json")


def render(params, template_path=DEFAULT_TEMPLATE, output_path=DEFAULT_OUTPUT):
    """Module-mode entry point. Returns rendered string."""
    return render_template(template_path, params, output_path, file_mode=0o700)


if __name__ == "__main__":
    cli_main(
        description="Render SSH_ASKPASS script",
        default_template=DEFAULT_TEMPLATE,
        default_output=DEFAULT_OUTPUT,
        default_params=DEFAULT_PARAMS,
        file_mode=0o700,
    )
