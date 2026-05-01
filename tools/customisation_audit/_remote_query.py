#!/usr/bin/env python3
"""Run on a dev VM: read site_config.json, execute SQL, emit JSON to stdout.

Invoked by ``db_query.py`` over SSH. Single argv:
    python3 /tmp/_audit_query.py <site_config.json> <sql>

Emits ``{"rows": [{col: value, ...}, ...]}`` on success, exits 1 on failure
with the mysql stderr.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> None:
    site_config_path, sql = sys.argv[1], sys.argv[2]
    with open(site_config_path) as f:
        cfg = json.load(f)
    env = {**os.environ, "MYSQL_PWD": cfg.get("db_password", "")}
    proc = subprocess.run(
        ["mysql", "-AD", cfg["db_name"], "-u" + cfg["db_name"], "-B", "-e", sql],
        capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(1)
    lines = proc.stdout.splitlines()
    if not lines:
        json.dump({"rows": []}, sys.stdout)
        return
    cols = lines[0].split("\t")
    rows = [dict(zip(cols, (_unescape(c) for c in ln.split("\t")))) for ln in lines[1:]]
    json.dump({"rows": rows}, sys.stdout)


# mysql -B (batch mode) escapes these sequences inside cell data; reverse them
# so row_data carries the original string. (#333)
_UNESCAPE_MAP = {"\\\\": "\\", "\\n": "\n", "\\r": "\r",
                 "\\t": "\t", "\\0": "\0", "\\Z": "\x1a"}


def _unescape(cell: str) -> str:
    out, i = [], 0
    while i < len(cell):
        if cell[i] == "\\" and i + 1 < len(cell):
            seq = cell[i:i + 2]
            out.append(_UNESCAPE_MAP.get(seq, seq))
            i += 2
        else:
            out.append(cell[i])
            i += 1
    return "".join(out)


if __name__ == "__main__":
    main()
