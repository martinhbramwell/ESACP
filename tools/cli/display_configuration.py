"""CLI: print the lab configuration tree + service URLs."""

from __future__ import annotations

from tools.cli._common import banner, console
from tools.cli.display.config_tree import build_tree
from tools.cli.display.url_table import build_url_table


def run(args, config: dict) -> int:
    banner("Lab Configuration")
    console.print(build_tree(config))
    urls = build_url_table(config)
    if urls is not None:
        console.print()
        console.print(urls)
    return 0
