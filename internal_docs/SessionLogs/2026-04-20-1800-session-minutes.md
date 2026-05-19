# Session Minutes — Matrix Run 04 GREEN (CLI restore from B03)

**Date:** 2026-04-20 ~17:10–18:04 EDT
**Branch:** `accept/04-cli-pseudo-restore`
**PR:** #258 — merged via local GPG-signed merge commit `33c4a3d` at 2026-04-20T22:04:34Z
**Agenda:** `internal_docs/SessionLogs/acceptance-matrix/04-cli-vm-pseudo-company-restore-from-wizard-backup.md`
**Params:** `internal_docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml`

## Objective

Execute Matrix Run 04 (CLI · dev VM · skeletal ERPNext restored from B03) to green, consuming the B03 archive produced by Run 03 (PR #257, `ad27d48`).

## Outcome — GREEN (first attempt)

- `accept-04` attempt 1: **1 passed (11.1m)**.
- `provisionGeneric dev01 --wizard-mode existing --wizard-arg 20260420_142102-dev01_iridium_blue.tgz` → exit 0 after 596s. handleRestore.sh internal elapsed: 0h 1m 59s.
- UI convergence: 1s.
- Canary: `GET /api/resource/Company/Pseudo-Co` → 200. Fields match Run 03 verbatim: `abbr=PSC`, `default_currency=CAD`, `country=Canada`, `Company.count==1`.
- `platforms/kvm/golden_backups/` unchanged — 3 files pre+post (B03 + two older), no new backup produced by restore path.
- `sync_check` ERPNext row for dev01 → ✅.

## Preflight finding (no issue filed — not a SUT bug)

The Run 04 agenda proposes `./tools/esacp.py provision --params <yml>`. The current SUT (post PR #255, `86a7c1d`) has no `--params` flag; the equivalent restore capability is `provisionGeneric --wizard-mode existing --wizard-arg <backup_tgz>` (documented in `tools/CLAUDE.md`: "`existing` = restore from golden backup"). The matrix SUT-frozen rule forbids inline SUT changes during an acceptance run. The spec invokes the existing CLI and reads target identity + canary facts from the param file. Same precedent documented inline in `03-cli-pseudo-wizard.yml`.

## Commits

| SHA | Commit |
|---|---|
| `10dedda` | test(accept-matrix): Run 04 restore spec + params |
| `33c4a3d` | Merge pull request #258 from martinhbramwell/accept/04-cli-pseudo-restore |

## Files added

- `internal_docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml` (37 lines)
- `prototypes/cytoscape/tests/accept-04-cli-pseudo-restore.spec.js` (322 lines)

## Uncommitted runtime churn on main (working tree)

`git status` after merge shows the same destroy-then-addHost ephemeral drift the Run 03 session left behind:

- `ansible/group_vars/all.yml` — dev01 WG pubkey rotated (new keypair from rebuild)
- `config/wireguard/keys.sops.yml` — SOPS ciphertext rotated (dev01 privkey stored)
- `hosts_map.yml` — `vm_role: dev:pseudo_wizard` → `dev:pseudo_restore`

Left uncommitted — Run 05 destroys dev01 first and will overwrite all three with its own variant's values. Matches Run 02/03 discipline. Issue #241 (hosts_map.local.yml overlay) is the long-term fix.

## Exit state (handed to Run 05)

- `dev01` running skeletal ERPNext restored from B03 (virsh id=72).
- `saconsole` running.
- Backups preserved: B03 + two older (generic 2026-04-09, target5 2026-04-15).
- Main at `33c4a3d`.

## CLI-transport halfway parity snapshot (per plan, post-Run-04 checkpoint)

| # | Transport | Target | Variant | Acceptance |
|---|---|---|---|---|
| 01 | CLI | saconsole | rebuild | Live-verified via #231 fix (PR #232); canonical Playwright replay formally waived 2026-04-19 pm |
| 02 | CLI | dev VM | full company-specific restore | GREEN attempt 6 — PR #251 merged 2026-04-20 09:48 EDT (`aa69022`) |
| 03 | CLI | dev VM | pseudo-company wizard (B03 produced) | GREEN attempt 7 — PR #257 merged 2026-04-20 ~17:05 EDT (`ad27d48`) |
| 04 | CLI | dev VM | pseudo-company restore from B03 | GREEN attempt 1 — PR #258 merged 2026-04-20 22:04:34Z (`33c4a3d`) |

All four CLI runs met acceptance. Matrix is halfway through. UI transport (Runs 05–07) is the remaining work, after which parity comparisons (02↔05, 03↔06, 04↔07) close the matrix.

## Open concerns not addressed this session

- `sync_check` 3 ❌ rows for dev02/dev03/target5 (idle VMs) — same pattern the spec tolerates via swallow-and-grep; not investigated. No new finding (pre-existing state at session start).
- Runtime churn on main working tree (hosts_map.yml, group_vars/all.yml, keys.sops.yml) — see above; intentional per prior-run discipline.

## Next

Run 05 — UI-driven dev VM full-company-specific restore from production backup (transport transition CLI → UI). Destroys dev01 first.
