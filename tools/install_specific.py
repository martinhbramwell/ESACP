#!/usr/bin/env python3
"""Thin entry — dispatches to the install_specific package.

On controller: package at tools/vm_scripts/install_specific/.
On VM: package at /tmp/vm_scripts/install_specific/ (rsynced by stage_4).
"""

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
for _candidate in (_here / "vm_scripts", Path("/tmp/vm_scripts")):
    if (_candidate / "install_specific").is_dir():
        sys.path.insert(0, str(_candidate))
        break

from install_specific import (  # noqa: E402
    cmd_after_restart, cmd_before_install, cmd_gate, cmd_phase1,
)

COMMANDS = {
    "phase1": cmd_phase1,
    "gate": cmd_gate,
    "before-install": cmd_before_install,
    "after-restart": cmd_after_restart,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("phase1", help="BaRe clone, envars symlink, bash_aliases")
    sub.add_parser("gate", help="handleBackup (first run) or handleRestore")
    sub.add_parser("before-install", help="File patches (no gunicorn needed)")
    sub.add_parser("after-restart", help="API work (gunicorn must be running)")
    args = parser.parse_args()

    fn = COMMANDS.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    fn()


if __name__ == "__main__":
    main()
