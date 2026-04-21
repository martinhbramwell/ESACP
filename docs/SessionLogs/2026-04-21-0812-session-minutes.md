# Session Minutes — Matrix Run 05 UI full company-specific — GREEN

**Date:** 2026-04-21 ~07:00–08:12 EDT
**Branch:** `accept/05-ui-full-company-specific`
**PR:** #266 (merged `9124505` at 2026-04-21T12:12:08Z)
**Issues closed:** #265

## Objective

Execute Matrix Run 05 (UI transport) per agenda — destroy + rebuild dev01 via Cytoscape UI, Playwright-validated, parity partner to Run 02 (CLI).

## Outcome — GREEN

- 1 passed (30.4m).
- Provision job `2b156924` finished after 1767s (29.5m).
- UI convergence 1s.
- Canary: Administrator login + REST `Item/Test Item` + desk page — all pass. Parity with Run 02 confirmed.
- sync_check post-run: 43 ✅ / 14 ⚠️ / 0 ❌.

## Session narrative

### Opening — crashed-session recovery

Last session had crashed mid-Run-05. Working tree had uncommitted dev01 deregistration across 4 files (`hosts_map.yml`, `ansible/inventory/kvm.yml`, `ansible/group_vars/all.yml`, `config/wireguard/keys.sops.yml`); dev01 absent from toshiba. The inverse of the usual "Run 04 runtime churn" pattern — this was the destroy-half's config mutation left uncommitted after crash. CLI destroy had run; Playwright test had not.

**Option A selected** (over amend-spec / file-finding): restore pre-Run-05 state, then execute the scaffolded Playwright spec end-to-end as designed.

### Step 1 — restore dev01 via CLI (Run 04 invocation)

```
git restore hosts_map.yml ansible/inventory/kvm.yml ansible/group_vars/all.yml config/wireguard/keys.sops.yml
./tools/esacp.py provisionGeneric dev01 --wizard-mode existing \
  --wizard-arg 20260420_142102-dev01_iridium_blue.tgz
```

First attempt failed: `Unknown VM 'dev01'. Valid: saconsole, dev02, dev03, target5` — CLI reads hosts_map.yml from disk, and the uncommitted deregistration had dev01 removed. Restoring the 4 files brought dev01 back into the tracked registration; second invocation succeeded. Restore portion: 2m 8s. Exit 0 with `Generic provision complete — https://dev01.iridium.blue`.

Post-restore sync_check: 43 ✅ / 14 ⚠️ / 0 ❌. Working tree clean.

### Step 2 — Run 05 Playwright attempt 1 — latent regex bug surfaced

Crashed at spec line 186 after 58.6s:

```
Error: page.fill: value: expected string, got undefined
  at tests/accept-05-ui-full-company-specific.spec.js:186
  await page.fill('#f-virbr0-ip', params.target_virbr0_ip)
```

The destroy half (Step 1 of the spec) had completed successfully — dev01 was destroyed via UI right-click. The drag-to-deploy had opened the Deploy dialog, and the spec's form-fill loop crashed on `params.target_virbr0_ip`.

### Root-cause analysis — #265

`loadParams()` in the spec uses regex `^\s*([a-z_]+)\s*:\s*(.+?)\s*$` to parse the YAML params file. The key group `[a-z_]+` rejects any key containing a digit; `if (!m) continue` silently skips the offending line. Run 05's params contains `target_virbr0_ip: "192.168.122.26"` — the `0` in `virbr0` (canonical libvirt bridge name) caused the whole line to fail the regex, leaving `params.target_virbr0_ip` undefined at access time.

**Audited scope across all 5 acceptance specs:**

| File | Regex line | Digit-keys in matching params |
|---|---|---|
| accept-01 | 37 | none |
| accept-02 | 40 | none |
| accept-03 | 46 | none |
| accept-04 | 44 | none |
| accept-05 | 40 | **`target_virbr0_ip`** |

Runs 01–04 passed for the right reasons — their params have no digit-containing keys, their specs have no `params.foo || 'default'` fallback patterns that could mask undefined values. The bug has been armed across all 5 specs since scaffolding; Run 05 is the first to trip it.

**Why Run 05 is the first to reference `virbr0`:** Runs 02/03/04 are CLI transport — they `execSync('./tools/esacp.py provisionGeneric …')` and the Python pipeline reads `virbr0_ip` internally from `hosts_map.yml`. The value never crosses the Node/YAML boundary. Run 05 is UI transport — the spec drives the Cytoscape Deploy dialog with `page.fill('#f-virbr0-ip', params.target_virbr0_ip)`, so the value must be declared in the params file.

### Step 3 — narrow fix (B1) applied

Issue #265 filed with full analysis. Fix scope considered:
- **B1 (narrow):** patch `accept-05` spec only; note 01–04 copies as dormant.
- **B2 (broad):** patch all 5 specs for root-cause hygiene.

Chose **B1** after evaluating that:
- Failure mode is loud-crash-on-use, not silent-corruption — any future digit-key in another params would crash immediately.
- Runs 01–04 are archival (merged, green); their regex copies will not execute again.
- Runs 06/07 (UI transport, pending scaffold) will be seeded from the fixed Run 05 by the parity-partner pattern, so the fix propagates forward naturally.

Commit `05d96b1` changes the regex key group from `[a-z_]+` to `[a-z0-9_]+` in `accept-05` only.

### Step 4 — Run 05 Playwright attempt 2 — GREEN

dev01 was absent at baseline (attempt 1's destroy succeeded), so the spec's idempotent "absent at baseline — nothing to destroy" branch fired and went straight to drag-to-deploy.

```
[accept-05] self-check OK — proceeding to baseline/destroy
[accept-05] dev01 absent at baseline — nothing to destroy
[accept-05] drag tpl-erpnext-restored into Dev zone for dev01
[accept-05] provision job 2b156924 — waiting up to 3000s
[accept-05] provision job finished after 1767s
[accept-05] awaiting UI convergence within 300s
[accept-05] UI converged after 1s
[accept-05] canary: login as Administrator + GET /app/item/Test%20Item
  ✓  accept-05 (30.4m)
```

## Commits

| SHA | Branch | Commit |
|---|---|---|
| `fce6819` | accept/05-ui-full-company-specific | test(accept-05): scaffold UI full company-specific spec + params (pre-existing, from prior crashed session) |
| `05d96b1` | accept/05-ui-full-company-specific | fix(accept-05): parse params keys containing digits — fixes #265 |
| `9124505` | main | Merge PR #266 |

## Session-end state on main

- HEAD `9124505`.
- Working tree: 3 files modified (`ansible/group_vars/all.yml` WG pubkey, `config/wireguard/keys.sops.yml` ciphertext, `hosts_map.yml` dev01 registered + `vm_role: dev:unspecified`) — matches Run 02/03/04 runtime-churn discipline; uncommitted, absorbed by Run 06's destroy+rebuild.
- Transport-asymmetry note: UI set `vm_role: dev:unspecified` (main.js:1828 forces it for the development zone); Run 02 CLI had used `dev:full_company_specific`. Non-blocker — acceptance did not assert `vm_role`; canary parity was the acceptance gate.
- sync_check: 43 ✅ / 14 ⚠️ / 0 ❌.
- Open issues: 28 at session open; 28 at close (#265 filed + closed, net zero).

## UI-transport halfway parity snapshot

| Run | Transport | Variant | Merge | Result |
|---|---|---|---|---|
| 01 | CLI | saconsole rebuild | #228 / `e12a2c2` | GREEN (live-verified via #231 fix) |
| 02 | CLI | full company-specific | #251 / `aa69022` | GREEN (27.7m) |
| 03 | CLI | pseudo-wizard | #257 / `ad27d48` | GREEN (9.8m, attempt 7) |
| 04 | CLI | pseudo-restore | #258 / `33c4a3d` | GREEN (11.1m) |
| **05** | **UI** | **full company-specific** | **#266 / `9124505`** | **GREEN (30.4m)** |
| 06 | UI | pseudo-wizard | pending | not scaffolded |
| 07 | UI | pseudo-restore | pending | not scaffolded |

**CLI transport acceptance: 4/4.** **UI transport acceptance: 1/3 complete.**

## Reminders for next session

1. **Runtime churn on main** — same pattern as every destroy+rebuild. Long-term fix is #241 (hosts_map.local.yml overlay), deferred behind #240. Run 06's destroy will overwrite.
2. **`vm_role` UI asymmetry** — `main.js:1828` forces `dev:unspecified` when a VM is dropped into the development zone. Run 06 (UI pseudo-wizard) will set `dev:unspecified` too, whereas Run 03 (CLI) set `dev:pseudo_wizard`. #235 tracks CLI/API transport asymmetries — consider logging this as a sub-note there if it becomes a friction point.
3. **Runs 06/07 scaffolding** — copy the Run 05 spec (fixed regex) as the seed, not an earlier one. Both will need a `target_virbr0_ip` field, so the regex fix is load-bearing.
4. **Regex bug in 01–04 left dormant by choice** — if a future re-run of 02/03/04 adds a digit key to its params, the spec will crash loudly at the point of use. #265 gives the 2-minute lookup.

## Next

Matrix Run 06 — UI pseudo-company wizard (parity partner: Run 03 CLI). Agenda: `docs/SessionLogs/acceptance-matrix/06-ui-vm-pseudo-company-wizard-creates-backup.md`. Starting state: dev01 running full-company-specific from Run 05 backup; Run 06 destroys it first.
