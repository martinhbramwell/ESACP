#!/usr/bin/env python3
"""render_envars.py — Generate /opt/ce_sri/envars.sh from Jinja2 template.

CLI:    python3 render_envars.py --params params.json [--output /opt/ce_sri/envars.sh]
Module: from tools.renderers.render_envars import render
"""

from pathlib import Path
try:
    from tools.renderers._base import render_template, cli_main
except ImportError:
    from _base import render_template, cli_main

_HERE = Path(__file__).parent
_TEMPLATES = _HERE.parent.parent / "platforms" / "kvm" / "templates"

DEFAULT_TEMPLATE = _TEMPLATES / "envars.sh.j2"
DEFAULT_OUTPUT = Path("/opt/ce_sri/envars.sh")
DEFAULT_PARAMS = Path("/tmp/params.json")


def render(params, template_path=DEFAULT_TEMPLATE, output_path=DEFAULT_OUTPUT):
    """Module-mode entry point. Returns rendered string."""
    return render_template(template_path, params, output_path, file_mode=0o644)


if __name__ == "__main__":
    cli_main(
        description="Render /opt/ce_sri/envars.sh",
        default_template=DEFAULT_TEMPLATE,
        default_output=DEFAULT_OUTPUT,
        default_params=DEFAULT_PARAMS,
        file_mode=0o644,
    )
