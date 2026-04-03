#!/usr/bin/env python3
"""render_supervisor.py — Generate ce-sri-svc supervisor conf from Jinja2 template.

CLI:    python3 render_supervisor.py --params params.json
Module: from tools.renderers.render_supervisor import render
"""

from pathlib import Path
try:
    from tools.renderers._base import render_template, cli_main
except ImportError:
    from _base import render_template, cli_main

_HERE = Path(__file__).parent
_TEMPLATES = _HERE.parent.parent / "platforms" / "kvm" / "templates"

DEFAULT_TEMPLATE = _TEMPLATES / "ce_sri_svc_supervisor.conf.j2"
DEFAULT_OUTPUT = Path("/etc/supervisor/conf.d/ce-sri-svc.conf")
DEFAULT_PARAMS = Path("/tmp/params.json")


def render(params, template_path=DEFAULT_TEMPLATE, output_path=DEFAULT_OUTPUT):
    """Module-mode entry point. Returns rendered string."""
    return render_template(template_path, params, output_path, file_mode=0o644)


if __name__ == "__main__":
    cli_main(
        description="Render ce-sri-svc supervisor config",
        default_template=DEFAULT_TEMPLATE,
        default_output=DEFAULT_OUTPUT,
        default_params=DEFAULT_PARAMS,
        file_mode=0o644,
    )
