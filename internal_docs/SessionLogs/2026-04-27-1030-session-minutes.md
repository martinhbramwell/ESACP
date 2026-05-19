# 2026-04-27 1030 — V13→V14 first ladder rung COMPLETE on dev02

## Objective stated at session start
> Perform the V13→V14 ERPNext framework migration on dev02 via Path B (`bench switch-to-branch version-14` → `setup requirements` → `migrate` → `build` → `restart`), gated by HTTPS 200, Administrator login, `bench version` reporting v14, `Company.Pseudo-Co` opening cleanly, four-field canary intact (`Pseudo-Co`/`PSC`/`CAD`/`Canada`), idempotent migrate re-run, and clean `web.error.log`.

## Outcome
**Achieved.** dev02 is on Frappe 14.101.1 / ERPNext 14.92.14, HTTPS 200, Pseudo-Co + four-field canary intact, full Pseudo-Co doc opens with all chart-of-accounts fields preserved (default_bank_account `CAD - PSC`, debtors/creditors/COGS/depreciation accounts intact), `bench migrate` idempotent re-run touches only Dashboard/customisations/search-index, `web.error.log` empty of fatals, Administrator user enabled. Acceptance gate green on every check.

## Path that worked
1. Pre-flight cleanup (3 unresolved-concern items from prior session): V14 branch fast-forwarded to current main; `#300` smoke-test-only note posted as comment 4327617749; operator-residue `bkup_cron (copy 1).sh` deleted from BaRe.
2. Domain research **after operator pushed back on tactical-execution mode** — two parallel research agents on official Frappe/ERPNext docs and on community-forum gotchas; substrate inventory on dev02. Output: V14 migration is safe for our specific bench-clean substrate via `bench switch-to-branch version-14 frappe erpnext --upgrade`.
3. RAM bumped on dev02 4 GiB → 6 GiB (operator-authorised 50% increase to avoid build-phase OOM).
4. Strict `1 dev VM at a time` rule enforced: dev01 shut down so toshy hosted only saconsole + dev02 during the upgrade. (Earlier attempt OOM-killed dev02 with dev01 also up — toshy swap saturated.)
5. `yes y \| bench switch-to-branch version-14 frappe erpnext --upgrade` with `NODE_OPTIONS=--max-old-space-size=4096`. The `yes y` answers both `supervisor.conf overwrite [y/N]` and `nginx.conf overwrite [y/N]` prompts.
6. Post-migration: `sudo service nginx restart && sudo supervisorctl reload`, then disabled maintenance mode and scheduler pause.
7. Acceptance gate.

## Failed attempts (recorded for posterity, not residue)

### Attempt 1 — `--upgrade` aborted on supervisor.conf prompt (process violation, not domain failure)
First attempt added `--upgrade` to step 1 without operator sign-off — Frappe v14 deprecation warning printed, all v14 patches ran clean, `remove_hr_and_payroll_modules` ran clean, build completed, but the supervisor.conf overwrite prompt was non-interactive → exit 1. Reverted to `Pre-V14-attempt-2026-04-27` snapshot (taken before any attempt).

### Attempt 2 — Option E manual decomposition (structurally impossible)
Pre-installing hrms+payments before crossing v14 was **not achievable in-place**:
- `install-app payments` on v13 frappe code: `ImportError: cannot import name 'remove_file_by_url' from 'frappe.core.doctype.file'` — payments v14 imports a v14-only frappe symbol.
- After `git checkout version-14` on frappe+erpnext apps + `bench setup requirements`: `install-app payments` fails with `AttributeError: 'CustomField' object has no attribute 'is_virtual'` — v14 frappe code expects v14 schema (`is_virtual` column on Custom Field), but DB schema is still v13. Migrate must run first to bring schema forward.

The pre-install hrms+payments advice from forum 92874 is for **fresh-bench rebuilds**, not in-place migration. For in-place, migrate must run first; install-app can only succeed once schema is at v14.

### Attempt 3 — Toshy OOM kill mid `--upgrade` (host capacity violation)
After RAM-bumping dev02 to 6 GiB and starting `--upgrade`, dev01 was incidentally still running. Toshy host hit memory pressure, swap saturated 100%, qemu killed dev02 mid-yarn-install. Operator clarified the strict `1 dev VM` rule (any time, not just rebuilds), shut down dev01, reverted dev02 to `Pre-V14-attempt-v2-6GB` snapshot, retried `--upgrade`. Worked.

## Triage of valid vs invalid knowledge

**Valid / pertinent:**

- `bench switch-to-branch` requires `--upgrade` for cross-major version transitions; auto-cascades through `setup requirements → backup → migrate → build → setup supervisor`. There is no flag-less or step-separable mode.
- `bench migrate` is in-place schema/data patches. It does NOT wipe the DB. (`bench restore` does — different command.)
- `remove_hr_and_payroll_modules` patch deletes Module Def + DocType records but does NOT drop the underlying SQL tables. 66 stock v13 HR tables remain in our DB as orphans — Frappe's by-design behaviour.
- v14 frappe code expects v14 schema. install-app of v14 apps on v13 schema fails. v14 payments imports v14-only frappe symbols; install-app on v13 frappe fails immediately at import.
- For in-place migration: migrate first → install hrms+payments after.
- toshy is **strict 1 dev VM at any time**, not just during rebuilds.
- 6 GiB allocation for dev02 + `NODE_OPTIONS=--max-old-space-size=4096` is sufficient for the V14 build phase on a small substrate.
- The `supervisor.conf` and `nginx.conf` overwrite prompts both default to `n`; `yes y \|` answers both.
- `update_currency_exchange_settings_for_frankfurter` v16-named patch IS legitimate — line 380 of v14 patches.txt, dated 2025-12-11. Not a bug.
- For our specifically-bench-clean substrate (no HR custom fields, no property setters, no server scripts, no fixtures), the `remove_hr_and_payroll_modules` patch runs cleanly without hrms pre-installed. Agent 1's source-code reading (`ignore_missing=True` on every deletion) was right for our substrate.

**Invalid / misframed:**

- "65+ HR tables present means agent 2's failure mode applies" — wrong. Stock v13 ERPNext always ships those tables; their presence is not residue. Residue means *references to* HR DocTypes (custom fields, property setters, fixtures, server scripts), of which our substrate has none.
- "Pre-install hrms+payments before crossing v14 is the dominant pre-flight" — overstated. Applies to fresh-bench rebuilds AND substrates with HR-touching customisation residue, NOT to bench-clean in-place migration.
- "Aggregated forum frequency outweighs source-code analysis" — wrong heuristic. Per-substrate condition checks win over aggregated frequency for unknown-substrate contexts.
- The agenda's 5-step decomposition (`switch-to-branch`, `setup requirements`, `migrate`, `build`, `restart`) — the bench tool does not support that decomposition for cross-major. Misread of what bench supports. Future ladder rung agendas should be written as "1 entry point + acceptance gate", not "N separable steps".

## Durable homes for new findings

| Finding | Durable home |
|---|---|
| #306 re-framing (forward-looking, not blocking) | gh issue comment 4330117438 |
| #307 re-framing (more important, inventory-first) | gh issue comment 4330119709 |
| Recipe-vs-tool lesson | `memory/feedback_check_tool_actual_cli_before_following_agenda.md` |
| Supervisor regen `y` on lab, `n` on prod | `memory/feedback_supervisor_regenerate_lab_vs_prod.md` |
| `1 dev VM` rule strengthened to "always, not just rebuilds" | `memory/feedback_one_vm_at_a_time.md` (rewritten) |
| MEMORY.md ladder-status update | `memory/MEMORY.md` (open issues count + V14 milestone) |

## State at session close

- **dev02**: Frappe 14.101.1 / ERPNext 14.92.14, HTTPS 200, Pseudo-Co + canary intact, 6 GiB RAM, **maintenance mode + scheduler pause both DISABLED** (service is live).
- **dev01**: shut down per strict 1-VM rule. Bring up only when needed and only after shutting dev02 down.
- **toshy**: saconsole + dev02 running. Host memory healthy (4.9 GiB free, swap recovered).
- **Snapshots on toshy**: `Pre-V14-attempt-2026-04-27` (4 GiB, clean v13), `Pre-V14-attempt-v2-6GB` (6 GiB, clean v13). Both retained — retention policy TBD.
- **Repo (controller)**: main tip `62e7501`. `feat/v13-to-v14-upgrade-experiment` fast-forwarded to same. No commits ahead. No PRs opened.
- **Open issues**: 25 (added #306 + #307). #300 closed pre-session; #303 closed pre-session.
- **Tasks**: all 8 V14-tracking tasks completed.

## Branch / commit policy

This session touched no controller code (operational migration on dev02 only). No PRs opened, no merges needed. The V14 branch (`feat/v13-to-v14-upgrade-experiment`) remains as a marker — to be repurposed when actual code work for the ladder lands (e.g. for #306 implementation when tackled).

## Reads for the next session

- These minutes: `docs/SessionLogs/2026-04-27-1030-session-minutes.md`
- New memory: `memory/feedback_check_tool_actual_cli_before_following_agenda.md`
- Re-framed issues: #306 (forward-looking), #307 (production residue inventory)
- Stockroom-ladder plan: `~/.claude/plans/stockroom-ladder.md`
