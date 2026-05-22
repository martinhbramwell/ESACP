# frappe_substrate_v16

V16-era frappe substrate prereqs — installs Python 3.14, Node 24, and
pkg-config on hosts whose `hosts_map.yml` declares `target_frappe_major >= 16`.
No-op on V13/V14/V15 targets.

## Why this role exists (ESACP#445)

The S74 V14-trial-extension probe established the V16 substrate distance
(see `internal_docs/SessionLogs/2026-05-22-v14-trial-notes.md` § Extension 3):

| Surface | Packer-baked v13 image | V16 frappe pin |
|---|---|---|
| Python | 3.10.12 | **3.14.x** (`requires-python = ">=3.14,<3.15"`) |
| Node | 18.20.8 | **24.x** (`engines.node = ">=24"`) |
| `pkg-config` | absent | required by pip install |

The packer template is still v13-era; rebuilding it for the V16 era is a
separate session per S75 agenda. This role provides a forward-compatible
overlay so V16-target VMs can be brought to substrate-ready state without
waiting on the packer template refresh.

## Scope

In:
- `python3.14` + `python3.14-dev` + `python3.14-venv` (deadsnakes PPA on 22.04)
- `nodejs` ≥ 24 (NodeSource setup_24.x)
- `pkg-config`
- Idempotent: skips Node setup if `node --version` already ≥ 24.

Out (separate issues / sessions):
- Rebuilding the bench venv on Python 3.14 (substrate migration territory).
- `returnable`'s pypika URL-dep crash (E9 — bespoke-app pattern fix).
- `erpnext.patches.v16_0.make_workstation_operating_components` defect
  (ESACP#444).
- Packer-template refresh (multi-session work, separate plan).

## Acceptance

Role's final task asserts:
1. `python3.14 --version` matches `^Python 3.14.`
2. `node --version` major ≥ 24.
3. `pkg-config --version` returns non-empty.

To run against a single target:

```
ansible-playbook -i ansible/inventory/kvm.yml ansible/site-kvm.yml \
  --limit dev02 --tags frappe_substrate_v16
```

(Role is wired into Play 4 with `tags: [frappe_substrate_v16]`.)

## Variables

See `defaults/main.yml`. The role keys off `target_frappe_major` —
declared per-host in `hosts_map.yml` and surfaced as a hostvar by
`tools/generate_inventory.py`. Defaults to `13` when absent.
