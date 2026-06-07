"""Pydantic request models shared across route modules."""

from __future__ import annotations

from pydantic import BaseModel

from tools.host_identity import DEFAULT_HYPERVISOR


class BuildTemplateReq(BaseModel):
    """Which frappe/erpnext line to build (dual-template; ESACP #631)."""
    frappe_branch:  str = "version-13"
    erpnext_branch: str = "version-13"


class NewHost(BaseModel):
    hostname:   str
    nickname:   str = ""
    virbr0_ip:  str
    wg_ip:      str
    backend:    str = "kvm"
    hypervisor: str = DEFAULT_HYPERVISOR
    zone:       str = "development"
    vm_role:    str = "dev"


class NewErpnextVM(BaseModel):
    hostname:   str
    nickname:   str = ""
    virbr0_ip:  str
    wg_ip:      str
    hypervisor: str = DEFAULT_HYPERVISOR
    zone:       str = "development"
    vm_role:    str = "dev:unspecified"


class NewGenericErpnextVM(BaseModel):
    hostname:    str
    nickname:    str = ""
    virbr0_ip:   str
    wg_ip:       str
    hypervisor:  str = DEFAULT_HYPERVISOR
    zone:        str = "development"
    vm_role:     str = "dev:unspecified"
    wizard_mode: str = "record"
    wizard_arg:  str = ""
