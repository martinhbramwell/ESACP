# 2026-06-03 1139 — Session 100 minutes

> Reconstructed post-hoc: S100 died after the substantive work landed but **before** SCC
> (no minutes, no next-agenda were written). All code work is captured in merged PR #582;
> nothing was lost. This file + the S101 agenda are the deferred close.

## Stated objective

**#567 bundle** — derive operator SSH identity from config. Root-cause pass over the
hardcoded-operator-SSH-identity class (`~/.ssh/hasan_mighty[.pub]`, `hasan@` literals baked
into pipeline / orchestration / CLI instead of sourced from config). Substantive 1:1:1.

## Pre-flight

- Branch at start: `main`, clean, tip `057b315` (S99-close S100-agenda seed).
- Open issues at start: ESACP **74** forecast (per S100 agenda), LSKB **12**.

## What happened

### Single source of truth + resolver (PR #582, branch `refactor/567-operator-ssh-identity`)

- **`hosts_map.yml`**: new `groups.controller.local.hypervisor_user` field — the operator's
  login on the bare-metal hypervisor (`$USER` fallback).
- **`tools/host_identity.py`**: three resolvers — `operator_ssh_key()` (reads
  `ansible/group_vars/kvm.yml` `ansible_ssh_private_key_file`), `operator_pubkey()` (= key + `.pub`),
  `hypervisor_user()` (reads the new `hosts_map` field). Documented home for the values; all other
  sites import from here.
- **`generate_inventory.py`**: derives the ProxyJump user via `hypervisor_user()`.
- **`tools/cli/_common.py:ssh_key_path()`**: delegates to the resolver (dedup; removed duplicate
  group_vars-reading logic + unused `import os`).

### Scope decision (operator)

Operator identity **only** — the key, the pubkey, and the hypervisor ProxyJump user. The guest VM
user (`you@`) is a distinct identity and was deliberately left for a separate 1:1:1.

### No behavioral change

Regenerated `ansible/inventory/kvm.yml` is **byte-identical** (derived value == old literal). No VM
ops ran; dev01/dev02/saconsole untouched.

### Intentional residuals (documented in the commit, not violations)

- `host_identity.py` keeps one `~/.ssh/hasan_mighty` default inside `operator_ssh_key()` — the
  SSoT's single code-side default.
- `section_a2e_controller_pubkey.sh` keeps `/tmp/hasan_mighty.pub` — the key *filename* convention is
  explicitly out of scope per #396.

### size_baselines.json

Four +1/+2 import-only bumps (`verify_build_vm` 80→81, `stage_1` verify 131→133, `stage_3` verify
134→135, `_test_helpers` 40→42; zero logic accretion, S84 precedent); two auto-tightened downward from
removed imports (`config` 60→58, `controller_pubkey` 42→41).

## Deliverables

- **PR #582 merged** (`mergedAt` 2026-06-03T15:30:44Z, merge commit `b29d14d`) — closed **#567**,
  **#396**, **#451** (all auto-closed at merge instant).
- **#580** filed — `verify_build_vm.py` at 81 lines, 1 over the 80-line pipeline cap (consequence of
  the import-only bump; tracked for decomposition, not a regression).
- **#581** filed — `ssh_key_path(config)` ignores its `config` param after the #567 delegation; remove
  the dead param once all callers are updated.

## Close state

- Open ESACP issues: **73** (74 − 3 closed + 2 filed = 73 ✓). LSKB **12**. Siblings: ce_sri 5 /
  ce_sri_svc 2 / BaRe 2 / LSV 2.
- Branch `refactor/567-operator-ssh-identity` kept (no prune).
- `main` clean at tip `b29d14d`.
