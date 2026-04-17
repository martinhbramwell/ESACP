"""Environment helpers — shared across all subcommands."""

import getpass
import os
import sys
from pathlib import Path


def env(key, fallback=None):
    """Read an environment variable; abort if required and missing."""
    val = os.environ.get(key, fallback)
    if val is None:
        print(f"[FAIL] Required env var {key} is not set")
        sys.exit(1)
    return val


def bench_dir():
    return env("TARGET_BENCH", os.path.expanduser("~/frappe-bench"))


def user_home():
    """Derive home dir from TARGET_BENCH (immune to sudo HOME pollution)."""
    bd = bench_dir()
    return str(Path(bd).parent)


def site_url():
    return env("ERPNEXT_SITE_URL")


def erp_user():
    return getpass.getuser()
