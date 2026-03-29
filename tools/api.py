"""ESACP Control Plane API — prototype

Runs on localhost:8088. Proxied from Vite dev server at /api.

Start (from project root):
    uvicorn tools.api:app --port 8088 --reload

Endpoints:
    GET  /api/hosts                  → current KVM hosts + IP suggestions
    POST /api/hosts/add              → add host to hosts_map.yml, regen inventory
    POST /api/provision/{hostname}   → start background job: cloud-init + WG + buildVM + provisionVM
    GET  /api/jobs/{job_id}          → poll job status + log lines
"""

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

# Logichem bespoke app sources (controller-local)
LOGICHEM_DIR       = Path.home() / "projects" / "Logichem"
CE_SRI_SRC         = LOGICHEM_DIR / "ce_sri_prod"
RETURNABLE_SRC     = LOGICHEM_DIR / "returnable_prod"
ROUTE_PLANNER_SRC  = LOGICHEM_DIR / "route_planner_prod"
BARE_SRC           = LOGICHEM_DIR / "BaRe"
BKP_SRC            = LOGICHEM_DIR / "ce_sri" / "BKP"
VIEWS_DDL_SRC      = LOGICHEM_DIR / "ce_sri" / "example_srvr_files" / "views.ddl"

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

        hosts.append({
            "id":            name,
            "hostname":      h.get("hostname", name),
            "nickname":      h.get("nickname", ""),
            "virbr0_ip":     h.get("virbr0_ip", ""),
            "wg_ip":         h.get("wg_ip", ""),
            "wg_role":       h.get("wg_role", "spoke"),
            "backend":       h.get("backend", "kvm"),
            "provisioned":   provisioned,
            "ansible_groups": h.get("ansible_groups", []),
            "vm_role":       h.get("vm_role", "dev"),
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

    def emit(line: str):
        if job["log"] and any(line.endswith(s) for s in _COMPACT_SUFFIXES):
            if any(job["log"][-1].endswith(s) for s in _COMPACT_SUFFIXES):
                job["log"][-1] = line   # update in-place — no new entry
                print(f"[job {job_id}] {line}", flush=True)
                return
        job["log"].append(line)
        print(f"[job {job_id}] {line}", flush=True)

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

    if vm.hostname in kvm:
        raise HTTPException(409, f"'{vm.hostname}' already exists in the kvm group")
    for name, h in kvm.items():
        if h.get("wg_ip") == vm.wg_ip:
            raise HTTPException(409, f"WireGuard IP {vm.wg_ip} already used by '{name}'")
        if h.get("virbr0_ip") == vm.virbr0_ip:
            raise HTTPException(409, f"virbr0 IP {vm.virbr0_ip} already used by '{name}'")

    # Register immediately so the UI can add the node
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

    threading.Thread(
        target=_run_provision_erpnext,
        args=(job_id, vm),
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


def _run_provision_erpnext(job_id: str, vm: NewErpnextVM):
    job = jobs[job_id]

    def emit(line: str):
        job["log"].append(line)
        print(f"[job {job_id}] {line}", flush=True)

    target_ssh = [
        "ssh",
        "-o", f"ProxyJump={TOSHIBA_ALIAS}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        "-i", str(Path.home() / ".ssh" / "hasan_mighty"),
        f"you@{vm.virbr0_ip}",
    ]

    try:
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

        # ── Step 10: rsync apps + BaRe + BKP (controller → VM) ───────────────
        # rsync into the ORIGINAL bench dir (rename happens inside differentiate.sh)
        # --rsync-path="sudo rsync" because bench/apps is owned by ERP_USER.
        emit("── Step 10: rsync apps + BaRe + BKP ──")
        rsync_targets = [
            (CE_SRI_SRC,         f"{bench_dir_orig}/apps/ce_sri"),
            (RETURNABLE_SRC,     f"{bench_dir_orig}/apps/returnable"),
            (ROUTE_PLANNER_SRC,  f"{bench_dir_orig}/apps/route_planner"),
            (BARE_SRC,           f"{bench_dir_orig}/BaRe"),
            (BKP_SRC,            f"{bench_dir_orig}/BKP"),
        ]
        for src_path, dst in rsync_targets:
            if not src_path.exists():
                emit(f"  [SKIP] {src_path} not found")
                continue
            r = subprocess.run(
                [
                    "rsync", "-a", "--delete",
                    "--exclude=*.egg-info",
                    "--rsync-path=sudo rsync",
                    "-e", rsync_e,
                    f"{src_path}/",
                    f"you@{vm.virbr0_ip}:{dst}/",
                ],
                capture_output=True, text=True, timeout=300,
            )
            if r.returncode != 0:
                raise RuntimeError(f"rsync {src_path.name} failed: {r.stderr.strip()}")
            emit(f"  [OK] {src_path.name} → {dst}")

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

        # ── Step 12: Generate + SCP differentiate.sh ─────────────────────────
        # All on-VM logic lives in this script — no SSH quoting games.
        emit("── Step 12: Deploy differentiate.sh ──")
        # chown paths reference the original bench dir (rename happens in section A2)
        chown_paths = " ".join(
            f"{bench_dir_orig}/apps/{n}" for n in ("ce_sri", "returnable", "route_planner")
        ) + f" {bench_dir_orig}/BaRe {bench_dir_orig}/BKP"
        private_files = f"{bench_dir}/sites/{site_url}/private/files"
        ddl_placement = (
            f"  sudo -u {ERP_USER} cp {ddl_on_vm} {private_files}/ddlViews.sql\n"
            f"  rm -f {ddl_on_vm}\n"
            f"  echo '  [OK] ddlViews.sql placed'\n"
        ) if ddl_on_vm else "  echo '  [SKIP] ddlViews.sql not available'\n"

        # nginx TLS hostname: e.g. dev01 for dev01.iridium.blue
        tls_domain    = "iridium.blue"
        cert_dir      = f"/etc/nginx/certs/{tls_domain}"
        nginx_cert    = f"{cert_dir}/fullchain.pem"
        nginx_key     = f"{cert_dir}/privkey.pem"
        nginx_dhparam = f"/etc/nginx/dhparam.pem"
        # Frappe supervisor/nginx ports (standard single-bench layout)
        gunicorn_port = 8000
        ws_port       = 9000

        if have_cert:
            tls_section = f"""\
echo "=== I: install TLS cert ==="
sudo mkdir -p {cert_dir}
sudo cp /tmp/fullchain.pem {nginx_cert}
sudo cp /tmp/privkey.pem   {nginx_key}
sudo chmod 600 {nginx_key}
sudo rm -f /tmp/fullchain.pem /tmp/privkey.pem /tmp/cert.pem
echo "  [OK] certs installed to {cert_dir}"

echo "=== J: generate nginx config ==="
sudo tee /etc/nginx/sites-available/{site_url} > /dev/null << 'NGINXEOF'
upstream frappe-{bench_name_new}-{site_url} {{
    server 127.0.0.1:{gunicorn_port};
}}
upstream frappe-socketio-{bench_name_new} {{
    server 127.0.0.1:{ws_port};
}}

server {{
    listen 80;
    server_name {site_url};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {site_url};

    ssl_certificate      {nginx_cert};
    ssl_certificate_key  {nginx_key};
    ssl_dhparam          {nginx_dhparam};
    ssl_protocols        TLSv1.2 TLSv1.3;
    ssl_ciphers          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache    shared:SSL:10m;
    ssl_session_timeout  1d;
    ssl_session_tickets  off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    root /home/{ERP_USER}/{bench_name_new}/sites;

    location /assets {{
        try_files $uri =404;
    }}

    location ~ ^/files/.*$ {{
        try_files /{site_url}/public$uri @webserver;
    }}

    location /socket.io {{
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://frappe-socketio-{bench_name_new};
    }}

    location @webserver {{
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Frappe-Site-Name {site_url};
        proxy_set_header X-Use-X-Accel-Redirect True;
        proxy_read_timeout 120;
        proxy_pass http://frappe-{bench_name_new}-{site_url};
    }}

    location / {{
        rewrite ^(.+)/$ $1 permanent;
        try_files /{site_url}/public$uri @webserver;
    }}
}}
NGINXEOF
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
            tls_section = f"""\
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

echo "=== A: /opt/ce_sri/ + envars.sh ==="
sudo mkdir -p /opt/ce_sri
sudo chmod 755 /opt/ce_sri
sudo tee /opt/ce_sri/envars.sh > /dev/null << 'ENVEOF'
#!/usr/bin/env bash
export ERP_USER_PWD="{ERP_USER_PWD}"
export MYPWD="{MYPWD}"
export ERPNEXT_SITE="{vm.hostname}"
export ERPNEXT_DNS="{vm.hostname}"
export ERPNEXT_TLD="{domain.split('.', 1)[1] if '.' in domain else domain}"
export ERPNEXT_DOMAIN="{site_url}"
export ERPNEXT_SITE_URL="{site_url}"
export ERP_USER_NAME="{ERP_USER}"
export ERPNEXT_SITE_NICKNAME="{nickname_str}"
export TARGET_BENCH_NAME="{bench_name_new}"
export TARGET_BENCH="$HOME/{bench_name_new}"
export RESTORE_SITE_CONFIG="no"
export KEEP_SITE_PASSWORD="yes"
ENVEOF
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

echo "=== A3: start bench services (supervisor) ==="
# Packer template never ran 'bench setup supervisor' — do it now before any bench commands
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
# nginx (www-data) must be able to traverse /home/$ERP_USER to serve static assets
sudo chmod o+x /home/"$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"

echo "=== B: fix ownership of rsynced dirs ==="
sudo chown -R "$ERP_USER:$ERP_USER" {chown_paths.replace(bench_dir_orig, "$BENCH_DIR")}
echo "  [OK] ownership -> $ERP_USER"

echo "=== C: BaRe/envars.sh symlink ==="
sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"

echo "=== D: bench new-site + install-app erpnext ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
sudo -u "$ERP_USER" bash -c "
  cd $BENCH_DIR
  bench new-site $SITE_URL \\
    --mariadb-root-password $MYPWD \\
    --admin-password $ERP_USER_PWD
  bench --site $SITE_URL install-app erpnext
"
echo "  [OK] site created, erpnext installed"

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
{ddl_placement}
echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G: handleRestore.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== H: supervisor reload (post-restore) ==="
sudo supervisorctl reread
sudo supervisorctl update
echo "  [OK] supervisor updated"

echo "=== H2: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
echo "  [OK] bench restarted"

echo "=== H3: reset admin password (bench restore overwrites it) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL set-admin-password $ERP_USER_PWD"
echo "  [OK] admin password reset to ERP_USER_PWD"

{tls_section}
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
            target_ssh + ["bash /tmp/differentiate.sh"],
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

    def emit(line: str):
        job["log"].append(line)
        print(f"[job {job_id}] {line}", flush=True)

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

    def emit(line: str):
        job["log"].append(line)
        print(f"[job {job_id}] {line}", flush=True)

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
