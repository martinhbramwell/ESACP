# saconsole compute-resource spec (v0)

> **What this document is.** Reference data for the Beaverdam Mode-A
> advisor. When the advisor needs to decide whether the operator's
> environment can **host saconsole** (and the sibling VMs it manages),
> it fetches this sheet and reads off the concrete resource figures
> below. Not operator-facing prose; it is the source the advisor
> reasons from. A competent reader — human or AI — should be able to
> look at a given machine or hosting plan and this sheet and decide
> *yes / no / with-caveats*.

---

## 1. What saconsole is

saconsole is the **management VM** — the "rope" in the shoe → string →
rope → chain metaphor. The controller bootstraps it; thereafter
saconsole manages every sibling VM (the ERPNext targets — the "chain").
It is the long-lived institutional centre of the lab.

Sizing has **two layers**, and the advisor must keep them separate:

- **Layer A — saconsole itself**: a fixed, modest footprint (below).
- **Layer B — the host that runs saconsole + its target VMs**: the real
  constraint. The host must have headroom for saconsole *plus* however
  many ERPNext target VMs the operator will run.

## 2. saconsole's own footprint (Layer A)

| Resource | Requirement | Notes |
|---|---|---|
| **vCPU** | 2 | From the live build (`virt-install --vcpus 2`). |
| **RAM** | 4 GiB | Live baseline; confirmed running at 4 GiB. |
| **Disk** | 20 GB (qcow2, thin-provisioned) | Grows toward the cap as used; start budget 20 GB. |
| **Network** | 1 NIC on a NAT/bridged network | Live build uses libvirt's `default` NAT network; bridged also valid. |
| **OS** | Xubuntu 24.04 (desktop) | Provisioned via autoinstall. |

## 3. Host requirements (Layer B — the real constraint)

The machine (or hosting plan) that runs saconsole must provide:

| Requirement | Detail |
|---|---|
| **Hardware virtualization** | KVM/libvirt on Linux (Intel VT-x / AMD-V enabled). A nested-virt-capable cloud instance also works. |
| **"May I run my own programs?"** | The hosting service **must permit installing and running arbitrary programs / VMs.** Shared web hosting (cPanel-style) and most managed-app platforms do **not** qualify. A VPS / dedicated server / own hardware does. |
| **RAM headroom** | ≥ saconsole's 4 GiB **plus** each target VM. An ERPNext target is ~2 GiB. So a one-target lab needs ~8 GiB usable; a two-target lab ~10 GiB; leave ~2 GiB for the host OS. |
| **Disk headroom** | ≥ 20 GB (saconsole) **plus** ~20 GB per target VM. A one-target lab budgets ~50 GB; size up per target. |
| **Network** | Outbound internet. Remote hosts join the lab over a WireGuard mesh; a single NAT'd host needs no inbound ports. |

## 4. Where saconsole can live

Three viable shapes, in rising order of resource:

1. **Same machine as the controller** — only if that machine is Linux
   with KVM and enough headroom (Layer B). A Windows/WSL2 controller
   **cannot** host saconsole directly; WSL2 does not provide nested KVM
   for this use. Such an operator needs a separate Linux host.
2. **A second local Linux box** (the common lab shape: a spare
   desktop/server acts as the hypervisor; the controller talks to it).
3. **A remote VPS / cloud instance** that permits virtualization, joined
   over WireGuard. Gated on a provider that allows running your own VMs.

## 5. Convergence checklist (what the advisor decides)

Given a candidate host, saconsole-hosting is viable when **all** hold:

1. Linux with KVM/libvirt available (or a nested-virt cloud instance).
2. The hosting arrangement **permits running your own programs/VMs**.
3. Usable RAM ≥ 4 GiB + (2 GiB × planned targets) + ~2 GiB host overhead.
4. Usable disk ≥ 20 GB + (~20 GB × planned targets).
5. Outbound internet (WireGuard handles remote reachability).

If a candidate fails only on "may I run my own programs" (e.g. shared
hosting), the advisor steers toward a VPS or a local Linux box rather
than recording a hard no. The most common real-world split: a
Windows/WSL2 controller **plus** a separate Linux machine (local or
VPS) as the saconsole host.
