#!/usr/bin/env python3
"""render_nginx_vhost.py — Generate nginx TLS vhost config from Jinja2 template.

CLI:    python3 render_nginx_vhost.py --params params.json
Module: from tools.renderers.render_nginx_vhost import render
"""

from pathlib import Path
try:
    from tools.renderers._base import render_template, cli_main
except ImportError:
    from _base import render_template, cli_main

_HERE = Path(__file__).parent
_TEMPLATES = _HERE.parent.parent / "platforms" / "kvm" / "templates"

DEFAULT_TEMPLATE = _TEMPLATES / "nginx_vhost.conf.j2"
DEFAULT_OUTPUT = Path("/etc/nginx/sites-available/site.conf")
DEFAULT_PARAMS = Path("/tmp/params.json")


def render(params, template_path=DEFAULT_TEMPLATE, output_path=DEFAULT_OUTPUT):
    """Module-mode entry point. Returns rendered string."""
    return render_template(template_path, params, output_path, file_mode=0o644)


if __name__ == "__main__":
    cli_main(
        description="Render nginx TLS vhost config",
        default_template=DEFAULT_TEMPLATE,
        default_output=DEFAULT_OUTPUT,
        default_params=DEFAULT_PARAMS,
        file_mode=0o644,
    )
