"""ESACP Control Plane API

FastAPI service running on saconsole (port 8088).
Provides read access to Docker, system info, Prometheus targets,
and stub VM lifecycle endpoints for the Cytoscape drill-down prototype.

Docker access: httpx over the Unix socket (/var/run/docker.sock).
This avoids the docker-py SDK and its urllib3 compatibility issues entirely.

All write/mutation operations (VM lifecycle) are stubs — they will be wired
to the appropriate hypervisor backend (KVM/libvirt, VBox, CloudStack) in Stage 2.x.
"""

import os
import socket
import uuid
from typing import Any

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

# Prometheus base URL — reachable by container name within observability_network.
_PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

# Docker socket transport — shared across requests.
_docker_transport = httpx.HTTPTransport(uds="/var/run/docker.sock")

# In-memory job store (single-process; resets on container restart).
_jobs: dict[str, dict[str, Any]] = {}


# ── Docker socket helper ───────────────────────────────────────────────────

async def _docker_get(path: str) -> Any:
    """GET from the Docker daemon REST API via Unix socket."""
    async with httpx.AsyncClient(
        transport=httpx.AsyncHTTPTransport(uds="/var/run/docker.sock"),
        base_url="http://localhost",
    ) as client:
        resp = await client.get(path)
        resp.raise_for_status()
        return resp.json()


# ── Data helpers ───────────────────────────────────────────────────────────

_SECRET_KEYS = {"password", "secret", "token", "key", "credential", "passwd", "auth"}


def _filter_env(env_list: list[str]) -> list[str]:
    result = []
    for entry in env_list:
        name = entry.split("=", 1)[0].lower()
        if any(s in name for s in _SECRET_KEYS):
            result.append(f"{entry.split('=', 1)[0]}=***")
        else:
            result.append(entry)
    return result


def _port_list(ports) -> list[str]:
    """Handle both list format (container list) and dict format (inspect)."""
    result = set()
    if isinstance(ports, list):
        # GET /containers/json: [{"PublicPort": 3000, "PrivatePort": 3000, ...}]
        for p in ports:
            val = p.get("PublicPort") or p.get("PrivatePort")
            if val:
                result.add(str(val))
    elif isinstance(ports, dict):
        # GET /containers/{id}/json NetworkSettings.Ports: {"3000/tcp": [{"HostPort": "3000"}]}
        for bindings in ports.values():
            for p in (bindings or []):
                val = (p or {}).get("HostPort") or (p or {}).get("PrivatePort")
                if val:
                    result.add(str(val))
    return sorted(result)


def _container_summary(c: dict) -> dict:
    image = (c.get("Image") or "").split("sha256:")[0] or "unknown"
    ports = _port_list(c.get("Ports", {}))
    name  = (c.get("Names") or ["unknown"])[0].lstrip("/")
    return {
        "id":     name,
        "name":   name,
        "image":  image,
        "status": c.get("Status", ""),
        "state":  c.get("State", ""),
        "ports":  ports,
    }


def _container_detail(c: dict) -> dict:
    cfg      = c.get("Config", {})
    state    = c.get("State", {})
    host_cfg = c.get("HostConfig", {})
    name     = c.get("Name", "").lstrip("/")

    networks = {
        n: {"ip": v.get("IPAddress"), "gateway": v.get("Gateway")}
        for n, v in c.get("NetworkSettings", {}).get("Networks", {}).items()
    }

    mounts = [
        {
            "source":      m.get("Source", ""),
            "destination": m.get("Destination", ""),
            "mode":        m.get("Mode", ""),
        }
        for m in c.get("Mounts", [])
        if not m.get("Source", "").startswith("/proc")
    ]

    ports = _port_list(c.get("NetworkSettings", {}).get("Ports", {}))

    return {
        "id":             name,
        "name":           name,
        "image":          cfg.get("Image", ""),
        "status":         state.get("Status", ""),
        "state":          state.get("Status", ""),
        "ports":          ports,
        "created":        c.get("Created", "")[:19].replace("T", " "),
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
async def system_info():
    info = await _docker_get("/info")
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
async def list_containers():
    containers = await _docker_get("/containers/json")
    return [_container_summary(c) for c in containers]


@app.get("/docker/containers/{name}")
async def get_container(name: str):
    try:
        c = await _docker_get(f"/containers/{name}/json")
        return _container_detail(c)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(404, detail=f"Container '{name}' not found")
        raise


@app.get("/docker/containers/{name}/logs")
async def get_logs(name: str, tail: int = 100):
    try:
        async with httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds="/var/run/docker.sock"),
            base_url="http://localhost",
        ) as client:
            resp = await client.get(
                f"/containers/{name}/logs",
                params={"stdout": 1, "stderr": 1, "timestamps": 1, "tail": tail},
            )
            resp.raise_for_status()
            # Docker log stream uses 8-byte frame headers — strip them
            raw  = resp.content
            lines = []
            i = 0
            while i + 8 <= len(raw):
                size = int.from_bytes(raw[i+4:i+8], "big")
                if i + 8 + size > len(raw):
                    break
                lines.append(raw[i+8:i+8+size].decode("utf-8", errors="replace").rstrip())
                i += 8 + size
            return {"container": name, "tail": tail, "logs": lines}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(404, detail=f"Container '{name}' not found")
        raise


@app.get("/docker/networks")
async def list_networks():
    networks   = await _docker_get("/networks")
    containers = await _docker_get("/containers/json")
    running    = {(c.get("Names") or ["?"])[0].lstrip("/"): c for c in containers}

    result = []
    for net in networks:
        members = [
            name for name, c in running.items()
            if net["Name"] in (c.get("NetworkSettings") or {}).get("Networks", {})
        ]
        result.append({
            "id":         net.get("Id", "")[:12],
            "name":       net.get("Name"),
            "driver":     net.get("Driver"),
            "scope":      net.get("Scope"),
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
