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

import re
import shutil
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT   = Path(__file__).parent.parent
PLATFORMS_KVM  = PROJECT_ROOT / "platforms" / "kvm"
CLOUD_INIT_DIR = PLATFORMS_KVM / "cloud-init"
HOSTS_MAP      = PROJECT_ROOT / "hosts_map.yml"
GROUP_VARS_ALL = PROJECT_ROOT / "ansible" / "group_vars" / "all.yml"
KEYS_SOPS      = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"

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

class NewHost(BaseModel):
    hostname:   str
    nickname:   str = ""
    virbr0_ip:  str
    wg_ip:      str
    backend:    str = "kvm"
    hypervisor: str = "toshiba"


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
        f"      ansible_groups:\n"
        f"        - kvm\n"
        f"        - targets\n"
        f"        - development\n"
        f"        - lab\n"
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
                text=True,
            )
            for line in proc.stdout:
                emit(line.rstrip())
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
            text=True,
        )
        for line in proc.stdout:
            emit(line.rstrip())
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
            text=True,
        )
        for line in proc.stdout:
            emit(line.rstrip())
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
