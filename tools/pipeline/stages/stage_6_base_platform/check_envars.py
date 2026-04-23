#!/usr/bin/env python3
"""Stage 6 envars-related checks (sections A and C)."""

from __future__ import annotations

from tools.pipeline.stages.stage_6_base_platform.check_ssh import ssh_vm


def _envars_paths(provision_mode: str) -> tuple[str, str]:
    """Return (present_path, absent_path_prefix) for the mode."""
    if provision_mode == "generic":
        return "/opt/generic/envars.sh", "/opt/ce_sri"
    return "/opt/ce_sri/envars.sh", "/opt/generic"


def check_envars_deployed(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    provision_mode: str = "restored",
) -> tuple[bool, str]:
    """Section A: envars.sh at mode-specific path; other path absent."""
    present, absent = _envars_paths(provision_mode)
    r = ssh_vm(target_ip, ssh_opts, ssh_key,
               f"test -f {present} && ! test -e {absent} && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"{present} deployed; {absent} absent"
    return False, f"envars placement wrong (want {present}, no {absent})"


def check_bare_symlink(
    target_ip: str, ssh_opts: list[str], ssh_key: str,
    bench_dir: str, provision_mode: str = "restored",
) -> tuple[bool, str]:
    """Section C: BaRe/envars.sh -> mode-specific target."""
    target, _ = _envars_paths(provision_mode)
    r = ssh_vm(
        target_ip, ssh_opts, ssh_key,
        f"test -L {bench_dir}/BaRe/envars.sh"
        f" && [ \"$(readlink {bench_dir}/BaRe/envars.sh)\" = \"{target}\" ]"
        " && echo y")
    if r.returncode == 0 and "y" in r.stdout:
        return True, f"BaRe/envars.sh -> {target}"
    return False, f"BaRe/envars.sh not linked to {target}"
