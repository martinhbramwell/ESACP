"""ESACP Control Plane API

FastAPI service running on saconsole (port 8088).
Provides read access to Docker, system info, Prometheus targets,
and stub VM lifecycle endpoints for the Cytoscape drill-down prototype.

All write/mutation operations (VM lifecycle) are stubs — they will be wired
to the appropriate hypervisor backend (KVM/libvirt, VBox, CloudStack) in Stage 2.x.
"""

import os
import socket
import uuid
from typing import Any

import docker
import docker.errors
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ESACP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_docker = docker.from_env()

# Prometheus base URL — reachable by container name within observability_network.
# Override via env var for testing outside Docker.
_PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

# In-memory job store (single-process; resets on container restart).
_jobs: dict[str, dict[str, Any]] = {}


# ── Helpers ────────────────────────────────────────────────────────────────

_SECRET_KEYS = {"password", "secret", "token", "key", "credential", "passwd", "auth"}


def _filter_env(env_list: list[str]) -> list[str]:
    """Redact environment variables whose name suggests a secret."""
    result = []
    for entry in env_list:
        name = entry.split("=", 1)[0].lower()
        if any(s in name for s in _SECRET_KEYS):
            result.append(f"{entry.split('=', 1)[0]}=***")
        else:
            result.append(entry)
    return result


def _port_list(c: docker.models.containers.Container) -> list[str]:
    ports = set()
    for bindings in (c.ports or {}).values():
        for p in (bindings or [{}]):
            val = p.get("HostPort") or p.get("PrivatePort")
            if val:
                ports.add(str(val))
    return sorted(ports)


def _container_summary(c: docker.models.containers.Container) -> dict:
    image = c.image.tags[0] if c.image.tags else c.attrs.get("Config", {}).get("Image", "")
    return {
        "id":     c.name,
        "name":   c.name,
        "image":  image,
        "status": c.status,
        "state":  c.attrs.get("State", {}).get("Status", c.status),
        "ports":  _port_list(c),
    }


def _container_detail(c: docker.models.containers.Container) -> dict:
    attrs    = c.attrs
    cfg      = attrs.get("Config", {})
    state    = attrs.get("State", {})
    host_cfg = attrs.get("HostConfig", {})

    networks = {
        name: {"ip": net.get("IPAddress"), "gateway": net.get("Gateway")}
        for name, net in attrs.get("NetworkSettings", {}).get("Networks", {}).items()
    }

    mounts = [
        {
            "source":      m.get("Source", ""),
            "destination": m.get("Destination", ""),
            "mode":        m.get("Mode", ""),
        }
        for m in attrs.get("Mounts", [])
        if not m.get("Source", "").startswith("/proc")
    ]

    return {
        **_container_summary(c),
        "created":        attrs.get("Created", "")[:19].replace("T", " "),
        "started":        state.get("StartedAt", "")[:19].replace("T", " "),
        "restart_policy": host_cfg.get("RestartPolicy", {}).get("Name", ""),
        "network_mode":   host_cfg.get("NetworkMode", ""),
        "networks":       networks,
        "mounts":         mounts,
        "env":            _filter_env(cfg.get("Env") or []),
        "cmd":            cfg.get("Cmd") or [],
    }


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "hostname": socket.gethostname()}


@app.get("/system/info")
def system_info():
    info = _docker.info()
    return {
        "hostname":           info.get("Name"),
        "os":                 info.get("OperatingSystem"),
        "kernel":             info.get("KernelVersion"),
        "architecture":       info.get("Architecture"),
        "docker_version":     info.get("ServerVersion"),
        "containers_running": info.get("ContainersRunning"),
        "containers_total":   info.get("Containers"),
        "images":             info.get("Images"),
    }


@app.get("/docker/containers")
def list_containers():
    return [_container_summary(c) for c in _docker.containers.list()]


@app.get("/docker/containers/{name}")
def get_container(name: str):
    try:
        return _container_detail(_docker.containers.get(name))
    except docker.errors.NotFound:
        raise HTTPException(404, detail=f"Container '{name}' not found")


@app.get("/docker/containers/{name}/logs")
def get_logs(name: str, tail: int = 100):
    try:
        c    = _docker.containers.get(name)
        text = c.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
        return {"container": name, "tail": tail, "logs": text.splitlines()}
    except docker.errors.NotFound:
        raise HTTPException(404, detail=f"Container '{name}' not found")


@app.get("/docker/networks")
def list_networks():
    running = {c.name: c for c in _docker.containers.list()}
    result  = []
    for net in _docker.networks.list():
        net.reload()
        members = [
            name for name in running
            if net.name in running[name].attrs.get("NetworkSettings", {}).get("Networks", {})
        ]
        result.append({
            "id":         net.short_id,
            "name":       net.name,
            "driver":     net.attrs.get("Driver"),
            "scope":      net.attrs.get("Scope"),
            "containers": members,
        })
    return result


@app.get("/prometheus/targets")
async def prometheus_targets():
    """Proxy to Prometheus /api/v1/targets. Avoids browser CORS issues."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{_PROMETHEUS}/api/v1/targets", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise HTTPException(502, detail=f"Prometheus unreachable: {exc}")


# ── VM lifecycle stubs — wired to hypervisor in Stage 2.x ─────────────────

@app.get("/vm/status")
def vm_status():
    return {"status": "stub", "message": "VM lifecycle not yet wired to hypervisor"}


@app.post("/vm/{vm}/snapshot")
def vm_snapshot(vm: str, name: str = ""):
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "stub", "vm": vm, "op": "snapshot", "name": name}
    return {"job_id": job_id}


@app.post("/vm/{vm}/revert")
def vm_revert(vm: str, snapshot: str = ""):
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "stub", "vm": vm, "op": "revert", "snapshot": snapshot}
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(404, detail=f"Job '{job_id}' not found")
    return _jobs[job_id]
