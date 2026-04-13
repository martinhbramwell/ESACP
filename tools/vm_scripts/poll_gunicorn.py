#!/usr/bin/env python3
"""Poll gunicorn /api/method/ping until it responds or timeout.

Usage:
    python3 poll_gunicorn.py --url URL [--timeout 120] [--interval 2]

Exit codes: 0 = responding, 1 = timeout.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request


def poll(url: str, timeout: int, interval: int) -> bool:
    """Return True when gunicorn responds, False on timeout."""
    elapsed = 0
    while elapsed < timeout:
        try:
            urllib.request.urlopen(url, timeout=5)
            print(f"  [OK] gunicorn responding after {elapsed}s")
            return True
        except Exception:
            pass
        time.sleep(interval)
        elapsed += interval
        if elapsed % 10 == 0:
            print(f"  Waiting for gunicorn... ({elapsed}s elapsed)")
    print(f"  [FAIL] gunicorn did not respond within {timeout}s")
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Poll gunicorn readiness")
    ap.add_argument("--url", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--interval", type=int, default=2)
    args = ap.parse_args()
    sys.exit(0 if poll(args.url, args.timeout, args.interval) else 1)


if __name__ == "__main__":
    main()
