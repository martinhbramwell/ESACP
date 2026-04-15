# Session Minutes — 2026-04-15 19:00

**Objective:** Fix #179 — Ansible `hub_key` parse-time failure

**Branch:** `fix/179-ansible-hub-hosts-directive` (merged to main via PR #184)

---

## Completed

### Step 1: Diagnose hub_key parse failure (#179)
- `site-kvm.yml` Play 2 used `hosts: "{{ hub_key }}"` — Ansible evaluates `hosts:` at parse time, before `group_vars/all.yml` is loaded
- Introduced by PR #176 (issue #171) which replaced literal `saconsole` with the variable
- Play 3's `hostvars[hub_key]` references are fine — task-level Jinja2, evaluated at runtime

### Step 2: Fix — inventory group approach
- `generate_inventory.py`: auto-creates a `hub` inventory group from hosts with `wg_role=hub`
- `site-kvm.yml`: Play 2 now uses `hosts: hub` (inventory group, available at parse time)
- Regenerated `ansible/inventory/kvm.yml` — new `hub` group with saconsole as sole member
- `ansible-playbook --syntax-check` passes (previously failed with `'hub_key' is undefined`)

### Step 3: PR and merge
- PR #184 created and merged to main (commit `6e98fad`, merge `6acdc7b`)
- Issue #179 closed automatically

## Open Issues (9)

| Priority | Issue | Title |
|---|---|---|
| Bug | #178 | SSH config for saconsole — unroutable hostname + stale host key |
| Enhancement | #181 | Parameterise Playwright recordings |
| Infra | #50 | cf-mcp-refresh not in repo/docs |
| Infra | #153 | Register Google OAuth redirect URIs for staging |
| Infra | #138 | saconsole phone-home agent |
| Decision | #48 | Registrar credentials backup |
| Decision | #65 | Auth architecture for control plane |
| Nice-to-have | #156 | saconsole on recycled Android tablet |
| Nice-to-have | #157 | WireGuard self-enrollment via staging slave |

## Not Done
- Nothing deferred — objective fully completed
