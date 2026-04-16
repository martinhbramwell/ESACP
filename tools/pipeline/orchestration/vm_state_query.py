#!/usr/bin/env python3
"""Query a hypervisor for VM state + provisioned flags in a single SSH call.

`provisioned=True` means the VM has a snapshot whose name contains "baseline"
(the marker placed at the end of Ansible provisioning). `provisioned=False`
means the VM exists on the hypervisor but is in-flight or partial.

Returns ``None`` when the hypervisor is unreachable (any SSH/parse error),
so callers can distinguish "host has no VMs" from "we don't know".
"""

from __future__ import annotations

import subprocess


_REMOTE_SCRIPT = (
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


def query_provisioned(hypervisor: str | None) -> dict[str, dict] | None:
    """Return ``{vm_name: {"provisioned": bool, "vm_state": str}}`` or ``None``.

    One SSH call per hypervisor; the remote shell loops over all VMs.
    """
    try:
        if hypervisor:
            cmd = ["ssh", hypervisor, _REMOTE_SCRIPT]
        else:
            cmd = ["bash", "-c", _REMOTE_SCRIPT]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None
        result: dict[str, dict] = {}
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("provisioned:"):
                state, name = line[len("provisioned:"):].split(":", 1)
                result[name] = {"provisioned": True, "vm_state": state}
            elif line.startswith("exists:"):
                state, name = line[len("exists:"):].split(":", 1)
                result[name] = {"provisioned": False, "vm_state": state}
        return result
    except Exception:
        return None
