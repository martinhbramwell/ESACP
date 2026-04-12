#!/usr/bin/env python3
"""Create or update a Cloudflare DNS A record for a VM."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from tools.pipeline.stages.common.types import Config, Emit, TaskResult

CF_ZONE_ID_IRIDIUM = "631cd57fa246c8bc575bdc55bc0db70b"
CF_DNS_TTL = 120


def _get_cf_token(project_root: str) -> str:
    """Decrypt all.sops.yml and return the cloudflare_acme_token."""
    sops_file = Path(project_root) / "ansible" / "group_vars" / "all.sops.yml"
    dec = subprocess.run(
        ["sops", "-d", str(sops_file)],
        cwd=project_root, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        raise RuntimeError(f"sops decrypt failed: {dec.stderr.strip()}")
    data = yaml.safe_load(dec.stdout)
    token = data.get("cloudflare_acme_token", "")
    if not token:
        raise RuntimeError("cloudflare_acme_token not found in all.sops.yml")
    return token


def upsert_cloudflare_dns(config: Config, emit: Emit) -> TaskResult:
    """Create or update the DNS A record ``{hostname}.iridium.blue → wg_ip``."""
    hostname = config.hostname
    ip = config.wg_ip
    fqdn = f"{hostname}.iridium.blue"

    token = _get_cf_token(config.project_root)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    base_url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{CF_ZONE_ID_IRIDIUM}/dns_records"
    )

    # List existing records matching name
    list_url = f"{base_url}?type=A&name={fqdn}"
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            existing = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return TaskResult(
            False, False,
            f"Cloudflare list DNS failed: {exc.code} {exc.read().decode()}")

    records = existing.get("result", [])
    body = json.dumps({
        "type": "A", "name": fqdn, "content": ip,
        "ttl": CF_DNS_TTL, "proxied": False,
    }).encode()

    if records:
        existing_ip = records[0].get("content", "")
        if existing_ip == ip:
            return TaskResult(True, False,
                              f"DNS {fqdn} → {ip} already up to date")
        record_id = records[0]["id"]
        put_url = f"{base_url}/{record_id}"
        req = urllib.request.Request(
            put_url, data=body, headers=headers, method="PUT")
        action = "Updated"
    else:
        req = urllib.request.Request(
            base_url, data=body, headers=headers, method="POST")
        action = "Created"

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return TaskResult(
            False, False,
            f"Cloudflare DNS upsert failed: {exc.code} {exc.read().decode()}")

    if not result.get("success"):
        return TaskResult(
            False, False,
            f"Cloudflare DNS upsert failed: {result.get('errors')}")
    return TaskResult(
        True, True,
        f"{action} DNS A record: {fqdn} → {ip} (TTL {CF_DNS_TTL}s)")
