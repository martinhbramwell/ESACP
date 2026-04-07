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
GROUP_VARS_ALL_SOPS = PROJECT_ROOT / "ansible" / "group_vars" / "all.sops.yml"
KEYS_SOPS           = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"

# Cloudflare
CF_ZONE_ID_IRIDIUM  = "631cd57fa246c8bc575bdc55bc0db70b"   # iridium.blue zone
CF_DNS_TTL          = 120

# Zone → canonical domain mapping
ZONE_DOMAINS: dict[str, str] = {
    "development": "iridium.blue",
    "staging":     "iridium.blue",
    "production":  "logichem.solutions",
}

# acme.sh cert home on saconsole
ACME_CERT_HOME_SACONSOLE = "/opt/acme-certs"

# Toshiba paths (accessed over SSH)
TOSHIBA_ALIAS        = "toshiba"
TOSHIBA_HYPERVISOR_USER = "hasan"
# Template qcow2 lives in the esacp libvirt pool (vol-clone, no sudo needed).
# Metadata JSON lives in hasan's home dir (writable without sudo).
TOSHIBA_METADATA_DIR = f"/home/{TOSHIBA_HYPERVISOR_USER}/esacp-packer-output"

# Logichem bespoke app sources (controller-local) — only BKP + ddlViews still rsynced
LOGICHEM_DIR       = Path.home() / "projects" / "Logichem"
BKP_SRC            = LOGICHEM_DIR / "ce_sri" / "BKP"
VIEWS_DDL_SRC      = LOGICHEM_DIR / "ce_sri" / "example_srvr_files" / "views.ddl"

# GitHub deploy keys for bespoke app repos (SCP'd to VM during provision)
DEPLOY_KEY_DIR       = Path.home() / ".ssh"
DEPLOY_KEYS          = {
    "ce_sri":         DEPLOY_KEY_DIR / "you_gh_ce_sri",
    "ce_sri_svc":     DEPLOY_KEY_DIR / "you_gh_ce_sri_svc",
    "route_planner":  DEPLOY_KEY_DIR / "you_gh_route_planner",
}
DEPLOY_KEY_PASSPHRASE = DEPLOY_KEY_DIR / "you_gh.txt"

# ce_sri secrets (SCP'd to VM for install.py's before_install)
CE_SRI_SECRETS_DIR   = Path.home() / ".ssh" / "secrets"
CE_SRI_P12_CERT      = CE_SRI_SECRETS_DIR / "PRESIDENTE_DANIEL_LEONARD_WILD_STAPEL_1709470171_171224162014.p12"
CE_SRI_PARMS_SOPS    = PROJECT_ROOT / "config" / "ce_sri_parms.sops.json"
CE_SRI_LOGO          = LOGICHEM_DIR / "ce_sri" / "example_srvr_files" / "docType_Logo.png"

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

def _query_provisioned(hypervisor: str | None) -> dict[str, bool] | None:
    """Return a dict mapping VM name → provisioned (True/False), or None if unreachable.

    provisioned=True  → VM has a 'Baseline' snapshot (Ansible completed)
    provisioned=False → VM exists but has no 'Baseline' snapshot (in-flight or partial)

    One SSH call per hypervisor; the remote shell loops over all VMs.
    """
    script = (
        "for vm in $(virsh --connect qemu:///system list --all --name | grep -v '^$'); do "
        "  if virsh --connect qemu:///system snapshot-list $vm --name 2>/dev/null "
        "     | grep -qi 'baseline'; then "
        "    echo provisioned:$vm; "
        "  else "
        "    echo exists:$vm; "
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
                    result[line[len("provisioned:"):]] = True
                elif line.startswith("exists:"):
                    result[line[len("exists:"):]] = False
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
        else:
            provisioned = vm_map.get(name, False)  # False = not yet created

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

TOSHIBA_IMAGES_DIR = "/mnt/esacp-disk/var/lib/libvirt/images"
TOSHIBA_POOL       = "esacp"


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


def _build_template_seed_iso(vm: NewErpnextVM, emit) -> Path:
    """Build a cloud-config (NoCloud) seed ISO for virt-install --import deployment.

    The Packer-built template image already has the 'you' user from its original
    cloud-init run. We inject the controller's SSH public key so api.py can SSH in
    after boot, and set the per-VM hostname and static IP.
    """
    controller_pubkey_path = Path.home() / ".ssh" / "hasan_mighty.pub"
    if not controller_pubkey_path.exists():
        raise FileNotFoundError(f"Controller pubkey not found: {controller_pubkey_path}")
    controller_pubkey = controller_pubkey_path.read_text().strip()

    user_data = f"""\
#cloud-config
hostname: {vm.hostname}
fqdn: {vm.hostname}.local
manage_etc_hosts: true

users:
  - name: you
    ssh_authorized_keys:
      - {controller_pubkey}
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo, adm
    lock_passwd: true
    shell: /bin/bash
"""

    network_config = f"""\
version: 2
ethernets:
  enp1s0:
    addresses:
      - {vm.virbr0_ip}/24
    routes:
      - to: default
        via: 192.168.122.1
    nameservers:
      addresses: [8.8.8.8, 1.1.1.1]
"""

    meta_data = f"instance-id: {vm.hostname}\nlocal-hostname: {vm.hostname}\n"

    work_dir = Path(tempfile.mkdtemp())
    try:
        (work_dir / "user-data").write_text(user_data)
        (work_dir / "meta-data").write_text(meta_data)
        (work_dir / "network-config").write_text(network_config)

        seed_iso = PLATFORMS_KVM / f"{vm.hostname}-seed.iso"
        r = subprocess.run(
            [
                "cloud-localds",
                "--network-config", str(work_dir / "network-config"),
                str(seed_iso),
                str(work_dir / "user-data"),
                str(work_dir / "meta-data"),
            ],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"cloud-localds failed: {r.stderr.strip()}")
        emit(f"  [OK] Seed ISO: {seed_iso.name}")
        return seed_iso
    finally:
        shutil.rmtree(work_dir)


def _scp_cesri_secrets(
    emit, scp_opts: list[str], target_ip: str,
    site_url: str, nickname_str: str, erp_user: str,
) -> int:
    """Decrypt SOPS parms, patch per-VM values, SCP P12 + parms + logo to /tmp/.

    Returns the number of files successfully transferred (0 = nothing to send).
    Called from both Deploy and Refresh so secrets are always fresh on the VM.
    """
    import json as _json

    cesri_scp_files: list[str] = []
    if CE_SRI_P12_CERT.exists():
        cesri_scp_files.append(str(CE_SRI_P12_CERT))
    else:
        emit(f"  [WARN] P12 cert not found at {CE_SRI_P12_CERT}")
    if CE_SRI_LOGO.exists():
        cesri_scp_files.append(str(CE_SRI_LOGO))
    else:
        emit(f"  [WARN] company logo not found at {CE_SRI_LOGO}")

    if CE_SRI_PARMS_SOPS.exists():
        sops_r = subprocess.run(
            ["sops", "-d", str(CE_SRI_PARMS_SOPS)],
            capture_output=True, text=True, timeout=15,
        )
        if sops_r.returncode != 0:
            raise RuntimeError(f"sops decrypt failed: {sops_r.stderr.strip()}")
        parms = _json.loads(sops_r.stdout)
        parms["erpnext_api"]["local_site"] = site_url
        parms["erpnext_api"]["api_protocol"] = "https"
        parms["erpnext_api"]["api_port"] = "443"
        parms["electronic_signature"]["certificate_location"] = f"/home/{erp_user}/.ssh/secrets"
        parms["electronic_signature"]["sri_p12_cert"] = CE_SRI_P12_CERT.name
        parms["environment"]["local_site_nickname"] = nickname_str
        parms["environment"]["company_logo_location"] = f"/home/{erp_user}/.ssh/secrets"
        parms["revenue_service"]["test_or_production_mode"] = "1"
        parms_tmp = Path("/tmp") / f"ce_sri_parms_{nickname_str}.json"
        parms_tmp.write_text(_json.dumps(parms, indent=2))
        cesri_scp_files.append(str(parms_tmp))
    else:
        emit(f"  [WARN] ce_sri_parms.sops.json not found at {CE_SRI_PARMS_SOPS}")

    if not cesri_scp_files:
        return 0

    r = subprocess.run(
        ["scp"] + scp_opts + cesri_scp_files + [f"you@{target_ip}:/tmp/"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        emit(f"  [WARN] SCP ce_sri secrets failed: {r.stderr.strip()}")
        return 0
    emit(f"  [OK] {len(cesri_scp_files)} ce_sri secret files → /tmp/")
    return len(cesri_scp_files)


def _run_provision_erpnext(job_id: str, vm: NewErpnextVM, cleanup_cfg: dict | None = None):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    target_ssh = [
        "ssh",
        "-o", f"ProxyJump={TOSHIBA_ALIAS}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
        f"you@{vm.virbr0_ip}",
    ]

    try:
        # ── Step 0: Clean up residue from a previous build ────────────────────
        if cleanup_cfg:
            emit("── Step 0: Cleaning up residue from previous build ──")
            _destroy_vm(vm.hostname, cleanup_cfg, emit)
            emit("  [OK] Old VM residue removed — starting fresh")

        # ── Step 1: WireGuard peer ────────────────────────────────────────────
        emit("── Step 1: Add WireGuard peer ──")
        if KEYS_SOPS.exists():
            dec = subprocess.run(
                ["sops", "-d", str(KEYS_SOPS)],
                cwd=PROJECT_ROOT, capture_output=True, text=True,
            )
            if vm.hostname in dec.stdout:
                emit(f"  WireGuard keys for '{vm.hostname}' already present — skipping")
            else:
                _add_wg_peer(vm.hostname, emit)
        else:
            emit("  keys.sops.yml not found — skipping WireGuard peer generation")

        # ── Step 2: Build seed ISO ────────────────────────────────────────────
        emit("── Step 2: Build cloud-config seed ISO ──")
        seed_local = _build_template_seed_iso(vm, emit)

        # ── Step 3: Upload seed ISO to hypervisor ────────────────────────────
        emit("── Step 3: Upload seed ISO to hypervisor ──")
        remote_seed = f"{TOSHIBA_IMAGES_DIR}/{vm.hostname}-seed.iso"
        r = subprocess.run(
            ["scp", str(seed_local), f"{TOSHIBA_HYPERVISOR_USER}@{TOSHIBA_ALIAS}:{remote_seed}"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"scp seed ISO failed: {r.stderr.strip()}")
        emit(f"  [OK] Seed ISO at {TOSHIBA_ALIAS}:{remote_seed}")

        # ── Step 4: Clone template qcow2 ─────────────────────────────────────
        emit("── Step 4: Clone template qcow2 ──")
        meta_r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS,
             f"cat {TOSHIBA_METADATA_DIR}/erpnext-v13-latest.json 2>/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        if meta_r.returncode != 0 or not meta_r.stdout.strip():
            raise RuntimeError("Template metadata not found on toshiba — run a Packer build first")
        meta = json.loads(meta_r.stdout)
        template_image = meta.get("image")
        if not template_image:
            raise RuntimeError("Template metadata missing 'image' field")
        emit(f"  Template image: {template_image}")

        clone_r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS,
             f"virsh --connect qemu:///system vol-clone --pool {TOSHIBA_POOL} "
             f"'{template_image}' '{vm.hostname}.qcow2'"],
            capture_output=True, text=True, timeout=300,
        )
        if clone_r.returncode != 0:
            raise RuntimeError(f"vol-clone failed: {clone_r.stderr.strip()}")
        emit(f"  [OK] Cloned {template_image} → {vm.hostname}.qcow2")

        # ── Step 5: virt-install --import ─────────────────────────────────────
        emit("── Step 5: virt-install --import ──")
        virt_cmd = (
            f"virt-install --connect qemu:///system"
            f" --name {vm.hostname}"
            f" --ram 4096"
            f" --vcpus 2"
            f" --disk vol={TOSHIBA_POOL}/{vm.hostname}.qcow2"
            f" --disk path={remote_seed},device=cdrom,readonly=on"
            f" --network network=default"
            f" --os-variant ubuntu20.04"
            f" --import"
            f" --graphics vnc"
            f" --noautoconsole"
        )
        r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS, virt_cmd],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            raise RuntimeError(f"virt-install --import failed: {r.stderr.strip()}")
        emit(f"  [OK] VM {vm.hostname} started (booting from template)")

        # ── Step 6: Wait for SSH ──────────────────────────────────────────────
        emit("── Step 6: Wait for SSH ──")
        subprocess.run(["ssh-keygen", "-R", vm.virbr0_ip], capture_output=True)
        subprocess.run(["ssh-keygen", "-R", vm.hostname],  capture_output=True)

        ssh_ready = False
        for attempt in range(60):
            time.sleep(10)
            r = subprocess.run(
                target_ssh + ["echo ready"],
                capture_output=True, text=True,
            )
            if r.returncode == 0 and "ready" in r.stdout:
                emit(f"  [OK] SSH up after ~{(attempt + 1) * 10}s")
                ssh_ready = True
                break
            if attempt % 3 == 0:
                emit(f"  Waiting for SSH ... ({(attempt + 1) * 10}s)")
        if not ssh_ready:
            raise RuntimeError("VM did not become SSH-ready within 10 minutes")

        # ── Step 7: Baseline snapshot ─────────────────────────────────────────
        emit("── Step 7: Take Baseline snapshot ──")
        r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS,
             f"virsh --connect qemu:///system snapshot-create-as {vm.hostname} 'Baseline' --atomic"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            emit(f"  [WARN] Baseline snapshot failed: {r.stderr.strip()}")
        else:
            emit("  [OK] Baseline snapshot taken")

        # ── Step 8: Update saconsole WireGuard ───────────────────────────────
        emit("── Step 8: Update saconsole WireGuard (Ansible) ──")
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
            emit(f"  [WARN] Ansible wireguard update failed (exit {proc.returncode})")
        else:
            emit("  [OK] saconsole WireGuard updated")

        # ── Step 8b: Cloudflare DNS A record ──────────────────────────────────
        emit("── Step 8b: Cloudflare DNS A record ──")
        _cf_dns_upsert(vm.hostname, vm.wg_ip, emit)

        # ── Step 8c: Distribute TLS cert from saconsole to VM ─────────────────
        emit("── Step 8c: Distribute TLS wildcard cert to VM ──")
        domain_dir = f"{ACME_CERT_HOME_SACONSOLE}/iridium.blue"
        sac_ssh_base = [
            "ssh", "-o", f"ProxyJump={TOSHIBA_ALIAS}",
            "-o", "StrictHostKeyChecking=no",
            "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
        ]
        # Verify cert exists on saconsole
        cert_check = subprocess.run(
            sac_ssh_base + [f"you@{SACONSOLE_IP}",
                            f"test -f {domain_dir}/fullchain.pem && echo found || echo missing"],
            capture_output=True, text=True, timeout=15,
        )
        if "found" not in cert_check.stdout:
            emit(f"  [WARN] Wildcard cert not found on saconsole at {domain_dir} — nginx will be HTTP-only")
            have_cert = False
        else:
            # Read each cert file from saconsole, push to VM /tmp/
            for pem_name, tmp_name in [
                ("fullchain.pem", "fullchain.pem"),
                ("key.pem",       "privkey.pem"),
                ("cert.pem",      "cert.pem"),
            ]:
                read_r = subprocess.run(
                    sac_ssh_base + [f"you@{SACONSOLE_IP}", f"cat {domain_dir}/{pem_name}"],
                    capture_output=True, timeout=15,
                )
                if read_r.returncode != 0:
                    raise RuntimeError(f"Failed to read {pem_name} from saconsole")
                write_r = subprocess.run(
                    target_ssh + [f"sudo tee /tmp/{tmp_name} > /dev/null"],
                    input=read_r.stdout,
                    capture_output=True, timeout=15,
                )
                if write_r.returncode != 0:
                    raise RuntimeError(f"Failed to write {tmp_name} to VM")
            emit("  [OK] Cert files in /tmp/ on VM")
            have_cert = True

        # ── Differentiation constants ─────────────────────────────────────────
        nickname_str = vm.nickname or vm.hostname[:4]
        domain       = ZONE_DOMAINS.get(vm.zone, "iridium.blue")
        site_url     = f"{vm.hostname}.{domain}"
        bench_name   = "frappe-bench"                        # Packer template bench dir
        bench_name_new = f"frappe-bench-{nickname_str}"      # renamed at differentiation
        with open(GROUP_VARS_ALL) as _f:
            ERP_USER = yaml.safe_load(_f).get("erp_user", "erpadm")
        bench_dir_orig = f"/home/{ERP_USER}/{bench_name}"    # before rename
        bench_dir      = f"/home/{ERP_USER}/{bench_name_new}" # after rename
        MYPWD        = "erpnext_build"              # MariaDB root pwd set by Packer OS prep
        ERP_USER_PWD = "sasa"
        rsync_e      = (
            f"ssh -o ProxyJump={TOSHIBA_ALIAS} "
            f"-o StrictHostKeyChecking=no "
            f"-i {Path.home() / '.ssh' / 'hasan_mighty'}"
        )
        scp_opts     = [
            "-o", f"ProxyJump={TOSHIBA_ALIAS}",
            "-o", "StrictHostKeyChecking=no",
            "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
        ]

        # ── Step 9: Ansible wireguard spoke on new VM ─────────────────────────
        emit("── Step 9: Configure WireGuard spoke (Ansible) ──")
        proc = subprocess.Popen(
            [
                "ansible-playbook",
                "-i", "inventory/kvm.yml",
                "site-kvm.yml",
                "--limit", vm.hostname,
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
            emit(f"  [WARN] Ansible wireguard spoke failed (exit {proc.returncode}) — continuing")
        else:
            emit("  [OK] WireGuard spoke configured")

        # ── Step 10: SCP deploy keys + rsync BKP (controller → VM) ────────────
        # Apps are now cloned from GitHub inside differentiate.sh (section A2d).
        # Only BKP (database backup archive) is still rsynced from controller.
        emit("── Step 10: SCP deploy keys + rsync BKP ──")

        # SCP deploy keys + passphrase to /tmp/ on VM (differentiate.sh moves them)
        scp_files = []
        for key_name, key_path in DEPLOY_KEYS.items():
            if key_path.exists():
                scp_files.append(str(key_path))
            else:
                emit(f"  [WARN] deploy key {key_path.name} not found — {key_name} clone will fail")
        if DEPLOY_KEY_PASSPHRASE.exists():
            scp_files.append(str(DEPLOY_KEY_PASSPHRASE))
        else:
            emit("  [WARN] deploy key passphrase not found — private repo clones will fail")

        # Include controller pubkey so differentiate.sh can install it for erpadm
        controller_pubkey_path = Path.home() / ".ssh" / "hasan_mighty.pub"
        if controller_pubkey_path.exists():
            scp_files.append(str(controller_pubkey_path))

        if scp_files:
            r = subprocess.run(
                ["scp"] + scp_opts + scp_files + [f"you@{vm.virbr0_ip}:/tmp/"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                raise RuntimeError(f"SCP deploy keys failed: {r.stderr.strip()}")
            emit(f"  [OK] {len(scp_files)} deploy key files → /tmp/")

        # SCP ce_sri secrets (P12 cert, ce_sri_parms.json, logo) to /tmp/ on VM
        _scp_cesri_secrets(
            emit, scp_opts, vm.virbr0_ip,
            site_url, nickname_str, ERP_USER,
        )

        # rsync BKP (database backup — not a git repo)
        if BKP_SRC.exists():
            r = subprocess.run(
                [
                    "rsync", "-a", "--delete",
                    "--rsync-path=sudo rsync",
                    "-e", rsync_e,
                    f"{BKP_SRC}/",
                    f"you@{vm.virbr0_ip}:{bench_dir_orig}/BKP/",
                ],
                capture_output=True, text=True, timeout=600,
            )
            if r.returncode != 0:
                raise RuntimeError(f"rsync BKP failed: {r.stderr.strip()}")
            emit(f"  [OK] BKP → {bench_dir_orig}/BKP")
        else:
            emit(f"  [SKIP] {BKP_SRC} not found")

        # ── Step 11: SCP ddlViews.sql → /tmp/ on VM ──────────────────────────
        emit("── Step 11: SCP ddlViews.sql ──")
        ddl_on_vm = "/tmp/ddlViews.sql"
        if VIEWS_DDL_SRC.exists():
            r = subprocess.run(
                ["scp"] + scp_opts + [str(VIEWS_DDL_SRC), f"you@{vm.virbr0_ip}:{ddl_on_vm}"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                emit(f"  [WARN] scp ddlViews.sql failed: {r.stderr.strip()} — will skip placement")
                ddl_on_vm = ""
            else:
                emit(f"  [OK] ddlViews.sql → {ddl_on_vm}")
        else:
            emit(f"  [SKIP] ddlViews.sql not found at {VIEWS_DDL_SRC}")
            ddl_on_vm = ""

        # ── Step 12: Render config artifacts + deploy to VM ────────────────
        emit("── Step 12: Render config + deploy differentiate.sh ──")

        # TLS / nginx constants
        tls_domain    = "iridium.blue"
        cert_dir      = f"/etc/nginx/certs/{tls_domain}"
        nginx_cert    = f"{cert_dir}/fullchain.pem"
        nginx_key     = f"{cert_dir}/privkey.pem"
        nginx_dhparam = "/etc/nginx/dhparam.pem"
        gunicorn_port = 8000
        ws_port       = 9000

        # Build shared params dict for all renderers
        render_params = {
            "erp_user": ERP_USER, "erp_user_pwd": ERP_USER_PWD, "mypwd": MYPWD,
            "hostname": vm.hostname,
            "tld": domain.split(".", 1)[1] if "." in domain else domain,
            "site_url": site_url, "nickname": nickname_str,
            "bench_name_new": bench_name_new, "bench_dir": bench_dir,
            "gunicorn_port": gunicorn_port, "ws_port": ws_port,
            "nginx_cert": nginx_cert, "nginx_key": nginx_key,
            "nginx_dhparam": nginx_dhparam,
        }

        # Render config artifacts on controller
        from tools.renderers.render_envars import render as r_envars
        from tools.renderers.render_supervisor import render as r_supervisor
        from tools.renderers.render_gh_askpass import render as r_askpass
        from tools.renderers.render_nginx_vhost import render as r_nginx

        rendered_dir = Path(tempfile.mkdtemp(prefix="esacp-rendered-"))
        r_envars(render_params, output_path=rendered_dir / "envars.sh")
        r_supervisor(render_params, output_path=rendered_dir / "ce_sri_svc_supervisor.conf")
        r_askpass(render_params, output_path=rendered_dir / "gh_askpass.sh")
        if have_cert:
            r_nginx(render_params, output_path=rendered_dir / "nginx_vhost.conf")

        # Copy static files into rendered bundle
        shutil.copy(PLATFORMS_KVM / "static" / "Procfile", rendered_dir / "Procfile")
        shutil.copy(PLATFORMS_KVM / "static" / "ssh_config", rendered_dir / "ssh_config")
        shutil.copy(PLATFORMS_KVM / "stop.py", rendered_dir / "stop.py")

        # Write params.json for VM-side renderer (bash_aliases needs runtime DB_NAME)
        (rendered_dir / "params.json").write_text(json.dumps(render_params, indent=2))
        emit(f"  [OK] {len(list(rendered_dir.iterdir()))} config artifacts rendered")

        # SCP rendered bundle + renderers + templates + vm_scripts to VM
        for local_dir, remote_path in [
            (str(rendered_dir) + "/", "/tmp/rendered/"),
            (str(PROJECT_ROOT / "tools" / "renderers") + "/", "/tmp/renderers/"),
            (str(PROJECT_ROOT / "tools" / "vm_scripts") + "/", "/tmp/vm_scripts/"),
            (str(PLATFORMS_KVM / "templates") + "/", "/tmp/templates/"),
        ]:
            r = subprocess.run(
                ["rsync", "-a", "-e",
                 f"ssh -o ProxyJump={TOSHIBA_ALIAS} -o StrictHostKeyChecking=no "
                 f"-i {Path.home() / '.ssh' / 'hasan_mighty'}",
                 local_dir, f"you@{vm.virbr0_ip}:{remote_path}"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                raise RuntimeError(f"rsync {remote_path} failed: {r.stderr.strip()}")
        emit("  [OK] rendered bundle + renderers + templates deployed")

        # Build the ddl_placement snippet (still f-string — 3 lines)
        private_files = f"{bench_dir}/sites/{site_url}/private/files"
        ddl_placement = (
            f"sudo -u \"$ERP_USER\" cp {ddl_on_vm} \"{private_files}/ddlViews.sql\"\n"
            f"rm -f {ddl_on_vm}\n"
            f"echo '  [OK] ddlViews.sql placed'"
        ) if ddl_on_vm else "echo '  [SKIP] ddlViews.sql not available'"

        # TLS section: cert install + nginx vhost placement + DH params + enable
        if have_cert:
            tls_section = f"""\
echo "=== I: install TLS cert ==="
sudo mkdir -p {cert_dir}
if [ -f /tmp/fullchain.pem ]; then
  sudo cp /tmp/fullchain.pem {nginx_cert}
  sudo cp /tmp/privkey.pem   {nginx_key}
  sudo chmod 600 {nginx_key}
  sudo rm -f /tmp/fullchain.pem /tmp/privkey.pem /tmp/cert.pem
  echo "  [OK] certs installed to {cert_dir}"
elif [ -f {nginx_cert} ]; then
  echo "  [OK] certs already in place at {cert_dir} — skipping"
else
  echo "  [ERROR] no cert at /tmp/fullchain.pem and none at {cert_dir}"
  exit 1
fi

echo "=== J: deploy nginx vhost config ==="
sudo cp /tmp/rendered/nginx_vhost.conf /etc/nginx/sites-available/{site_url}
echo "  [OK] /etc/nginx/sites-available/{site_url}"

echo "=== K: DH params + enable site ==="
if [ ! -f {nginx_dhparam} ]; then
    echo "  Generating DH params (2048-bit) — once per VM, reused on redeploy ..."
    sudo openssl dhparam -out {nginx_dhparam} 2048 2>/dev/null
    echo "  [OK] DH params written to {nginx_dhparam}"
fi
sudo ln -sf /etc/nginx/sites-available/{site_url} /etc/nginx/sites-enabled/{site_url}
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
echo "  [OK] nginx reloaded with SSL site"
"""
        else:
            tls_section = """\
echo "=== I-K: TLS cert not available — HTTP only ==="
echo "  [WARN] Deploy wildcard cert to saconsole and re-run to enable HTTPS"
"""

        differentiate_sh = f"""\
#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR_ORIG="{bench_dir_orig}"
BENCH_DIR="{bench_dir}"
SITE_URL="{site_url}"
ERP_USER="{ERP_USER}"
MYPWD="{MYPWD}"
ERP_USER_PWD="{ERP_USER_PWD}"

pip3 install --quiet jinja2 2>/dev/null || true

echo "=== A: deploy pre-rendered envars.sh ==="
sudo mkdir -p /opt/ce_sri
sudo cp /tmp/rendered/envars.sh /opt/ce_sri/envars.sh
sudo chmod 644 /opt/ce_sri/envars.sh
echo "  [OK] /opt/ce_sri/envars.sh"

echo "=== A2: rename bench dir ==="
if sudo test -d "$BENCH_DIR_ORIG" && ! sudo test -L "$BENCH_DIR"; then
    sudo -u "$ERP_USER" ln -sf "$BENCH_DIR_ORIG" "$BENCH_DIR"
    echo "  [OK] symlinked frappe-bench -> {bench_name_new} (venv paths preserved)"
elif sudo test -L "$BENCH_DIR"; then
    echo "  [OK] {bench_name_new} symlink already exists — skipping"
else
    echo "  [ERROR] Neither $BENCH_DIR_ORIG nor $BENCH_DIR found"
    exit 1
fi

echo "=== A2b: deploy Procfile ==="
PROCFILE="$BENCH_DIR/Procfile"
if ! grep -q 'ce_sri_svc' "$PROCFILE" 2>/dev/null; then
  cp /tmp/rendered/Procfile "$PROCFILE"
  chown $ERP_USER:$ERP_USER "$PROCFILE"
  echo "  [OK] Procfile deployed"
else
  echo "  [OK] Procfile already contains ce_sri_svc — skipping"
fi

echo "=== A2c: setup deploy keys for GitHub ==="
mkdir -p /home/$ERP_USER/.ssh
chmod 700 /home/$ERP_USER/.ssh
for key in you_gh_ce_sri you_gh_ce_sri_svc you_gh_route_planner you_gh.txt; do
    if [ -f /tmp/$key ]; then
        mv /tmp/$key /home/$ERP_USER/.ssh/$key
        chmod 600 /home/$ERP_USER/.ssh/$key
    fi
done
cp /tmp/rendered/ssh_config /home/$ERP_USER/.ssh/config
chmod 600 /home/$ERP_USER/.ssh/config
cp /tmp/rendered/gh_askpass.sh /home/$ERP_USER/.ssh/gh_askpass.sh
chmod 700 /home/$ERP_USER/.ssh/gh_askpass.sh
chown -R $ERP_USER:$ERP_USER /home/$ERP_USER/.ssh
echo "  [OK] deploy keys + SSH config installed"

echo "=== A2e: deploy controller pubkey to erpadm authorized_keys ==="
ERPADM_SSH="/home/$ERP_USER/.ssh"
ERPADM_AK="$ERPADM_SSH/authorized_keys"
if [ -f /tmp/hasan_mighty.pub ]; then
    mkdir -p "$ERPADM_SSH"
    if [ -f "$ERPADM_AK" ] && grep -qf /tmp/hasan_mighty.pub "$ERPADM_AK" 2>/dev/null; then
        echo "  [OK] controller pubkey already in authorized_keys — skipping"
    else
        cat /tmp/hasan_mighty.pub >> "$ERPADM_AK"
        echo "  [OK] controller pubkey appended to $ERPADM_AK"
    fi
    chmod 700 "$ERPADM_SSH"
    chmod 600 "$ERPADM_AK"
    chown -R $ERP_USER:$ERP_USER "$ERPADM_SSH"
    rm -f /tmp/hasan_mighty.pub
else
    echo "  [WARN] /tmp/hasan_mighty.pub not found — erpadm SSH access not configured"
fi

echo "=== A2d: clone apps from GitHub ==="
_GH_CLONE() {{
  sudo -u "$ERP_USER" bash -c "
    export DISPLAY=:0
    export SSH_ASKPASS=/home/$ERP_USER/.ssh/gh_askpass.sh
    export SSH_ASKPASS_REQUIRE=force
    export GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no'
    $1
  "
}}
if [ ! -d "$BENCH_DIR/apps/ce_sri/.git" ]; then
  _GH_CLONE "cd $BENCH_DIR && git clone git@ce_sri.gh:martinhbramwell/ce_sri.git apps/ce_sri --branch wip/2026-03-25"
  echo "  [OK] ce_sri cloned"
else
  _GH_CLONE "cd $BENCH_DIR/apps/ce_sri && git pull"
  echo "  [OK] ce_sri pulled"
fi
if [ ! -d "$BENCH_DIR/apps/route_planner/.git" ]; then
  _GH_CLONE "cd $BENCH_DIR && git clone git@route_planner.gh:martinhbramwell/route_planner.git apps/route_planner --branch wip/2026-03-31"
  echo "  [OK] route_planner cloned"
else
  _GH_CLONE "cd $BENCH_DIR/apps/route_planner && git pull"
  echo "  [OK] route_planner pulled"
fi
if [ ! -d "$BENCH_DIR/apps/returnable/.git" ]; then
  sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BtlMng.git apps/returnable --branch wip/2026-03-31"
  echo "  [OK] returnable (BtlMng) cloned"
else
  sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/apps/returnable && git pull"
  echo "  [OK] returnable pulled"
fi
if [ ! -d "$BENCH_DIR/apps/ce_sri/services/ce_sri_svc/.git" ]; then
  _GH_CLONE "mkdir -p $BENCH_DIR/apps/ce_sri/services && cd $BENCH_DIR && git clone git@ce_sri_svc.gh:martinhbramwell/ce_sri_svc.git apps/ce_sri/services/ce_sri_svc --branch wip/2026-03-31"
  echo "  [OK] ce_sri_svc cloned"
else
  _GH_CLONE "cd $BENCH_DIR/apps/ce_sri/services/ce_sri_svc && git pull"
  echo "  [OK] ce_sri_svc pulled"
fi
if [ ! -d "$BENCH_DIR/BaRe/.git" ]; then
  sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BaRe.git BaRe"
  echo "  [OK] BaRe cloned"
else
  sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/BaRe && git pull"
  echo "  [OK] BaRe pulled"
fi
echo "  [OK] all apps cloned/pulled from GitHub"

echo "=== A3: start bench services (supervisor) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
echo "=== A3b: deploy ce_sri_svc supervisor conf ==="
sudo cp /tmp/rendered/ce_sri_svc_supervisor.conf /etc/supervisor/conf.d/ce-sri-svc.conf
echo "  [OK] /etc/supervisor/conf.d/ce-sri-svc.conf deployed"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
sudo chmod o+x /home/"$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"

echo "=== B: fix ownership of BKP ==="
sudo chown -R "$ERP_USER:$ERP_USER" $BENCH_DIR/BKP
echo "  [OK] BKP ownership -> $ERP_USER"

echo "=== B2: (removed — .env generated by install.py before_install in H4c) ==="

echo "=== B2b: npm install for ce_sri_svc ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
if [ -f "$_CESRI_SVC/package.json" ]; then
  sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && npm install 2>&1"
  echo "  [OK] npm install completed for ce_sri_svc"
else
  echo "  [SKIP] no package.json in ce_sri_svc"
fi

echo "=== C: BaRe/envars.sh symlink ==="
sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"

echo "=== D: bench new-site + install-app erpnext ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
if sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL doctor" 2>/dev/null; then
  echo "  [SKIP] site $SITE_URL already exists"
else
  sudo -u "$ERP_USER" bash -c "
    cd $BENCH_DIR
    bench new-site $SITE_URL \\
      --mariadb-root-password $MYPWD \\
      --admin-password $ERP_USER_PWD
    bench --site $SITE_URL install-app erpnext
  "
  echo "  [OK] site created, erpnext installed"
fi

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
{ddl_placement}

echo "=== E1: seed tabPatch Log (skip patches that crash on restored DB) ==="
python3 /tmp/vm_scripts/g1_seed_patch_log.py \
  --bench-dir "$BENCH_DIR" --site "$SITE_URL"

echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G-pre: strip DEFINER clauses from backup SQL ==="
python3 /tmp/vm_scripts/gpre_strip_definer.py --bench-dir "$BENCH_DIR"

echo "=== G: handleRestore.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== G1: re-seed tabPatch Log (restore wiped DB) ==="
python3 /tmp/vm_scripts/g1_seed_patch_log.py \
  --bench-dir "$BENCH_DIR" --site "$SITE_URL"

echo "=== G2: clear fixture Custom Fields + re-migrate ==="
echo "  Clearing fixture-defined Custom Fields from restored DB..."
python3 /tmp/vm_scripts/g2_clear_fixture_custom_fields.py \
  --bench-dir "$BENCH_DIR" --site "$SITE_URL"
echo "  Re-running bench migrate to reimport fixtures..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL migrate" 2>&1 \
  | grep -E "^(Migrating|Executing|Updating|Building)" | tail -10
echo "  [OK] fixtures reimported with correct positioning"

echo "=== H: supervisor reload (post-restore) ==="
sudo supervisorctl reread
sudo supervisorctl update
echo "  [OK] supervisor updated"

echo "=== H2: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
sudo supervisorctl restart frappe-bench-ce-sri-svc || true
echo "  [OK] bench + ce_sri_svc restarted"

echo "=== H2b: wait for gunicorn to respond ==="
PING_URL="http://127.0.0.1:{gunicorn_port}/api/method/ping"
WAITED=0
MAX_WAIT=60
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf "$PING_URL" >/dev/null 2>&1; then
        echo "  [OK] gunicorn responding after ${{WAITED}}s"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done
if [ $WAITED -ge $MAX_WAIT ]; then
    echo "  [WARN] gunicorn did not respond within ${{MAX_WAIT}}s — continuing anyway"
fi

echo "=== H4a: clear stale encrypted secrets + regenerate API key ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && $BENCH_DIR/env/bin/python /tmp/vm_scripts/h4a_apikeys.py --site $SITE_URL --bench-dir $BENCH_DIR"

echo "=== H3: reset admin password (H4a wipes __Auth — must run after) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL set-admin-password $ERP_USER_PWD"
echo "  [OK] admin password reset to ERP_USER_PWD"

echo "=== H4b: place secrets for install.py ==="
sudo -u "$ERP_USER" mkdir -p /home/$ERP_USER/.ssh/secrets
for f in /tmp/*.p12 /tmp/ce_sri_parms_*.json /tmp/docType_Logo.png; do
  if [ -f "$f" ]; then
    DEST="/home/$ERP_USER/.ssh/secrets/$(basename "$f")"
    if [[ "$f" == *ce_sri_parms_*.json ]]; then
      DEST="/home/$ERP_USER/.ssh/secrets/ce_sri_parms.json"
    fi
    sudo mv "$f" "$DEST"
    sudo chown $ERP_USER:$ERP_USER "$DEST"
    sudo chmod 600 "$DEST"
    echo "  [OK] $(basename "$DEST") -> /home/$ERP_USER/.ssh/secrets/"
  fi
done

echo "=== H4c: generate bench nginx.conf (install.py patches it) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup nginx --yes" || true
echo "  [OK] config/nginx.conf generated"

echo "=== H4d: run ce_sri before_install ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL execute ce_sri.install.before_install"
echo "  [OK] ce_sri before_install complete"

echo "=== H4e: generate .env via UPDATE_SRI_SERVICE_PARAMETERS.py ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
python3 /tmp/vm_scripts/h4e_patch_parms.py \
  --apikey-sh "$BENCH_DIR/sites/$SITE_URL/private/files/apikey.sh" \
  --parms /home/$ERP_USER/.ssh/secrets/ce_sri_parms.json
sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && python3 UPDATE_SRI_SERVICE_PARAMETERS.py --parms /home/$ERP_USER/.ssh/secrets/ce_sri_parms.json"
echo "  [OK] .env generated for $SITE_URL"

echo "=== H4f: restart after install.py + .env changes ==="
sudo supervisorctl reread
sudo supervisorctl update
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
sudo supervisorctl restart frappe-bench-ce-sri-svc || true
sudo nginx -t && sudo systemctl reload nginx || true
echo "  [OK] services restarted after install.py"

{tls_section}
echo "=== L0: deploy stop.py ==="
cp /tmp/rendered/stop.py $BENCH_DIR/stop.py
chown $ERP_USER:$ERP_USER $BENCH_DIR/stop.py
chmod 755 $BENCH_DIR/stop.py
echo "  [OK] stop.py deployed to $BENCH_DIR"

echo "=== L: render bash_aliases (VM-side — needs DB_NAME from site_config.json) ==="
DB_NAME=$(python3 -c "import json; print(json.load(open('$BENCH_DIR/sites/$SITE_URL/site_config.json'))['db_name'])" 2>/dev/null || echo "unknown_db")
python3 /tmp/renderers/render_bash_aliases.py \\
  --template /tmp/templates/bash_aliases.j2 \\
  --params /tmp/rendered/params.json \\
  --output /home/$ERP_USER/.bash_aliases \\
  --extra db_name="$DB_NAME"
chown $ERP_USER:$ERP_USER /home/$ERP_USER/.bash_aliases
echo "  [OK] .bash_aliases rendered for $ERP_USER"

echo "=== Done ==="
"""

        script_local = PLATFORMS_KVM / f"{vm.hostname}-differentiate.sh"
        script_local.write_text(differentiate_sh)
        r = subprocess.run(
            ["scp"] + scp_opts + [str(script_local), f"you@{vm.virbr0_ip}:/tmp/differentiate.sh"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            raise RuntimeError(f"scp differentiate.sh failed: {r.stderr.strip()}")
        emit(f"  [OK] differentiate.sh deployed")

        # ── Step 13: Execute differentiate.sh on VM (streaming) ───────────────
        emit("── Step 13: Execute differentiate.sh (~25 min) ──")
        proc = subprocess.Popen(
            target_ssh + ["sudo bash /tmp/differentiate.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

        )
        for line in _stream_lines(proc.stdout):
            emit(line)
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"differentiate.sh failed (exit {proc.returncode})")
        emit("  [OK] Differentiation complete")

        # ── Step 14: Final snapshot — Logichem DB Restored ───────────────────
        emit("── Step 14: Snapshot — ERPNext v13 Logichem DB Restored ──")
        r = subprocess.run(
            ["ssh", TOSHIBA_ALIAS,
             f"virsh --connect qemu:///system snapshot-create-as {vm.hostname} "
             f"'ERPNext v13 Logichem DB Restored' --atomic"],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            emit(f"  [WARN] Snapshot failed: {r.stderr.strip()}")
        else:
            emit("  [OK] Snapshot 'ERPNext v13 Logichem DB Restored' taken")

        job["status"] = "done"
        proto = "https" if have_cert else "http"
        emit(f"── Differentiation complete — ERPNext at {proto}://{site_url} ──")

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
    """Re-SCP and re-run the saved {hostname}-differentiate.sh on the VM (idempotent)."""
    script = PLATFORMS_KVM / f"{hostname}-differentiate.sh"
    if not script.exists():
        raise HTTPException(
            404,
            f"No differentiate script for '{hostname}' — provision via ERPNext template first",
        )
    data = load_hosts_map()
    kvm  = data["groups"].get("kvm", {})
    if hostname not in kvm:
        raise HTTPException(404, f"'{hostname}' not found in hosts_map.yml")
    wg_ip = kvm[hostname].get("wg_ip", "")
    if not wg_ip:
        raise HTTPException(400, f"No WireGuard IP configured for '{hostname}'")

    host_cfg = kvm[hostname]

    job_id       = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "log": [], "hostname": hostname}
    threading.Thread(
        target=_run_refresh,
        args=(job_id, hostname, wg_ip, script, host_cfg),
        daemon=True,
    ).start()
    return {"job_id": job_id}


def _run_refresh(job_id: str, hostname: str, wg_ip: str, script: Path, host_cfg: dict):
    job = jobs[job_id]

    def _ts():
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def emit(line: str):
        stamped = f"[{_ts()}] {line}"
        job["log"].append(stamped)
        print(f"[job {job_id}] {stamped}", flush=True)

    try:
        ssh_opts      = ["-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        remote_script = f"/tmp/{hostname}-differentiate.sh"

        emit(f"── Refresh: uploading differentiate.sh to {hostname} ({wg_ip}) ──")
        r = subprocess.run(
            ["scp"] + ssh_opts + [str(script), f"you@{wg_ip}:{remote_script}"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            raise RuntimeError(f"SCP failed: {r.stderr.strip()}")
        emit("  [OK] script uploaded")

        emit("── Uploading controller pubkey ──")
        controller_pubkey_path = Path.home() / ".ssh" / "hasan_mighty.pub"
        if controller_pubkey_path.exists():
            r = subprocess.run(
                ["scp"] + ssh_opts + [str(controller_pubkey_path), f"you@{wg_ip}:/tmp/hasan_mighty.pub"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                emit(f"  [WARN] scp hasan_mighty.pub failed: {r.stderr.strip()} — continuing")
            else:
                emit("  [OK] hasan_mighty.pub uploaded")
        else:
            emit("  [SKIP] controller pubkey not found")

        emit("── Uploading ddlViews.sql ──")
        if VIEWS_DDL_SRC.exists():
            r = subprocess.run(
                ["scp"] + ssh_opts + [str(VIEWS_DDL_SRC), f"you@{wg_ip}:/tmp/ddlViews.sql"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                emit(f"  [WARN] scp ddlViews.sql failed: {r.stderr.strip()} — continuing")
            else:
                emit("  [OK] ddlViews.sql uploaded")
        else:
            emit(f"  [SKIP] ddlViews.sql not found at {VIEWS_DDL_SRC}")

        # App code sync handled by differentiate.sh section A2d (git pull from GitHub)

        # ── Render + upload config bundle (same artifacts as provision Step 12) ──
        emit("── Rendering + uploading config bundle ──")
        nickname_str = host_cfg.get("nickname", hostname[:4])
        groups = host_cfg.get("ansible_groups", [])
        if "production" in groups:
            zone_key = "production"
        elif "staging" in groups:
            zone_key = "staging"
        else:
            zone_key = "development"
        domain = ZONE_DOMAINS.get(zone_key, "iridium.blue")
        site_url = f"{hostname}.{domain}"
        bench_name_new = f"frappe-bench-{nickname_str}"
        with open(GROUP_VARS_ALL) as _f:
            ERP_USER = yaml.safe_load(_f).get("erp_user", "erpadm")
        bench_dir = f"/home/{ERP_USER}/{bench_name_new}"
        ERP_USER_PWD = "sasa"
        MYPWD = "erpnext_build"

        # SCP ce_sri secrets (P12 cert, ce_sri_parms.json, logo) to /tmp/ on VM
        emit("── Uploading ce_sri secrets (SOPS → decrypt → patch → SCP) ──")
        _scp_cesri_secrets(
            emit, ssh_opts, wg_ip,
            site_url, nickname_str, ERP_USER,
        )

        tls_domain = "iridium.blue"
        cert_dir = f"/etc/nginx/certs/{tls_domain}"
        gunicorn_port = 8000
        ws_port = 9000

        render_params = {
            "erp_user": ERP_USER, "erp_user_pwd": ERP_USER_PWD, "mypwd": MYPWD,
            "hostname": hostname,
            "tld": domain.split(".", 1)[1] if "." in domain else domain,
            "site_url": site_url, "nickname": nickname_str,
            "bench_name_new": bench_name_new, "bench_dir": bench_dir,
            "gunicorn_port": gunicorn_port, "ws_port": ws_port,
            "nginx_cert": f"{cert_dir}/fullchain.pem",
            "nginx_key": f"{cert_dir}/privkey.pem",
            "nginx_dhparam": "/etc/nginx/dhparam.pem",
        }

        from tools.renderers.render_envars import render as r_envars
        from tools.renderers.render_supervisor import render as r_supervisor
        from tools.renderers.render_gh_askpass import render as r_askpass
        from tools.renderers.render_nginx_vhost import render as r_nginx

        rendered_dir = Path(tempfile.mkdtemp(prefix="esacp-refresh-"))
        r_envars(render_params, output_path=rendered_dir / "envars.sh")
        r_supervisor(render_params, output_path=rendered_dir / "ce_sri_svc_supervisor.conf")
        r_askpass(render_params, output_path=rendered_dir / "gh_askpass.sh")
        r_nginx(render_params, output_path=rendered_dir / "nginx_vhost.conf")

        shutil.copy(PLATFORMS_KVM / "static" / "Procfile", rendered_dir / "Procfile")
        shutil.copy(PLATFORMS_KVM / "static" / "ssh_config", rendered_dir / "ssh_config")
        shutil.copy(PLATFORMS_KVM / "stop.py", rendered_dir / "stop.py")
        (rendered_dir / "params.json").write_text(json.dumps(render_params, indent=2))

        rsync_e = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"
        for local_dir, remote_path in [
            (str(rendered_dir) + "/", "/tmp/rendered/"),
            (str(PROJECT_ROOT / "tools" / "renderers") + "/", "/tmp/renderers/"),
            (str(PROJECT_ROOT / "tools" / "vm_scripts") + "/", "/tmp/vm_scripts/"),
            (str(PLATFORMS_KVM / "templates") + "/", "/tmp/templates/"),
        ]:
            r = subprocess.run(
                ["rsync", "-a", "-e", rsync_e,
                 local_dir, f"you@{wg_ip}:{remote_path}"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                raise RuntimeError(f"rsync {remote_path} failed: {r.stderr.strip()}")
        shutil.rmtree(rendered_dir, ignore_errors=True)
        emit(f"  [OK] config bundle + renderers + templates + vm_scripts deployed")

        emit("── Running differentiate.sh (idempotent) ──")
        proc = subprocess.Popen(
            ["ssh"] + ssh_opts + [f"you@{wg_ip}", f"sudo bash {remote_script}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        for line in _stream_lines(proc.stdout):
            emit(line)
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"differentiate.sh exited {proc.returncode}")

        emit("── Refresh complete ──")
        job["status"] = "done"

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


def _get_cf_token() -> str:
    """Decrypt all.sops.yml and return the cloudflare_acme_token."""
    dec = subprocess.run(
        ["sops", "-d", str(GROUP_VARS_ALL_SOPS)],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        raise RuntimeError(f"sops decrypt failed: {dec.stderr.strip()}")
    data = yaml.safe_load(dec.stdout)
    token = data.get("cloudflare_acme_token", "")
    if not token:
        raise RuntimeError("cloudflare_acme_token not found in all.sops.yml")
    return token


def _cf_dns_upsert(record_name: str, ip: str, emit) -> None:
    """Create or update a Cloudflare DNS A record for record_name → ip.

    record_name: e.g. 'dev01' → creates 'dev01.iridium.blue'
    ip: WireGuard IP (10.10.0.x) — accessible to WireGuard peers only
    """
    import urllib.request
    import urllib.error

    token = _get_cf_token()
    fqdn  = f"{record_name}.iridium.blue"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    base_url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID_IRIDIUM}/dns_records"

    # List existing records matching name
    list_url = f"{base_url}?type=A&name={fqdn}"
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            existing = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Cloudflare list DNS failed: {exc.code} {exc.read().decode()}")

    records = existing.get("result", [])
    body = json.dumps({"type": "A", "name": fqdn, "content": ip, "ttl": CF_DNS_TTL, "proxied": False}).encode()

    if records:
        record_id = records[0]["id"]
        existing_ip = records[0].get("content", "")
        if existing_ip == ip:
            emit(f"  [OK] DNS {fqdn} → {ip} already up to date")
            return
        put_url = f"{base_url}/{record_id}"
        req = urllib.request.Request(put_url, data=body, headers=headers, method="PUT")
        action = "Updated"
    else:
        req = urllib.request.Request(base_url, data=body, headers=headers, method="POST")
        action = "Created"

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Cloudflare DNS upsert failed: {exc.code} {exc.read().decode()}")

    if not result.get("success"):
        raise RuntimeError(f"Cloudflare DNS upsert failed: {result.get('errors')}")
    emit(f"  [OK] {action} DNS A record: {fqdn} → {ip} (TTL {CF_DNS_TTL}s)")


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
