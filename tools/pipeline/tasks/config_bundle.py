"""Render config artifacts and deploy bundle to target VM."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from tools.pipeline.ssh import rsync_to_vm, scp_to_vm
from tools.pipeline.types import Config, Emit, TaskResult


def _build_render_params(config: Config) -> dict:
    domain = config.domain
    tls_domain = "iridium.blue"
    cert_dir = f"/etc/nginx/certs/{tls_domain}"
    return {
        "erp_user": config.erp_user,
        "erp_user_pwd": config.erp_user_pwd,
        "mypwd": config.db_root_pwd,
        "hostname": config.hostname,
        "tld": domain.split(".", 1)[1] if "." in domain else domain,
        "site_url": config.site_url,
        "nickname": config.nickname,
        "bench_name_new": f"frappe-bench-{config.nickname}",
        "bench_dir": config.bench_dir,
        "gunicorn_port": 8000,
        "ws_port": 9000,
        "nginx_cert": f"{cert_dir}/fullchain.pem",
        "nginx_key": f"{cert_dir}/privkey.pem",
        "nginx_dhparam": "/etc/nginx/dhparam.pem",
    }


def _render_artifacts(params: dict, rendered_dir: Path) -> None:
    from tools.renderers.render_envars import render as r_envars
    from tools.renderers.render_supervisor import render as r_supervisor
    from tools.renderers.render_gh_askpass import render as r_askpass
    from tools.renderers.render_nginx_vhost import render as r_nginx

    r_envars(params, output_path=rendered_dir / "envars.sh")
    r_supervisor(params, output_path=rendered_dir / "ce_sri_svc_supervisor.conf")
    r_askpass(params, output_path=rendered_dir / "gh_askpass.sh")
    r_nginx(params, output_path=rendered_dir / "nginx_vhost.conf")


def _copy_statics(project_root: Path, rendered_dir: Path) -> None:
    kvm_static = project_root / "platforms" / "kvm" / "static"
    kvm_dir = project_root / "platforms" / "kvm"
    shutil.copy(kvm_static / "Procfile", rendered_dir / "Procfile")
    shutil.copy(kvm_static / "ssh_config", rendered_dir / "ssh_config")
    shutil.copy(kvm_dir / "stop.py", rendered_dir / "stop.py")


def render_and_deploy_config(config: Config, emit: Emit) -> TaskResult:
    """Render config artifacts, rsync bundle + support dirs to VM."""
    project = Path(config.project_root)
    params = _build_render_params(config)

    rendered_dir = Path(tempfile.mkdtemp(prefix="esacp-rendered-"))
    try:
        _render_artifacts(params, rendered_dir)
        _copy_statics(project, rendered_dir)
        (rendered_dir / "params.json").write_text(
            json.dumps(params, indent=2))
        count = len(list(rendered_dir.iterdir()))
        emit(f"  {count} config artifacts rendered")

        dirs = [
            (str(rendered_dir) + "/", "/tmp/rendered/"),
            (str(project / "tools" / "renderers") + "/", "/tmp/renderers/"),
            (str(project / "tools" / "vm_scripts") + "/", "/tmp/vm_scripts/"),
            (str(project / "platforms" / "kvm" / "templates") + "/",
             "/tmp/templates/"),
        ]
        for local_dir, remote_path in dirs:
            r = rsync_to_vm(config, local_dir, remote_path, timeout=30)
            if r.returncode != 0:
                return TaskResult(False, False,
                                  f"rsync {remote_path}: {r.stderr.strip()}")
        emit("  bundle + renderers + templates + vm_scripts deployed")

        isp = str(project / "tools" / "install_specific.py")
        r = scp_to_vm(config, [isp], "/tmp/", timeout=15)
        if r.returncode != 0:
            emit(f"  [WARN] SCP install_specific.py failed: {r.stderr.strip()}")
        else:
            emit("  install_specific.py → /tmp/")
    finally:
        shutil.rmtree(rendered_dir, ignore_errors=True)

    return TaskResult(True, True, "Config bundle deployed")
