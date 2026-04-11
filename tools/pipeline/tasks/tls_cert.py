"""Distribute wildcard TLS cert from saconsole to target VM."""

from __future__ import annotations

from tools.pipeline.ssh import saconsole_ssh_run, ssh_run
from tools.pipeline.types import Config, Emit, TaskResult

ACME_CERT_HOME = "/opt/acme-certs"
DOMAIN = "iridium.blue"
CERT_DIR = f"{ACME_CERT_HOME}/{DOMAIN}"

PEM_MAP = [
    ("fullchain.pem", "fullchain.pem"),
    ("key.pem",       "privkey.pem"),
    ("cert.pem",      "cert.pem"),
]


def _cert_exists_on_vm(config: Config) -> bool:
    r = ssh_run(config,
                "test -f /etc/nginx/certs/iridium.blue/fullchain.pem && echo y",
                timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def _cert_exists_on_saconsole(config: Config) -> bool:
    r = saconsole_ssh_run(config,
                          f"test -f {CERT_DIR}/fullchain.pem && echo found")
    return "found" in r.stdout


def _push_pem(config: Config, pem_name: str, tmp_name: str) -> None:
    read = saconsole_ssh_run(config, f"cat {CERT_DIR}/{pem_name}")
    if read.returncode != 0:
        raise RuntimeError(f"Failed to read {pem_name} from saconsole")
    import subprocess
    write = subprocess.run(
        ["ssh", *config.ssh_opts, "-i", config.ssh_key,
         f"you@{config.target_ip}",
         f"sudo tee /tmp/{tmp_name} > /dev/null"],
        input=read.stdout.encode(), capture_output=True, timeout=15,
    )
    if write.returncode != 0:
        raise RuntimeError(f"Failed to write {tmp_name} to VM")


def ensure_tls_cert(config: Config, emit: Emit) -> TaskResult:
    """Copy wildcard PEM files from saconsole → VM /tmp/."""
    if _cert_exists_on_vm(config):
        return TaskResult(True, False, "TLS cert already on VM")
    if not _cert_exists_on_saconsole(config):
        emit("  [WARN] Cert not on saconsole — skipping (HTTP-only)")
        return TaskResult(True, False, "No cert on saconsole")
    try:
        for pem_name, tmp_name in PEM_MAP:
            _push_pem(config, pem_name, tmp_name)
    except RuntimeError as exc:
        return TaskResult(False, False, str(exc))
    return TaskResult(True, True, "Cert files → /tmp/ on VM")
