"""ESACP Control Plane API — prototype

Runs on localhost:8088. Proxied from Vite dev server at /api.

Start (from project root):
    uvicorn tools.api:app --port 8088 --reload

Endpoints:
    GET  /api/hosts                  → current KVM hosts + IP suggestions + erp_user/erp_url
    POST /api/hosts/add              → add host to hosts_map.yml, regen inventory
    POST /api/provision/{hostname}   → start background job: cloud-init + WG + buildVM + provisionVM
    POST /api/refresh/{hostname}     → re-SCP + re-run {hostname}-differentiate.sh (git pull + idempotent)
    GET  /api/health/{hostname}      → quick SSH check: { web, app, db } each green/amber/red
    GET  /api/jobs/{job_id}          → poll job status + log lines
"""

from datetime import datetime, timezone
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


PROJECT_ROOT        = Path(__file__).parent.parent
PLATFORMS_KVM       = PROJECT_ROOT / "platforms" / "kvm"
PLATFORMS_PACKER    = PROJECT_ROOT / "platforms" / "packer"
CLOUD_INIT_DIR      = PLATFORMS_KVM / "cloud-init"
HOSTS_MAP           = PROJECT_ROOT / "hosts_map.yml"
GROUP_VARS_ALL      = PROJECT_ROOT / "ansible" / "group_vars" / "all.yml"
KEYS_SOPS           = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"

# Zone → canonical domain mapping
ZONE_DOMAINS: dict[str, str] = {
    "development": "iridium.blue",
    "staging":     "iridium.blue",
    "production":  "logichem.solutions",
}


# Toshiba paths (accessed over SSH)
TOSHIBA_ALIAS        = "toshiba"
TOSHIBA_HYPERVISOR_USER = "hasan"
# Template qcow2 lives in the esacp libvirt pool (vol-clone, no sudo needed).
# Metadata JSON lives in hasan's home dir (writable without sudo).
TOSHIBA_METADATA_DIR = f"/home/{TOSHIBA_HYPERVISOR_USER}/esacp-packer-output"


# saconsole access from controller (ProxyJump through hypervisor)
SACONSOLE_IP        = "192.168.122.10"
SACONSOLE_SSH       = [
    "ssh", "-o", f"ProxyJump={TOSHIBA_ALIAS}",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
    f"you@{SACONSOLE_IP}",
]

app = FastAPI(title="ESACP Control Plane API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store — sufficient for prototype (single process, dev use only)
jobs: dict[str, dict] = {}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _stream_lines(pipe):
    """Yield lines from a binary pipe, handling \\r (carriage return) correctly.

    Terminal progress bars overwrite lines using \\r. In a plain text iterator
    these appear as embedded \\r bytes inside a \\n-terminated line, producing
    hundreds of intermediate states in the log panel. This reader treats \\r as
    'overwrite current line' — only the final value before each \\n is yielded.
    """
    buf = b""
    current = b""
    while True:
        chunk = pipe.read(256)
        if not chunk:
            break
        buf += chunk
        while buf:
            nl = buf.find(b"\n")
            cr = buf.find(b"\r")
            if nl == -1 and cr == -1:
                current += buf
                buf = b""
            elif nl != -1 and (cr == -1 or nl < cr):
                current += buf[:nl]
                yield current.decode("utf-8", errors="replace")
                current = b""
                buf = buf[nl + 1:]
            else:  # cr comes first — overwrite current line
                current = buf[cr + 1:]
                buf = b""
    if current:
        yield current.decode("utf-8", errors="replace")


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
        domain   = ZONE_DOMAINS.get(zone_key, "iridium.blue")
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
    default_hv  = max(set(hypervisors), key=hypervisors.count) if hypervisors else "toshiba"

    return {
        "hosts": hosts,
        "suggestions": {
            "wg_ip":      f"10.10.0.{next_wg}",
            "virbr0_ip":  f"192.168.122.{next_vbr}",
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
    hypervisor: str = "toshiba"
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
            ["ssh", TOSHIBA_ALIAS,
             f"cat {TOSHIBA_METADATA_DIR}/erpnext-v13-latest.json 2>/dev/null"],
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
            ["ssh", TOSHIBA_ALIAS,
             f"cat {TOSHIBA_METADATA_DIR}/erpnext-v13-latest.json 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if meta_r.returncode == 0 and meta_r.stdout.strip():
            meta = json.loads(meta_r.stdout)
            image = meta.get("image")
            if image:
                subprocess.run(
                    ["ssh", TOSHIBA_ALIAS,
                     f"virsh --connect qemu:///system vol-delete --pool esacp '{image}' 2>/dev/null || true"],
                    capture_output=True, text=True, timeout=30,
                )
        # Remove metadata regardless
        r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS,
             f"rm -f {TOSHIBA_METADATA_DIR}/erpnext-v13-latest.json"],
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

    Runs platforms/packer/build.sh on saconsole via SSH.
    saconsole creates the build VM on toshiba, runs Packer provisioners,
    exports the qcow2, then destroys the build VM.
    Only one build may run at a time.
    """
    running = [j for j in jobs.values()
               if j.get("type") == "build_template" and j["status"] == "running"]
    if running:
        raise HTTPException(409, "A template build is already in progress")

    job_id       = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "log": [], "hostname": "template", "type": "build_template"}

    threading.Thread(
        target=_run_build_template,
        args=(job_id,),
        daemon=True,
    ).start()

    return {"job_id": job_id}


def _run_build_template(job_id: str):
    job = jobs[job_id]
    ssh_opts = [
        "-o", f"ProxyJump={TOSHIBA_ALIAS}",
        "-o", "StrictHostKeyChecking=no",
        "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
    ]

    # Patterns where consecutive identical-suffix lines should replace rather than append
    _COMPACT_SUFFIXES = ("— waiting 30s ...",)

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        if job["log"] and any(line.endswith(s) for s in _COMPACT_SUFFIXES):
            if any(job["log"][-1].endswith(s) for s in _COMPACT_SUFFIXES):
                job["log"][-1] = stamped
                print(f"[job {job_id}] {stamped}", flush=True)
                return
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        emit("── ERPNext v13 template build ──")

        # Sync packer directory to saconsole (repo lives on controller, not saconsole)
        emit("Syncing platforms/packer/ to saconsole ...")
        rsync = subprocess.run(
            ["rsync", "-az", "--delete",
             "-e", "ssh " + " ".join(ssh_opts),
             str(PLATFORMS_PACKER) + "/",
             f"you@{SACONSOLE_IP}:/opt/esacp/platforms/packer/"],
            capture_output=True, text=True,
        )
        if rsync.returncode != 0:
            raise RuntimeError(f"rsync to saconsole failed: {rsync.stderr.strip()}")

        emit(f"Connecting to saconsole ({SACONSOLE_IP} via {TOSHIBA_ALIAS}) ...")

        # Run build.sh detached from the SSH session so it survives any uvicorn
        # reload or connection loss.  Exit code is written to REMOTE_EXIT when done.
        # Log output is streamed by polling REMOTE_LOG.  (fixes GH #61)
        REMOTE_LOG  = "/tmp/packer-build-output.log"
        REMOTE_EXIT = "/tmp/packer-build-output.log.exit"

        subprocess.run(SACONSOLE_SSH + [f"rm -f {REMOTE_LOG} {REMOTE_EXIT}"],
                       capture_output=True)

        start_cmd = (
            f"nohup bash -c 'bash /opt/esacp/platforms/packer/build.sh"
            f" > {REMOTE_LOG} 2>&1; echo $? > {REMOTE_EXIT}'"
            f" > /dev/null 2>&1 & echo $!"
        )
        r = subprocess.run(SACONSOLE_SSH + [start_cmd], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Failed to start build on saconsole: {r.stderr.strip()}")
        emit(f"Build detached on saconsole (PID {r.stdout.strip()}) — polling log ...")

        import time
        offset = 0
        while True:
            time.sleep(5)
            # Read any new output appended since last poll
            r = subprocess.run(
                SACONSOLE_SSH + [f"tail -c +{offset + 1} {REMOTE_LOG} 2>/dev/null || true"],
                capture_output=True, text=True,
            )
            if r.stdout:
                for raw_line in r.stdout.splitlines():
                    if raw_line.strip():
                        emit(raw_line)
                offset += len(r.stdout.encode("utf-8"))

            # Check for exit code file — signals build finished
            r = subprocess.run(
                SACONSOLE_SSH + [f"cat {REMOTE_EXIT} 2>/dev/null || echo -1"],
                capture_output=True, text=True,
            )
            exit_str = r.stdout.strip()
            if exit_str != "-1":
                # Drain any final output
                r = subprocess.run(
                    SACONSOLE_SSH + [f"tail -c +{offset + 1} {REMOTE_LOG} 2>/dev/null || true"],
                    capture_output=True, text=True,
                )
                for raw_line in r.stdout.splitlines():
                    if raw_line.strip():
                        emit(raw_line)
                exit_code = int(exit_str) if exit_str.isdigit() else 1
                if exit_code != 0:
                    emit(f"[ERROR] build.sh exited with code {exit_code}")
                    job["status"] = "error"
                    return
                break

        job["status"] = "done"
        emit("── Build complete — new image ready on toshiba ──")

    except Exception as exc:
        emit(f"[ERROR] {exc}")
        job["status"] = "error"


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
    hypervisor: str  = "toshiba"
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
      8.  Ansible wireguard role on saconsole (update hub wg0.conf)
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
      8. Ansible wireguard role on saconsole (add new spoke)
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
        if vm_map and vm_map.get(vm.hostname) is True:
            raise HTTPException(409, f"'{vm.hostname}' is already provisioned — Destroy it first")
        # Flag cleanup for the job thread — any leftover VM/storage will be
        # removed before vol-clone so we don't hit disk pool collisions.
        if vm_map is not None and vm.hostname in vm_map:
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
    jobs[job_id] = {
        "status":   "running",
        "log":      [],
        "hostname": vm.hostname,
        "type":     "provision_erpnext",
    }

    cleanup_cfg = kvm.get(vm.hostname) if needs_cleanup else None

    threading.Thread(
        target=_run_provision_erpnext,
        args=(job_id, vm, cleanup_cfg),
        daemon=True,
    ).start()

    return {"job_id": job_id, "hostname": vm.hostname}




def _run_provision_erpnext(job_id: str, vm: NewErpnextVM, cleanup_cfg: dict | None = None):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        from tools.pipeline.macro.provision import run as run_provision
        run_provision(
            hostname=vm.hostname,
            virbr0_ip=vm.virbr0_ip,
            project_root=str(PROJECT_ROOT),
            emit=emit,
            cleanup_cfg=cleanup_cfg,
        )
        job["status"] = "done"
        emit(f"── Provision complete — ERPNext at https://{vm.hostname}.iridium.blue ──")

    except Exception as exc:
        emit(f"[ERROR] {exc}")
        job["status"] = "error"


# ── POST /api/provision/{hostname} ───────────────────────────────────────────

@app.post("/api/provision/{hostname}")
def start_provision(hostname: str):
    """Start a background provisioning job for a KVM host."""
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not found in the kvm group of hosts_map.yml")

    job_id        = str(uuid.uuid4())[:8]
    jobs[job_id]  = {"status": "running", "log": [], "hostname": hostname}

    threading.Thread(
        target=_run_provision,
        args=(job_id, hostname, kvm[hostname]),
        daemon=True,
    ).start()

    return {"job_id": job_id}


def _run_provision(job_id: str, hostname: str, host_cfg: dict):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        # ── Step 1: cloud-init files ─────────────────────────────────────────
        ci_dir = CLOUD_INIT_DIR / hostname
        if ci_dir.exists():
            emit(f"cloud-init: {ci_dir} exists — skipping generation")
        else:
            emit("── Generating cloud-init files ──")
            _generate_cloud_init(hostname, host_cfg, emit)

        # ── Step 2: WireGuard peer ───────────────────────────────────────────
        if KEYS_SOPS.exists():
            dec = subprocess.run(
                ["sops", "-d", str(KEYS_SOPS)],
                cwd=PROJECT_ROOT, capture_output=True, text=True,
            )
            if hostname in dec.stdout:
                emit(f"WireGuard: keys for '{hostname}' already in keys.sops.yml — skipping")
            else:
                emit("── Adding WireGuard peer ──")
                _add_wg_peer(hostname, emit)
        else:
            emit(f"WireGuard: keys.sops.yml not found — skipping peer generation")

        # ── Steps 3 & 4: buildVM + provisionVM ──────────────────────────────
        for sub in ("buildVM", "provisionVM"):
            emit(f"── {sub} {hostname} ──")
            proc = subprocess.Popen(
                ["python3", "tools/esacp.py", sub, hostname],
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
    
            )
            for line in _stream_lines(proc.stdout):
                emit(line)
            proc.wait()
            if proc.returncode != 0:
                emit(f"[ERROR] {sub} exited with code {proc.returncode}")
                job["status"] = "error"
                return
            emit(f"[OK] {sub} complete")

        # ── Step 5: Update saconsole hub WireGuard config ────────────────────
        # saconsole's wg0.conf must be regenerated to include the new spoke peer.
        emit("── Update saconsole WireGuard (add new peer) ──")
        proc = subprocess.Popen(
            [
                "ansible-playbook",
                "-i", "inventory/kvm.yml",
                "site-kvm.yml",
                "--limit", "saconsole",
                "--tags", "wireguard",
            ],
            cwd=str(PROJECT_ROOT / "ansible"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

        )
        for line in _stream_lines(proc.stdout):
            emit(line)
        proc.wait()
        if proc.returncode != 0:
            emit(f"[WARN] saconsole WireGuard update failed (exit {proc.returncode}) — new peer may not connect")
        else:
            emit("[OK] saconsole WireGuard updated")

        job["status"] = "done"
        emit("── Provisioning complete ──")

    except Exception as exc:
        emit(f"[ERROR] {exc}")
        job["status"] = "error"


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

    job_id       = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "log": [], "hostname": hostname}
    threading.Thread(
        target=_run_refresh,
        args=(job_id, hostname, host_cfg),
        daemon=True,
    ).start()
    return {"job_id": job_id}


def _run_refresh(job_id: str, hostname: str, host_cfg: dict):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        from tools.pipeline.macro.refresh import run as run_refresh
        run_refresh(
            hostname=hostname,
            host_cfg=host_cfg,
            project_root=str(PROJECT_ROOT),
            emit=emit,
        )
        job["status"] = "done"
        emit("── Refresh complete ──")

    except Exception as exc:
        emit(f"[ERROR] {exc}")
        job["status"] = "error"


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
    db_out = run("sudo mysql -u root -perpnext_build -e 'SELECT 1' 2>/dev/null && echo ok")
    db = "green" if "ok" in db_out else ("amber" if not db_out else "red")

    return {"web": web, "app": app, "db": db}


def _generate_cloud_init(hostname: str, host_cfg: dict, emit):
    """Generate cloud-init user-data + meta-data from the target1 template."""
    template_dir = CLOUD_INIT_DIR / "target1"
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    ci_dir = CLOUD_INIT_DIR / hostname
    ci_dir.mkdir(parents=True, exist_ok=True)

    virbr0_ip = host_cfg.get("virbr0_ip", "")

    user_data = (template_dir / "user-data").read_text()
    user_data = user_data.replace("hostname: target1", f"hostname: {hostname}")
    user_data = user_data.replace("192.168.122.11", virbr0_ip)
    (ci_dir / "user-data").write_text(user_data)

    meta_data = (template_dir / "meta-data").read_text()
    meta_data = meta_data.replace("target1", hostname)
    (ci_dir / "meta-data").write_text(meta_data)

    emit(f"  [OK] cloud-init written to {ci_dir}")



def _add_wg_peer(hostname: str, emit):
    """Run add_peer.sh and insert the new public key into group_vars/all.yml."""
    result = subprocess.run(
        ["bash", "config/wireguard/add_peer.sh", hostname],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            emit(f"  {line}")
    if result.returncode != 0:
        raise RuntimeError(f"add_peer.sh failed:\n{result.stderr.strip()}")

    # Extract "wg_pubkey_<name>: "<key>"" from add_peer.sh stdout
    match = re.search(r'(wg_pubkey_[\w-]+):\s+"([^"]+)"', result.stdout)
    if match:
        key_name, key_value = match.group(1), match.group(2)
        content = GROUP_VARS_ALL.read_text()
        if key_name not in content:
            lines     = content.splitlines(keepends=True)
            insert_at = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("wg_pubkey_"):
                    insert_at = i + 1
            lines.insert(insert_at, f'{key_name}: "{key_value}"\n')
            GROUP_VARS_ALL.write_text("".join(lines))
            emit(f"  [OK] Added {key_name} to group_vars/all.yml")
        else:
            emit(f"  [OK] {key_name} already present in group_vars/all.yml")
    else:
        emit("  [WARN] Could not parse public key from add_peer.sh output — update group_vars/all.yml manually")


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

    job_id       = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "log": [], "hostname": hostname, "type": "destroy"}

    threading.Thread(
        target=_run_destroy,
        args=(job_id, hostname, host_cfg),
        daemon=True,
    ).start()

    return {"job_id": job_id}


def _run_destroy(job_id: str, hostname: str, host_cfg: dict):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        # ── Step 1: Get public key + remove live WireGuard peer ──────────────
        emit("── Remove live WireGuard peer ──")
        pubkey = _get_wg_pubkey(hostname)
        if pubkey:
            _remove_wg_peer_live(hostname, pubkey, emit)
        else:
            emit(f"  [WARN] No pubkey found for {hostname} — skipping live WG removal")

        # ── Step 2: Destroy VM on hypervisor ─────────────────────────────────
        emit("── Destroy VM ──")
        _destroy_vm(hostname, host_cfg, emit)

        # ── Step 3: Remove from hosts_map.yml ────────────────────────────────
        emit("── Update hosts_map.yml ──")
        _remove_from_hosts_map(hostname, emit)

        # ── Step 4: Remove pubkey from group_vars/all.yml ────────────────────
        emit("── Update group_vars/all.yml ──")
        _remove_from_group_vars_all(hostname, emit)

        # ── Step 5: Regenerate inventory ─────────────────────────────────────
        emit("── Regenerate inventory ──")
        result = subprocess.run(
            ["python3", "tools/generate_inventory.py"],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"generate_inventory.py failed:\n{result.stderr}")
        emit("  [OK] inventory regenerated")

        # ── Step 6: Update saconsole wg0.conf via Ansible wireguard role ─────
        emit("── Update saconsole WireGuard config (Ansible) ──")
        proc = subprocess.Popen(
            [
                "ansible-playbook",
                "-i", "inventory/kvm.yml",
                "site-kvm.yml",
                "--limit", "saconsole",
                "--tags", "wireguard",
            ],
            cwd=str(PROJECT_ROOT / "ansible"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

        )
        for line in _stream_lines(proc.stdout):
            emit(line)
        proc.wait()
        if proc.returncode != 0:
            emit(f"  [WARN] Ansible wireguard update failed (exit {proc.returncode}) — wg0.conf may still list old peer")
        else:
            emit("  [OK] saconsole wg0.conf updated")

        # ── Step 7: Remove keys from keys.sops.yml ───────────────────────────
        emit("── Remove WireGuard keys ──")
        _remove_keys_from_sops(hostname, emit)

        # ── Step 8: Remove cloud-init dir if present ─────────────────────────
        ci_dir = CLOUD_INIT_DIR / hostname
        if ci_dir.exists():
            shutil.rmtree(ci_dir)
            emit(f"  [OK] Removed cloud-init dir {ci_dir}")

        job["status"] = "done"
        emit("── Destroy complete ──")

    except Exception as exc:
        emit(f"[ERROR] {exc}")
        job["status"] = "error"


def _get_wg_pubkey(hostname: str) -> str | None:
    """Decrypt keys.sops.yml and return the WireGuard public key for hostname, or None."""
    if not KEYS_SOPS.exists():
        return None
    dec = subprocess.run(
        ["sops", "-d", str(KEYS_SOPS)],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        return None
    keys_data = yaml.safe_load(dec.stdout)
    peer = keys_data.get(hostname, {})
    return peer.get("public_key") if isinstance(peer, dict) else None


def _remove_wg_peer_live(hostname: str, pubkey: str, emit):
    """Remove the WireGuard peer from saconsole hub live (wg set ... remove)."""
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    hub  = next((h for h in kvm.values() if h.get("wg_role") == "hub"), None)
    if not hub:
        emit("  [WARN] Cannot find hub in hosts_map.yml — skipping live WG removal")
        return
    hub_ip  = hub.get("virbr0_ip", "192.168.122.10")
    hub_hv  = hub.get("hypervisor", "toshiba")
    r = subprocess.run(
        ["ssh", "-o", f"ProxyJump={hub_hv}", "-o", "StrictHostKeyChecking=no",
         f"you@{hub_ip}", f"sudo wg set wg0 peer {pubkey} remove"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        emit(f"  [WARN] wg set peer remove failed: {r.stderr.strip()}")
    else:
        emit(f"  [OK] Live WireGuard peer for {hostname} removed from hub")


def _destroy_vm(hostname: str, host_cfg: dict, emit):
    """Destroy (stop) then undefine (delete + storage) the VM on its hypervisor."""
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise RuntimeError(f"No hypervisor configured for '{hostname}'")

    # Delete all snapshots first — libvirt 6.0.0 refuses to undefine a domain
    # that has snapshots. Loop until snapshot-list returns empty (handles
    # hierarchical snapshot trees where a parent can't be deleted before children).
    for _attempt in range(20):
        snap_r = subprocess.run(
            ["ssh", hypervisor,
             f"virsh --connect qemu:///system snapshot-list {hostname} --name"],
            capture_output=True, text=True, timeout=30,
        )
        snapshots = [s.strip() for s in snap_r.stdout.strip().splitlines() if s.strip()]
        if not snapshots:
            break
        for snap_name in snapshots:
            # Single-string SSH command so the remote shell handles quoting.
            # ["ssh", host, "bash", "-c", "cmd"] is WRONG in subprocess — SSH
            # joins args with spaces → bash -c only sees the first word as its
            # script and hangs reading stdin. Pass one string; the remote shell
            # then parses the single-quotes around the snapshot name correctly.
            del_r = subprocess.run(
                ["ssh", hypervisor,
                 f"virsh --connect qemu:///system snapshot-delete {hostname} '{snap_name}'"],
                capture_output=True, text=True, timeout=60,
            )
            if del_r.returncode == 0:
                emit(f"  [OK] Deleted snapshot: {snap_name}")
            else:
                emit(f"  [WARN] snapshot-delete {snap_name}: {del_r.stderr.strip()}")

    for virsh_cmd in (
        f"virsh --connect qemu:///system destroy {hostname}",
        f"virsh --connect qemu:///system undefine {hostname} --remove-all-storage",
    ):
        r = subprocess.run(
            ["ssh", hypervisor, virsh_cmd],
            capture_output=True, text=True, timeout=60,
        )
        combined = (r.stdout + r.stderr).lower()
        if r.returncode != 0:
            if "domain is not running" in combined or "failed to get domain" in combined:
                emit(f"  [OK] {virsh_cmd} — VM was already stopped or absent, continuing")
            else:
                raise RuntimeError(f"'{virsh_cmd}' failed: {r.stderr.strip()}")
        else:
            emit(f"  [OK] {virsh_cmd}")


def _remove_from_hosts_map(hostname: str, emit):
    """Remove the host YAML block from hosts_map.yml using regex."""
    text    = HOSTS_MAP.read_text()
    pattern = rf'\n    {re.escape(hostname)}:\n(?:[ ]{{6}}[^\n]*\n)+'
    new_text = re.sub(pattern, "\n", text)
    # Collapse any triple+ newlines left by the removal
    new_text = re.sub(r'\n{3,}', "\n\n", new_text)
    if new_text == text:
        emit(f"  [WARN] '{hostname}' block not found in hosts_map.yml — nothing removed")
    else:
        HOSTS_MAP.write_text(new_text)
        emit(f"  [OK] Removed '{hostname}' from hosts_map.yml")


def _remove_from_group_vars_all(hostname: str, emit):
    """Remove the wg_pubkey_<hostname> line from group_vars/all.yml."""
    key_name = f"wg_pubkey_{hostname}"
    content  = GROUP_VARS_ALL.read_text()
    if key_name not in content:
        emit(f"  [OK] {key_name} not in group_vars/all.yml — nothing to remove")
        return
    lines    = [l for l in content.splitlines(keepends=True) if not l.startswith(f"{key_name}")]
    GROUP_VARS_ALL.write_text("".join(lines))
    emit(f"  [OK] Removed {key_name} from group_vars/all.yml")


def _remove_keys_from_sops(hostname: str, emit):
    """Decrypt keys.sops.yml, remove hostname entries, re-encrypt in place."""
    if not KEYS_SOPS.exists():
        emit("  [WARN] keys.sops.yml not found — skipping")
        return

    # Read age recipient from .sops.yaml
    sops_conf = PROJECT_ROOT / ".sops.yaml"
    match     = re.search(r'age1[a-z0-9]+', sops_conf.read_text())
    if not match:
        raise RuntimeError(f"Cannot find age recipient in {sops_conf}")
    age_recipient = match.group(0)

    dec = subprocess.run(
        ["sops", "-d", str(KEYS_SOPS)],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        raise RuntimeError(f"sops decrypt failed: {dec.stderr.strip()}")

    keys_data = yaml.safe_load(dec.stdout)
    removed   = []

    if hostname in keys_data:
        del keys_data[hostname]
        removed.append(hostname)

    psks = keys_data.get("preshared_keys", {})
    for k in [k for k in psks if hostname in k]:
        del psks[k]
        removed.append(f"preshared_keys.{k}")

    if not removed:
        emit(f"  [WARN] No keys for '{hostname}' found in keys.sops.yml")
        return

    work_dir = Path(tempfile.mkdtemp())
    try:
        plain = work_dir / "keys.sops.yml"
        plain.write_text(yaml.dump(keys_data, default_flow_style=False, sort_keys=False))

        enc = subprocess.run(
            ["sops", "--encrypt", "--age", age_recipient,
             "--input-type", "yaml", "--output-type", "yaml", str(plain)],
            capture_output=True, text=True,
        )
        if enc.returncode != 0:
            raise RuntimeError(f"sops encrypt failed: {enc.stderr.strip()}")
        KEYS_SOPS.write_text(enc.stdout)
        emit(f"  [OK] Removed from keys.sops.yml: {', '.join(removed)}")
    finally:
        for f in work_dir.iterdir():
            subprocess.run(["shred", "-u", str(f)], capture_output=True)
        work_dir.rmdir()


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
    """Return all jobs — allows the frontend to reconnect after a page refresh."""
    return {
        jid: {"status": j["status"], "hostname": j["hostname"]}
        for jid, j in jobs.items()
    }


# ── GET /api/jobs/{job_id} ────────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Poll a provisioning job's status and accumulated log."""
    if job_id not in jobs:
        raise HTTPException(404, "job not found")
    j = jobs[job_id]
    return {"status": j["status"], "log": j["log"], "hostname": j["hostname"]}
