#!/usr/bin/env python3
"""Acceptance tests for Phase 2 host-registration primitives (#190).

Hits a live uvicorn (uvicorn tools.api:app --port 8088 --reload) via stdlib
urllib — no httpx dependency. All four cases exercise error paths that
reject BEFORE any hosts_map.yml write, so the repo's live configuration
stays untouched.

Exit 0 on full pass, 1 on any failure.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8088"


def post(path: str, payload: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


failures: list[str] = []


def expect(case: str, status_got: int, body_got: str, status: int, needle: str) -> None:
    ok = status_got == status and needle in body_got
    mark = "✅" if ok else "❌"
    print(f"  {mark}  {case}: got {status_got}, body={body_got[:160]}")
    if not ok:
        failures.append(f"{case} — expected {status} containing {needle!r}")


print("── Phase 2 acceptance: host-registration primitives ──")

# 1. Invalid hostname → 400
s, b = post("/api/hosts/add", {
    "hostname": "BadName", "virbr0_ip": "192.168.122.99", "wg_ip": "10.10.0.99",
})
expect("invalid hostname (regex)", s, b, 400, "lowercase letters")

# 2. Duplicate hostname → 409
s, b = post("/api/hosts/add", {
    "hostname": "dev01", "virbr0_ip": "192.168.122.99", "wg_ip": "10.10.0.99",
})
expect("duplicate hostname", s, b, 409, "already exists")

# 3. Duplicate virbr0 IP → 409
s, b = post("/api/hosts/add", {
    "hostname": "newvm99", "virbr0_ip": "192.168.122.21", "wg_ip": "10.10.0.99",
})
expect("duplicate virbr0 IP", s, b, 409, "virbr0 IP 192.168.122.21")

# 4. Duplicate WireGuard IP → 409
s, b = post("/api/hosts/add", {
    "hostname": "newvm99", "virbr0_ip": "192.168.122.99", "wg_ip": "10.10.0.13",
})
expect("duplicate WireGuard IP", s, b, 409, "WireGuard IP 10.10.0.13")

print()
if failures:
    print(f"FAIL — {len(failures)} test(s) failed:")
    for f in failures:
        print(f"  • {f}")
    sys.exit(1)
print("PASS — all 4 acceptance tests OK.")
