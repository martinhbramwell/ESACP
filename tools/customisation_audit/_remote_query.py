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
    rows = [dict(zip(cols, ln.split("\t"))) for ln in lines[1:]]
    json.dump({"rows": rows}, sys.stdout)


if __name__ == "__main__":
    main()
