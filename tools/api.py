"""ESACP Control Plane API — prototype

Runs on localhost:8088. Proxied from Vite dev server at /api.

Start (from project root):
    uvicorn tools.api:app --port 8088 --reload

Endpoints:
    GET  /api/hosts                  → current KVM hosts + IP suggestions + erp_user/erp_url
    POST /api/hosts/add              → add host to hosts_map.yml, regen inventory
    POST /api/provision/erpnext      → template-based deploy via macro/provision.py (stages 1–9)
    POST /api/provision/erpnext-generic → generic deploy (no prod data) + wizard completion
    GET  /api/wizard/recordings      → list available Playwright wizard recordings
    GET  /api/wizard/backups         → list available golden backup files
    POST /api/refresh/{hostname}     → re-run stages 3–9 via macro/refresh.py (idempotent)
    POST /api/destroy/{hostname}     → full teardown: WG + VM + hosts_map + keys + inventory
    GET  /api/health/{hostname}      → quick SSH check: { web, app, db } each green/amber/red
    GET  /api/template/status        → metadata for latest undifferentiated ERPNext image
    POST /api/build/template         → start background Packer build on hub
    DELETE /api/template             → delete template artifact from toshiba
    POST /api/promote                → staging → production promotion (stub)
    POST /api/vm/{hostname}/start    → start a shut-off VM (memory guard)
    POST /api/vm/{hostname}/stop     → graceful shutdown
    POST /api/vm/{hostname}/reboot   → reboot a running VM
    GET  /api/jobs                   → list all jobs (page-refresh reconnect)
    GET  /api/jobs/{job_id}          → poll job status + log lines
"""

from datetime import datetime, timezone
import json
import re
import subprocess
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


from tools.host_identity import (
    DEFAULT_HYPERVISOR, ZONE_DOMAINS, virbr0_subnet_prefix,
)
from tools.secrets import load_build_secrets

PROJECT_ROOT        = Path(__file__).parent.parent
PLATFORMS_KVM       = PROJECT_ROOT / "platforms" / "kvm"
HOSTS_MAP           = PROJECT_ROOT / "hosts_map.yml"
GROUP_VARS_ALL      = PROJECT_ROOT / "ansible" / "group_vars" / "all.yml"
KEYS_SOPS           = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"


# Hypervisor paths (accessed over SSH)
HYPERVISOR_ALIAS     = DEFAULT_HYPERVISOR
HYPERVISOR_USER      = "hasan"
# Template qcow2 lives in the esacp libvirt pool (vol-clone, no sudo needed).
# Metadata JSON lives in hasan's home dir (writable without sudo).
HYPERVISOR_METADATA_DIR = f"/home/{HYPERVISOR_USER}/esacp-packer-output"

app = FastAPI(title="ESACP Control Plane API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Job tracking (file-based, survives uvicorn restarts — GH #37) ────────────

JOB_DIR = Path("/tmp")


def _job_meta_path(job_id: str) -> Path:
    return JOB_DIR / f"esacp-job-{job_id}.meta"


def _job_log_path(job_id: str) -> Path:
    return JOB_DIR / f"esacp-job-{job_id}.log"


def _job_status_path(job_id: str) -> Path:
    return JOB_DIR / f"esacp-job-{job_id}.status"


def _spawn_job(job_type: str, job_id: str, args: dict, hostname: str, job_type_label: str | None = None) -> None:
    """Spawn an independent worker process for a job.

    The child process writes to /tmp/esacp-job-{id}.log (stdout) and
    /tmp/esacp-job-{id}.status (on completion). It survives uvicorn restarts.
    """
    meta = {
        "hostname": hostname,
        "type": job_type_label or job_type,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _job_meta_path(job_id).write_text(json.dumps(meta))

    log_file = open(_job_log_path(job_id), "w")
    subprocess.Popen(
        [
            "python3", "tools/job_worker.py",
            job_type, job_id, json.dumps(args),
        ],
        cwd=PROJECT_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # fully detached from uvicorn
    )


def _read_job(job_id: str) -> dict | None:
    """Read job state from disk. Returns None if job doesn't exist."""
    meta_path = _job_meta_path(job_id)
    if not meta_path.exists():
        return None

    meta = json.loads(meta_path.read_text())

    log_path = _job_log_path(job_id)
    log_lines = log_path.read_text().splitlines() if log_path.exists() else []

    status_path = _job_status_path(job_id)
    if status_path.exists():
        status = status_path.read_text().strip()
    else:
        status = "running"

    return {
        "status": status,
        "log": log_lines,
        "hostname": meta.get("hostname", ""),
        "type": meta.get("type", ""),
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_hosts_map() -> dict:
    with open(HOSTS_MAP) as f:
        return yaml.safe_load(f)


def _last_octet(ip: str) -> int:
    try:
        return int(ip.split(".")[-1])
    except (ValueError, IndexError):
        return 0


# ── GET /api/hosts ────────────────────────────────────────────────────────────

def _query_provisioned(hypervisor: str | None) -> dict[str, dict] | None:
    """Return a dict mapping VM name → {provisioned, vm_state}, or None if unreachable.

    provisioned=True  → VM has a 'Baseline' snapshot (Ansible completed)
    provisioned=False → VM exists but has no 'Baseline' snapshot (in-flight or partial)
    vm_state          → libvirt domain state string (e.g. 'running', 'shut off')

    One SSH call per hypervisor; the remote shell loops over all VMs.
    """
    script = (
        "for vm in $(virsh --connect qemu:///system list --all --name | grep -v '^$'); do "
        "  state=$(virsh --connect qemu:///system domstate $vm 2>/dev/null | head -1); "
        "  if virsh --connect qemu:///system snapshot-list $vm --name 2>/dev/null "
        "     | grep -qi 'baseline'; then "
        "    echo \"provisioned:$state:$vm\"; "
        "  else "
        "    echo \"exists:$state:$vm\"; "
        "  fi; "
        "done"
    )
    try:
        if hypervisor:
            cmd = ["ssh", hypervisor, script]
        else:
            cmd = ["bash", "-c", script]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            result = {}
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("provisioned:"):
                    rest = line[len("provisioned:"):]
                    state, name = rest.split(":", 1)
                    result[name] = {"provisioned": True, "vm_state": state}
                elif line.startswith("exists:"):
                    rest = line[len("exists:"):]
                    state, name = rest.split(":", 1)
                    result[name] = {"provisioned": False, "vm_state": state}
            return result
    except Exception:
        pass
    return None


@app.get("/api/hosts")
def get_hosts():
    """Return current KVM hosts and suggested next-available IPs.

    provisioned=True  → VM has 'Baseline' snapshot (Ansible-provisioned)
    provisioned=False → in hosts_map.yml but VM not found on hypervisor
    provisioned=None  → hypervisor unreachable, state unknown
    """
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})

    # Read global erp_user once
    try:
        with open(GROUP_VARS_ALL) as _f:
            _erp_user = yaml.safe_load(_f).get("erp_user", "erpadm")
    except Exception:
        _erp_user = "erpadm"

    # Batch: one SSH call per unique hypervisor
    vm_cache: dict[str | None, dict[str, bool] | None] = {}
    for h in kvm.values():
        hv = h.get("hypervisor") or None
        if hv not in vm_cache:
            vm_cache[hv] = _query_provisioned(hv)

    hosts            = []
    wg_octets        = []
    virbr0_octets    = []

    for name, h in kvm.items():
        hv      = h.get("hypervisor") or None
        vm_map  = vm_cache.get(hv)
        if vm_map is None:
            provisioned = None          # hypervisor unreachable
            vm_state    = None
        elif name in vm_map:
            provisioned = vm_map[name]["provisioned"]
            vm_state    = vm_map[name]["vm_state"]
        else:
            provisioned = False         # not yet created
            vm_state    = None

        # Derive zone key from ansible_groups for erp_url
        groups   = h.get("ansible_groups", [])
        if "production" in groups:
            zone_key = "production"
        elif "staging" in groups:
            zone_key = "staging"
        else:
            zone_key = "development"
        hostname = h.get("hostname", name)
        wg_role  = h.get("wg_role", "spoke")
        domain   = ZONE_DOMAINS[zone_key]
        erp_url  = f"https://{hostname}.{domain}" if wg_role == "spoke" else ""

        hosts.append({
            "id":            name,
            "hostname":      hostname,
            "nickname":      h.get("nickname", ""),
            "virbr0_ip":     h.get("virbr0_ip", ""),
            "wg_ip":         h.get("wg_ip", ""),
            "wg_role":       wg_role,
            "backend":       h.get("backend", "kvm"),
            "hypervisor":    hv or "",
            "provisioned":   provisioned,
            "vm_state":      vm_state,
            "ansible_groups": groups,
            "vm_role":       h.get("vm_role", "dev"),
            "erp_user":      _erp_user,
            "erp_url":       erp_url,
        })
        wg = h.get("wg_ip", "")
        if wg:
            wg_octets.append(_last_octet(wg))
        vbr = h.get("virbr0_ip", "")
        if vbr:
            virbr0_octets.append(_last_octet(vbr))

    next_wg  = max(wg_octets,     default=0) + 1
    next_vbr = max(virbr0_octets, default=9) + 1

    # Default hypervisor for new hosts: match the most common one in the current fleet
    hypervisors = [h.get("hypervisor") for h in kvm.values() if h.get("hypervisor")]
    default_hv  = max(set(hypervisors), key=hypervisors.count) if hypervisors else DEFAULT_HYPERVISOR

    return {
        "hosts": hosts,
        "suggestions": {
            "wg_ip":      f"10.10.0.{next_wg}",
            "virbr0_ip":  f"{virbr0_subnet_prefix()}.{next_vbr}",
            "hypervisor": default_hv,
        },
    }


# ── POST /api/hosts/add ───────────────────────────────────────────────────────

_ZONE_GROUPS: dict[str, list[str]] = {
    "development": ["kvm", "targets", "development", "lab"],
    "staging":     ["kvm", "targets", "staging",     "lab"],
    "production":  ["kvm", "targets", "production"],
}


class NewHost(BaseModel):
    hostname:   str
    nickname:   str = ""
    virbr0_ip:  str
    wg_ip:      str
    backend:    str = "kvm"
    hypervisor: str = DEFAULT_HYPERVISOR
    zone:       str = "development"   # development | staging | production
    vm_role:    str = "dev"           # dev | master | slave


@app.post("/api/hosts/add")
def add_host(host: NewHost):
    """Append a new KVM host to hosts_map.yml and regenerate Ansible inventory."""
    if not re.match(r'^[a-z][a-z0-9-]*$', host.hostname):
        raise HTTPException(400, "hostname: lowercase letters/digits/hyphens, must start with a letter")

    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})

    if host.hostname in kvm:
        raise HTTPException(409, f"'{host.hostname}' already exists in the kvm group")

    for name, h in kvm.items():
        if h.get("wg_ip") == host.wg_ip:
            raise HTTPException(409, f"WireGuard IP {host.wg_ip} already used by '{name}'")
        if h.get("virbr0_ip") == host.virbr0_ip:
            raise HTTPException(409, f"virbr0 IP {host.virbr0_ip} already used by '{name}'")

    nickname = host.nickname or host.hostname[:4]
    groups   = _ZONE_GROUPS.get(host.zone, _ZONE_GROUPS["development"])
    groups_yaml = "\n".join(f"        - {g}" for g in groups)
    role_line = f"      vm_role: {host.vm_role}\n" if host.vm_role and host.vm_role != "dev" else ""

    # Build the YAML block, matching existing file indentation (4-space host key, 6-space fields)
    block = (
        f"\n    {host.hostname}:\n"
        f"      hostname: {host.hostname}\n"
        f"      nickname: {nickname}\n"
        f'      virbr0_ip: "{host.virbr0_ip}"\n'
        f'      wg_ip: "{host.wg_ip}"\n'
        f"      wg_role: spoke\n"
        f"      ansible_managed: true\n"
        f"      backend: {host.backend}\n"
        f"      hypervisor: {host.hypervisor}\n"
        f"{role_line}"
        f"      ansible_groups:\n"
        f"{groups_yaml}\n"
    )

    text   = HOSTS_MAP.read_text()
    marker = "  # ── VirtualBox guests"
    if marker not in text:
        raise HTTPException(500, "Cannot find insertion point in hosts_map.yml — expected '  # ── VirtualBox guests' section")

    HOSTS_MAP.write_text(text.replace(marker, block + marker))

    result = subprocess.run(
        ["python3", "tools/generate_inventory.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(500, f"generate_inventory.py failed:\n{result.stderr}")

    return {"ok": True, "hostname": host.hostname}


# ── GET /api/template/status ─────────────────────────────────────────────────

@app.get("/api/template/status")
def get_template_status():
    """Return metadata for the latest undifferentiated ERPNext image on toshiba.

    Reads /mnt/esacp-disk/packer-output/erpnext-v13-latest.json over SSH.
    Returns { image, built_at, frappe_branch, erpnext_branch, state } if built,
    or { image: null, state: "not_built" } if no build has been run yet.
    """
    try:
        r = subprocess.run(
            ["ssh", HYPERVISOR_ALIAS,
             f"cat {HYPERVISOR_METADATA_DIR}/erpnext-v13-latest.json 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return {"image": None, "built_at": None, "state": "not_built"}


# ── DELETE /api/template ─────────────────────────────────────────────────────

@app.delete("/api/template")
def delete_template():
    """Delete the undifferentiated ERPNext image artifact from toshiba.

    Removes the qcow2, the latest symlink, and the metadata JSON from
    /mnt/esacp-disk/packer-output/ on toshiba. Resets state to 'not_built'.
    """
    try:
        # Read metadata to find the volume name, then delete from esacp pool
        meta_r = subprocess.run(
            ["ssh", HYPERVISOR_ALIAS,
             f"cat {HYPERVISOR_METADATA_DIR}/erpnext-v13-latest.json 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if meta_r.returncode == 0 and meta_r.stdout.strip():
            meta = json.loads(meta_r.stdout)
            image = meta.get("image")
            if image:
                subprocess.run(
                    ["ssh", HYPERVISOR_ALIAS,
                     f"virsh --connect qemu:///system vol-delete --pool esacp '{image}' 2>/dev/null || true"],
                    capture_output=True, text=True, timeout=30,
                )
        # Remove metadata regardless
        r = subprocess.run(
            ["ssh", HYPERVISOR_ALIAS,
             f"rm -f {HYPERVISOR_METADATA_DIR}/erpnext-v13-latest.json"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            raise HTTPException(500, f"Failed to delete template metadata: {r.stderr.strip()}")
        return {"ok": True, "message": "Template artifact deleted — state reset to not_built"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ── POST /api/build/template ──────────────────────────────────────────────────

@app.post("/api/build/template")
def start_build_template():
    """Start a background job to build the undifferentiated ERPNext v13 image.

    Runs platforms/packer/build.sh on the hub via SSH.
    The hub creates the build VM on toshiba, runs Packer provisioners,
    exports the qcow2, then destroys the build VM.
    Only one build may run at a time.
    """
    # Check for already-running build by scanning active job files
    for meta_file in JOB_DIR.glob("esacp-job-*.meta"):
        jid = meta_file.stem.replace("esacp-job-", "")
        j = _read_job(jid)
        if j and j.get("type") == "build_template" and j["status"] == "running":
            raise HTTPException(409, "A template build is already in progress")

    job_id = str(uuid.uuid4())[:8]
    _spawn_job("build_template", job_id, {}, hostname="template")
    return {"job_id": job_id}


# ── POST /api/promote ────────────────────────────────────────────────────────

@app.post("/api/promote")
def promote_staging():
    """Stub: initiate Staging → Production promotion.

    Full implementation: validate staging state, send Telegram approval request
    to configured approvers, await 2 confirmations, then execute DNS flip via
    Cloudflare API and swap quadrant labels. Deferred pending v13 staging.
    """
    return {"ok": True, "message": "Promotion initiated — awaiting Telegram approval (stub; DNS flip not yet implemented)"}


# ── POST /api/provision/erpnext ──────────────────────────────────────────────


class NewErpnextVM(BaseModel):
    hostname:   str
    nickname:   str  = ""   # Frappe bench suffix: frappe-bench-{nickname}
    virbr0_ip:  str
    wg_ip:      str
    hypervisor: str  = DEFAULT_HYPERVISOR
    zone:       str  = "development"
    vm_role:    str  = "dev:unspecified"


@app.post("/api/provision/erpnext")
def start_provision_erpnext(vm: NewErpnextVM):
    """Register a new VM and start a template-based provisioning job.

    Unlike /api/provision/{hostname}, this endpoint both registers the host
    AND starts the job atomically — the caller gets back a job_id immediately
    and polls /api/jobs/{job_id} for progress.

    The provisioning job does:
      1.  Add WireGuard peer
      2.  Build cloud-config seed ISO (hostname + IP + controller SSH key)
      3.  SCP seed ISO to hypervisor
      4.  virsh vol-clone the undifferentiated template qcow2
      5.  virt-install --import (boots in seconds, cloud-init sets identity)
      6.  Wait for SSH
      7.  Take "Baseline" snapshot → node shows provisioned=True in UI
      8.  Ansible wireguard role on hub (update hub wg0.conf)
      Differentiation (steps 9–18):
      9.  Ansible wireguard role on new VM (configure spoke wg0)
      10. Push envars.sh → /opt/ce_sri/envars.sh
      11. bench new-site + install-app erpnext
      12. rsync ce_sri + returnable + route_planner + BaRe + BKP
      13. BaRe/envars.sh symlink → /opt/ce_sri/envars.sh
      14. Place ddlViews.sql
      15. installApps.sh (pip install bespoke apps + migrate)
      16. handleRestore.sh (DB restore + views)
      17. bench restart
      18. Snapshot "ERPNext v13 Logichem DB Restored"
      8. Ansible wireguard role on hub (add new spoke)
    """
    if not re.match(r'^[a-z][a-z0-9-]*$', vm.hostname):
        raise HTTPException(400, "hostname: lowercase letters/digits/hyphens, must start with a letter")

    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})

    already_registered = vm.hostname in kvm
    needs_cleanup = False
    if already_registered:
        # Host is in hosts_map — check whether it's actually provisioned on the hypervisor.
        # If provisioned (Baseline snapshot exists), reject. Otherwise clean up residue and rebuild.
        host_cfg   = kvm[vm.hostname]
        hypervisor = host_cfg.get("hypervisor")
        vm_map     = _query_provisioned(hypervisor)
        vm_info    = vm_map.get(vm.hostname, {}) if vm_map else {}
        if vm_info.get("provisioned") is True:
            raise HTTPException(409, f"'{vm.hostname}' is already provisioned — Destroy it first")
        # Flag cleanup for the job thread — any leftover VM/storage will be
        # removed before vol-clone so we don't hit disk pool collisions.
        if vm_map is not None and vm.hostname in vm_map and not vm_info.get("provisioned"):
            needs_cleanup = True
    else:
        # New host — check for IP collisions
        for name, h in kvm.items():
            if h.get("wg_ip") == vm.wg_ip:
                raise HTTPException(409, f"WireGuard IP {vm.wg_ip} already used by '{name}'")
            if h.get("virbr0_ip") == vm.virbr0_ip:
                raise HTTPException(409, f"virbr0 IP {vm.virbr0_ip} already used by '{name}'")

        # Register in hosts_map.yml so the UI can add the node
        nickname  = vm.nickname or vm.hostname[:4]
        groups    = _ZONE_GROUPS.get(vm.zone, _ZONE_GROUPS["development"])
        role_line = f"      vm_role: {vm.vm_role}\n" if vm.vm_role and vm.vm_role != "dev" else ""
        block = (
            f"\n    {vm.hostname}:\n"
            f"      hostname: {vm.hostname}\n"
            f"      nickname: {nickname}\n"
            f'      virbr0_ip: "{vm.virbr0_ip}"\n'
            f'      wg_ip: "{vm.wg_ip}"\n'
            f"      wg_role: spoke\n"
            f"      ansible_managed: true\n"
            f"      backend: {vm.hypervisor and 'kvm' or 'kvm'}\n"
            f"      hypervisor: {vm.hypervisor}\n"
            f"{role_line}"
            f"      ansible_groups:\n"
            + "\n".join(f"        - {g}" for g in groups) + "\n"
        )
        text   = HOSTS_MAP.read_text()
        marker = "  # ── VirtualBox guests"
        if marker not in text:
            raise HTTPException(500, "Cannot find insertion point in hosts_map.yml")
        HOSTS_MAP.write_text(text.replace(marker, block + marker))

        result = subprocess.run(
            ["python3", "tools/generate_inventory.py"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise HTTPException(500, f"generate_inventory.py failed:\n{result.stderr}")

    job_id = str(uuid.uuid4())[:8]
    cleanup_cfg = kvm.get(vm.hostname) if needs_cleanup else None

    _spawn_job("provision", job_id, {
        "hostname": vm.hostname,
        "virbr0_ip": vm.virbr0_ip,
        "cleanup_cfg": cleanup_cfg,
    }, hostname=vm.hostname, job_type_label="provision_erpnext")

    return {"job_id": job_id, "hostname": vm.hostname}


# ── POST /api/provision/erpnext-generic ─────────────────────────────────────


class NewGenericErpnextVM(BaseModel):
    hostname:    str
    nickname:    str  = ""
    virbr0_ip:   str
    wg_ip:       str
    hypervisor:  str  = DEFAULT_HYPERVISOR
    zone:        str  = "development"
    vm_role:     str  = "dev:unspecified"
    wizard_mode: str  = "record"   # "record" | "replay" | "existing"
    wizard_arg:  str  = ""         # recording script name or backup filename


@app.post("/api/provision/erpnext-generic")
def start_provision_erpnext_generic(vm: NewGenericErpnextVM):
    """Register a new VM and provision a generic ERPNext (no production data).

    Same host registration as /api/provision/erpnext, but uses the generic
    pipeline (provision_mode="generic"). After stages 1-9, the wizard_mode
    determines how the setup wizard is completed.
    """
    if not re.match(r'^[a-z][a-z0-9-]*$', vm.hostname):
        raise HTTPException(400, "hostname: lowercase letters/digits/hyphens, must start with a letter")
    if vm.wizard_mode not in ("record", "replay", "existing"):
        raise HTTPException(400, f"wizard_mode must be record, replay, or existing (got '{vm.wizard_mode}')")
    if vm.wizard_mode == "replay" and not vm.wizard_arg:
        raise HTTPException(400, "wizard_mode=replay requires wizard_arg (recording script name)")
    if vm.wizard_mode == "existing" and not vm.wizard_arg:
        raise HTTPException(400, "wizard_mode=existing requires wizard_arg (backup filename)")

    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})

    already_registered = vm.hostname in kvm
    needs_cleanup = False
    if already_registered:
        host_cfg   = kvm[vm.hostname]
        hypervisor = host_cfg.get("hypervisor")
        vm_map     = _query_provisioned(hypervisor)
        vm_info    = vm_map.get(vm.hostname, {}) if vm_map else {}
        if vm_info.get("provisioned") is True:
            raise HTTPException(409, f"'{vm.hostname}' is already provisioned — Destroy it first")
        if vm_map is not None and vm.hostname in vm_map and not vm_info.get("provisioned"):
            needs_cleanup = True
    else:
        for name, h in kvm.items():
            if h.get("wg_ip") == vm.wg_ip:
                raise HTTPException(409, f"WireGuard IP {vm.wg_ip} already used by '{name}'")
            if h.get("virbr0_ip") == vm.virbr0_ip:
                raise HTTPException(409, f"virbr0 IP {vm.virbr0_ip} already used by '{name}'")

        nickname  = vm.nickname or vm.hostname[:4]
        groups    = _ZONE_GROUPS.get(vm.zone, _ZONE_GROUPS["development"])
        role_line = f"      vm_role: {vm.vm_role}\n" if vm.vm_role and vm.vm_role != "dev" else ""
        block = (
            f"\n    {vm.hostname}:\n"
            f"      hostname: {vm.hostname}\n"
            f"      nickname: {nickname}\n"
            f'      virbr0_ip: "{vm.virbr0_ip}"\n'
            f'      wg_ip: "{vm.wg_ip}"\n'
            f"      wg_role: spoke\n"
            f"      ansible_managed: true\n"
            f"      backend: kvm\n"
            f"      hypervisor: {vm.hypervisor}\n"
            f"{role_line}"
            f"      ansible_groups:\n"
            + "\n".join(f"        - {g}" for g in groups) + "\n"
        )
        text   = HOSTS_MAP.read_text()
        marker = "  # ── VirtualBox guests"
        if marker not in text:
            raise HTTPException(500, "Cannot find insertion point in hosts_map.yml")
        HOSTS_MAP.write_text(text.replace(marker, block + marker))

        result = subprocess.run(
            ["python3", "tools/generate_inventory.py"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise HTTPException(500, f"generate_inventory.py failed:\n{result.stderr}")

    job_id = str(uuid.uuid4())[:8]
    cleanup_cfg = kvm.get(vm.hostname) if needs_cleanup else None

    _spawn_job("provision_generic", job_id, {
        "hostname": vm.hostname,
        "virbr0_ip": vm.virbr0_ip,
        "zone": vm.zone,
        "cleanup_cfg": cleanup_cfg,
        "wizard_mode": vm.wizard_mode,
        "wizard_arg": vm.wizard_arg,
    }, hostname=vm.hostname, job_type_label="provision_generic")

    return {"job_id": job_id, "hostname": vm.hostname}


# ── GET /api/wizard/recordings ─────────────────────────────────────────────

RECORDINGS_DIR = PROJECT_ROOT / "prototypes" / "cytoscape" / "recordings" / "wizard"


@app.get("/api/wizard/recordings")
def list_wizard_recordings():
    """List available Playwright wizard recordings."""
    if not RECORDINGS_DIR.exists():
        return {"recordings": []}
    recordings = []
    for f in sorted(RECORDINGS_DIR.glob("*.spec.js"), reverse=True):
        stat = f.stat()
        recordings.append({
            "name": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "created_at": datetime.fromtimestamp(
                stat.st_ctime, tz=timezone.utc,
            ).isoformat(),
        })
    return {"recordings": recordings}


# ── GET /api/wizard/backups ────────────────────────────────────────────────

GOLDEN_BACKUPS_DIR = PROJECT_ROOT / "platforms" / "kvm" / "golden_backups"


@app.get("/api/wizard/backups")
def list_wizard_backups():
    """List available golden backup files."""
    if not GOLDEN_BACKUPS_DIR.exists():
        return {"backups": []}
    backups = []
    for f in sorted(GOLDEN_BACKUPS_DIR.glob("*.tgz"), reverse=True):
        stat = f.stat()
        backups.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 1),
            "created_at": datetime.fromtimestamp(
                stat.st_ctime, tz=timezone.utc,
            ).isoformat(),
        })
    return {"backups": backups}


# ── POST /api/refresh/{hostname} ─────────────────────────────────────────────

@app.post("/api/refresh/{hostname}")
def start_refresh(hostname: str):
    """Re-run stages 3–9 on an existing VM via WireGuard (idempotent)."""
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not found in hosts_map.yml")
    host_cfg = kvm[hostname]
    wg_ip = host_cfg.get("wg_ip", "")
    if not wg_ip:
        raise HTTPException(400, f"No WireGuard IP configured for '{hostname}'")

    job_id = str(uuid.uuid4())[:8]
    _spawn_job("refresh", job_id, {
        "hostname": hostname,
        "host_cfg": host_cfg,
    }, hostname=hostname)
    return {"job_id": job_id}


# ── GET /api/health/{hostname} ────────────────────────────────────────────────

@app.get("/api/health/{hostname}")
def get_health(hostname: str):
    """Quick SSH health check for an ERPNext VM.

    Returns { web, app, db } each as 'green' | 'amber' | 'red'.
    amber = check could not run (SSH timeout, unreachable).
    """
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not found in hosts_map.yml")
    wg_ip = kvm[hostname].get("wg_ip", "")
    if not wg_ip:
        raise HTTPException(400, f"No WireGuard IP for '{hostname}'")

    ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
                "-o", "BatchMode=yes", f"you@{wg_ip}"]

    def run(cmd: str, timeout: int = 8) -> str:
        try:
            r = subprocess.run(ssh_base + [cmd], capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip()
        except Exception:
            return ""

    # Web: nginx active?
    nginx_state = run("systemctl is-active nginx 2>/dev/null")
    web = "green" if nginx_state == "active" else ("amber" if not nginx_state else "red")

    # App: supervisor processes — all RUNNING = green, some = amber, none/error = red
    sup_out = run("sudo supervisorctl status 2>/dev/null")
    if sup_out:
        lines   = [l for l in sup_out.splitlines() if l.strip()]
        total   = len(lines)
        running = sum(1 for l in lines if "RUNNING" in l)
        app     = "green" if total > 0 and running == total else ("amber" if running > 0 else "red")
    else:
        app = "amber"

    # DB: MariaDB responding?
    secrets = load_build_secrets(str(PROJECT_ROOT))
    db_pwd = secrets["db_root_pwd"]
    db_out = run(f"sudo mysql -u root -p{db_pwd} -e 'SELECT 1' 2>/dev/null && echo ok")
    db = "green" if "ok" in db_out else ("amber" if not db_out else "red")

    return {"web": web, "app": app, "db": db}


# ── POST /api/destroy/{hostname} ─────────────────────────────────────────────

@app.post("/api/destroy/{hostname}")
def start_destroy(hostname: str):
    """Start a background job to destroy a KVM host: remove WG peer, delete VM,
    strip from hosts_map.yml / keys.sops.yml / group_vars/all.yml, regen inventory."""
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not found in the kvm group of hosts_map.yml")
    host_cfg = kvm[hostname]
    if host_cfg.get("wg_role") == "hub":
        raise HTTPException(400, f"Cannot destroy hub node '{hostname}' — this would break the entire mesh")

    job_id = str(uuid.uuid4())[:8]
    _spawn_job("destroy", job_id, {
        "hostname": hostname,
        "host_cfg": host_cfg,
    }, hostname=hostname)
    return {"job_id": job_id}


# ── VM power control ─────────────────────────────────────────────────────────

# Safety margin: reserve this much KiB for the host OS when checking RAM.
_HOST_RAM_RESERVE_KIB = 2 * 1024 * 1024   # 2 GiB


def _virsh_ssh(hypervisor: str, virsh_cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a single virsh command on a hypervisor via SSH."""
    full_cmd = f"virsh --connect qemu:///system {virsh_cmd}"
    return subprocess.run(
        ["ssh", hypervisor, full_cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def _check_memory(hypervisor: str, hostname: str) -> str | None:
    """Return an error message if starting *hostname* would exceed safe RAM, else None.

    Queries the hypervisor for total host memory, memory consumed by all
    running domains, and the target VM's configured memory.  If starting
    the VM would leave less than _HOST_RAM_RESERVE_KIB for the host OS,
    returns a human-readable rejection string.
    """
    # 1. Host total memory (KiB) from `virsh nodeinfo`
    r = _virsh_ssh(hypervisor, "nodeinfo")
    if r.returncode != 0:
        return f"Cannot query hypervisor memory: {r.stderr.strip()}"
    host_mem_kib = 0
    for line in r.stdout.splitlines():
        if line.startswith("Memory size:"):
            # "Memory size:      16331264 kB"
            host_mem_kib = int(line.split(":")[1].strip().split()[0])
            break
    if host_mem_kib == 0:
        return "Could not parse host memory from virsh nodeinfo"

    # 2. Sum memory of all currently-running domains
    r_list = _virsh_ssh(hypervisor, "list --name")
    if r_list.returncode != 0:
        return f"Cannot list running VMs: {r_list.stderr.strip()}"
    running_vms = [v.strip() for v in r_list.stdout.splitlines() if v.strip()]

    used_kib = 0
    for vm in running_vms:
        r_info = _virsh_ssh(hypervisor, f"dominfo {vm}")
        if r_info.returncode != 0:
            continue
        for line in r_info.stdout.splitlines():
            if line.startswith("Max memory:"):
                used_kib += int(line.split(":")[1].strip().split()[0])
                break

    # 3. Target VM's configured memory
    r_target = _virsh_ssh(hypervisor, f"dominfo {hostname}")
    if r_target.returncode != 0:
        return f"Cannot query VM config for '{hostname}': {r_target.stderr.strip()}"
    target_kib = 0
    for line in r_target.stdout.splitlines():
        if line.startswith("Max memory:"):
            target_kib = int(line.split(":")[1].strip().split()[0])
            break

    needed = used_kib + target_kib
    available = host_mem_kib - _HOST_RAM_RESERVE_KIB
    if needed > available:
        used_mb = used_kib // 1024
        target_mb = target_kib // 1024
        host_mb = host_mem_kib // 1024
        reserve_mb = _HOST_RAM_RESERVE_KIB // 1024
        running_list = ", ".join(running_vms) if running_vms else "(none)"
        return (
            f"Not enough memory on hypervisor — "
            f"{target_mb} MiB needed for {hostname}, "
            f"{used_mb} MiB already used by [{running_list}], "
            f"host has {host_mb} MiB total ({reserve_mb} MiB reserved for host OS). "
            f"Shut down another VM first."
        )
    return None


@app.post("/api/vm/{hostname}/start")
def vm_start(hostname: str):
    """Start a shut-off VM, with a memory guard to prevent OOM."""
    data = load_hosts_map()
    kvm = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not in hosts_map.yml")
    host_cfg = kvm[hostname]
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise HTTPException(400, f"No hypervisor configured for '{hostname}'")

    # Memory guard
    mem_err = _check_memory(hypervisor, hostname)
    if mem_err:
        raise HTTPException(409, mem_err)

    r = _virsh_ssh(hypervisor, f"start {hostname}")
    if r.returncode != 0:
        detail = r.stderr.strip() or r.stdout.strip()
        if "already active" in (r.stdout + r.stderr).lower():
            return {"ok": True, "message": f"{hostname} is already running"}
        raise HTTPException(500, f"virsh start failed: {detail}")
    return {"ok": True, "message": f"{hostname} started"}


@app.post("/api/vm/{hostname}/stop")
def vm_stop(hostname: str):
    """Graceful shutdown of a running VM (virsh shutdown)."""
    data = load_hosts_map()
    kvm = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not in hosts_map.yml")
    host_cfg = kvm[hostname]
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise HTTPException(400, f"No hypervisor configured for '{hostname}'")
    if host_cfg.get("wg_role") == "hub":
        raise HTTPException(400, f"Cannot stop hub node '{hostname}' — this would break the mesh")

    r = _virsh_ssh(hypervisor, f"shutdown {hostname}")
    if r.returncode != 0:
        detail = r.stderr.strip() or r.stdout.strip()
        if "domain is not running" in (r.stdout + r.stderr).lower():
            return {"ok": True, "message": f"{hostname} is already stopped"}
        raise HTTPException(500, f"virsh shutdown failed: {detail}")
    return {"ok": True, "message": f"{hostname} shutting down"}


@app.post("/api/vm/{hostname}/reboot")
def vm_reboot(hostname: str):
    """Reboot a running VM (virsh reboot)."""
    data = load_hosts_map()
    kvm = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not in hosts_map.yml")
    host_cfg = kvm[hostname]
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise HTTPException(400, f"No hypervisor configured for '{hostname}'")

    r = _virsh_ssh(hypervisor, f"reboot {hostname}")
    if r.returncode != 0:
        detail = r.stderr.strip() or r.stdout.strip()
        raise HTTPException(500, f"virsh reboot failed: {detail}")
    return {"ok": True, "message": f"{hostname} rebooting"}


# ── GET /api/jobs ─────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def list_jobs():
    """Return all jobs — reads from /tmp/esacp-job-*.meta files.

    Survives uvicorn restarts (GH #37).
    """
    result = {}
    for meta_file in JOB_DIR.glob("esacp-job-*.meta"):
        jid = meta_file.stem.replace("esacp-job-", "")
        j = _read_job(jid)
        if j:
            result[jid] = {"status": j["status"], "hostname": j["hostname"]}
    return result


# ── GET /api/jobs/{job_id} ────────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Poll a job's status and accumulated log — reads from disk.

    Survives uvicorn restarts (GH #37).
    """
    j = _read_job(job_id)
    if j is None:
        raise HTTPException(404, "job not found")
    return {"status": j["status"], "log": j["log"], "hostname": j["hostname"]}
