"""Distribute wildcard TLS cert from the hub to target VM."""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import hub_ssh_run, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

ACME_CERT_HOME = "/opt/acme-certs"

PEM_MAP = [
    ("fullchain.pem", "fullchain.pem"),
    ("key.pem",       "privkey.pem"),
    ("cert.pem",      "cert.pem"),
]


def _cert_dir_on_hub(config: Config) -> str:
    return f"{ACME_CERT_HOME}/{config.domain}"


def _cert_exists_on_vm(config: Config) -> bool:
    r = ssh_run(config,
                f"test -f /etc/nginx/certs/{config.domain}/fullchain.pem && echo y",
                timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def _cert_exists_on_hub(config: Config) -> bool:
    cert_dir = _cert_dir_on_hub(config)
    r = hub_ssh_run(config,
                    f"test -f {cert_dir}/fullchain.pem && echo found")
    return "found" in r.stdout


def _push_pem(config: Config, pem_name: str, tmp_name: str) -> None:
    cert_dir = _cert_dir_on_hub(config)
    read = hub_ssh_run(config, f"cat {cert_dir}/{pem_name}")
    if read.returncode != 0:
        raise RuntimeError(f"Failed to read {pem_name} from hub")
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
    """Copy wildcard PEM files from the hub → VM /tmp/."""
    if _cert_exists_on_vm(config):
        return TaskResult(True, False, "TLS cert already on VM")
    if not _cert_exists_on_hub(config):
        emit("  [WARN] Cert not on hub — skipping (HTTP-only)")
        return TaskResult(True, False, "No cert on hub")
    try:
        for pem_name, tmp_name in PEM_MAP:
            _push_pem(config, pem_name, tmp_name)
    except RuntimeError as exc:
        return TaskResult(False, False, str(exc))
    return TaskResult(True, True, "Cert files → /tmp/ on VM")
