# 2026-05-22 1217 — Session 74 minutes

## Stated objective

Execute V13→V14 upgrade trial on dev02 per the S73 plan file `~/.claude/plans/v14-trial-dev02.md` (ESACP#428). Substantive-class 1:1:1 session. Branch `feat/428-v14-trial-dev02` from main.

## Outcome — #428 acceptance met; closing via PR; substantial scope expansion on disposable substrate

V13→V14 upgrade trial executed end-to-end on dev02 (frappe 13.58.22 → 14.101.1, erpnext 13.55.2 → 14.92.14, 22 433 Sales Invoices / 1 803 Customers / 312 Items preserved exactly, HTTP 200, all services healthy). Wall-clock 06:57 → 07:36 = **39 min** (vs. 2hr cap). All four acceptance criteria from plan file §"Acceptance criteria" satisfied.

Operator then greenlit two exploratory extensions on the same dev02 substrate (informal probes within S74, per `feedback_dev_vms_are_disposable.md`): V14→V15 (11 min, succeeded — frappe 15.108.0 / erpnext 15.108.3) and V15→V16 (1 min to definitive answer — hit Python 3.10 vs frappe-v16 PEP 695 syntax wall). Reverted to v15 snapshot, then a third extension reframed by operator-articulated end-state vision ([[end-state-v16-lts-current-stack]] saved to memory): "quick" path = install Python 3.14 + Node 24 + pkg-config on existing 22.04 substrate, rebuild bench venv on python3.14, retry v16. Probe ran 11:08 → 11:46 = **38 min**. Reached the actual v16 migration; halted on real upstream erpnext patch defect.

Full chronological log (every command, exit code, timing) in `internal_docs/SessionLogs/2026-05-22-v14-trial-notes.md`. This minutes file summarizes.

**dev02 final state**: reverted to `pre-py312-rebuild-S74` snapshot per operator instruction. Frappe 15.108.0 / erpnext 15.108.3 / HTTP 200 / root + login + API ping all confirmed post-revert.

## Findings discovered + filed (5 new issues, 9 captured findings)

| Defect | Class | Where | Issue |
|---|---|---|---|
| `clearKnownHosts` misses FQDN entries (`dev02.iridium.blue` form) — only clears bare hostname/nickname/IPs from `hosts_map.yml` | tooling | Pre-flight 1 | ESACP#438 |
| `snapShotVM` dispatcher runs local virsh — does not resolve hypervisor from `hosts_map.yml` | tooling | Pre-flight 4 | ESACP#440 |
| Plan-doc gap: `frappe-bench-all` supervisor group is generic, doesn't match VM-specific groups (web, workers, redis) | plan-text | Step 1 | (capture for plan-file update; minor) |
| #331 narrower than predicted — only `returnable` hits gunicorn URL-dep; route_planner / ce_sri / SPC install with full deps | observed | Step 2 | (informs future workarounds) |
| Plan sequencing: `bench migrate` requires `redis_cache` running; plan §Step 1 stops all services | plan-text | Step 5 | (capture for plan-file update or substrate primitive auto-start) |
| `applySubstrateMigration` discards `bench migrate` stdout on success — loses defect-capture surface | tooling | Step 5 | (high-value follow-up — see S75 agenda) |
| Patch-log creation timestamps backdated to 06:20-06:21 for patches applied at 07:12-07:23 | observed | Step 5 | (capture for review; not blocking) |
| `bench execute frappe.utils.background_jobs.get_workers` JSON-serialize TypeError | tooling | Step 7 | (minor CLI defect) |
| Phase 3 (LSKB#5) result: redis-py 3.5.3 ✓, rq 1.14.1 ≠ target 1.8.0 — but no observable regression | observation | Step 7 | LSKB follow-up needed |
| `pypika` URL-dep on `returnable` consistent v14→v15→v16 — actually returnable declares unpinned frappe dep | observed | Extensions | (root-cause refined for #331 class) |
| **V16 substrate prereqs**: Python ≥3.14 (not just 3.12+, frappe pyproject pin), Node ≥24, pkg-config | infra | Extension 3 | ESACP#445 |
| **V16 patch defect**: `erpnext.patches.v16_0.make_workstation_operating_components` calls `doc.save()` on submitted doc → `UpdateAfterSubmitError` ("Operating Components Cost" 0→3). Halts v16 schema migration. | bug | Extension 3 | ESACP#444 |

## Verifications performed (substrate touched per plan)

| Check | Method | Result |
|---|---|---|
| Sync_check at start | `bash platforms/kvm/sync_check.sh` | 45-46/9/2-3 — flapping on dev02 ping (Run-2 transient); direct ping clean; accepted per pre-flight Decision #1 |
| dev02 SSH | `ssh dev02-erp` (alias; FQDN form failed via too-many-auth — see Defect #2 narrative) | Worked via SSH alias once routing fixed |
| Pre-flight baselines | Captured exactly per plan: bench version + list-apps + HTTP 200 + 3-table row counts + tabPatch Log tail (Phase 4 SPC patch confirmed at 2026-05-21 15:42:17) | All captured |
| Snapshot create (raw virsh via S71 directive) | `ssh toshy 'virsh ... snapshot-create-as dev02 pre-v14-upgrade-trial-S74 --atomic'` | ✓ in 19s |
| V14 trial end-to-end | Plan Steps 1-7 | All ✓; HTTP 200 + login + API ping post-restart |
| V14→V15 probe | Same pattern as v14 trial | ✓ 11 min |
| V15→V16 (3.10) attempt | switch-to-branch v16 | Hard wall: PEP 695 syntax → reverted |
| V15→V16 (3.14) attempt | Python 3.14 + Node 24 + pkg-config + mt940 install; bench setup env --python python3.14 + bench setup requirements + --no-deps workaround | ✓ all installs; bench build ✓; migrate halted on E10 |
| dev02 post-revert | `snapshot-revert pre-py312-rebuild-S74` + verify | frappe 15.108.0 / erpnext 15.108.3 / HTTP 200 ✓ |

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1 (pre-commit) | `Agent(esacp-qa)` pre-`<this commit>` | _pending — see qa-log close-batch row_ | Substantive single-issue class. Three files: trial notes (substantive log), minutes, next-agenda, qa-log row. |
| T2 (pre-merge) | `Agent(esacp-qa)` pre `gh pr merge` | _pending — see qa-log close-batch row_ | Single-commit branch; §2.2 carve-out applies if T1+T3 approve. |
| T3 (pre-push) | `Agent(esacp-qa)` pre `git push -u origin feat/428-v14-trial-dev02` | _pending — see qa-log close-batch row_ | T1+T3 combined per §2.1. |
| T5 (pre-issue-close) | `Agent(esacp-qa)` pre `fixes #428` auto-close | _pending — see qa-log close-batch row_ | #428 acceptance met (V14 trial end-to-end, defects captured, dev02 reachable, Phase 3 observed). |

T4 (pre-destroy) not triggered S74 — snapshot reverts are reversible by re-creating + re-running upgrade; no `destroy_vm` or equivalent ran. The `ssh-keygen -R` was a single-line workaround, not a destructive operation in the verdict-layer sense.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| ESACP#428 | closed via `fixes #428` in PR body | V13→V14 trial acceptance met (HTTP 200, defects captured, Phase 3 observed) |
| ESACP#438 | filed at discovery | `clearKnownHosts` FQDN bug — tooling defect found during pre-flight |
| ESACP#440 | filed at discovery | `snapShotVM` hypervisor-resolution bug — tooling defect found during pre-flight |
| ESACP#444 | filed at session-close | V16 erpnext patch defect (E10) — `make_workstation_operating_components` |
| ESACP#445 | filed at session-close | V16 substrate prereqs (E5/E6/E7) — Python 3.14 + Node 24 + pkg-config |

## Counts at session end

- ESACP open: was 48 at S74-start → **51** at S74-close (close #428 = -1; file #438, #440, #444, #445 = +4; net +3).
- LSKB / ce_sri / ce_sri_svc / LogiSoluValidations / BaRe open: unchanged from S73 close (9 / 6 / 2 / 2 / 2).
- Trial notes file: `internal_docs/SessionLogs/2026-05-22-v14-trial-notes.md` (~330 lines; substantive log).
- Snapshots on dev02: **6** total (Baseline, ERPNext v13 Restored Baseline, pre-v14-upgrade-trial-S74, post-v14-pre-v15-S74, post-v15-pre-v16-S74, pre-py312-rebuild-S74). All retained per `feedback_keep_merged_branches.md` analogous-disposition (substrate restore points are cheap and useful for re-runs).

## TRIVIAL_FIXES.md status

Unchanged — 3 monitor-only entries carry forward (LSMem Trigger-3 skip S33; `tools/secrets.py +x` S47; `sync_check.sh:2 Mighty` S58). Not touched this session (substrate work, no housekeeping).

## Memory updates

- **New**: `project_end_state_v16_lts_current_stack.md` ("scripted production-backup → fully-current V16/LTS/apt/pip/npm; gates CloudStack"). Articulated by operator mid-session, captured to memory so future sessions inherit the end-state framing.
- **MEMORY.md index updated** with link to the new memory entry.

## Carry-forward operator-reminders (delta)

**New from S74**:

- **V16-substrate work prioritization** — ESACP#444 (E10 patch defect) + #445 (E5/E6/E7 substrate prereqs) are now filed. Next session's operator decision: do them in priority order vs. doing the bespoke-app `returnable` cleanup (E9, currently uncatalogued).
- **`applySubstrateMigration` stdout-discard finding** — high-value tooling improvement: primitive's success path loses migrate output, which is the trial's whole point. Captured but not filed as own issue this session.
- **dev02 currently on v15** — six snapshots retained; future sessions can pick v13, v14, v15, or mid-v16-migration starting point cheaply.

**Discharged from S73 next-agenda carry-forward (this session)**:

- **#428 plan execution** — V14 trial completed end-to-end with full defect log + Phase 3 observation + #331 narrower-than-expected finding (LSKB#5 verification result captured).
- **Three pre-flight operator-decisions** — locked in at S74 start per recommendations; all three played out (sync_check tolerance = right call, no revert needed S5-irrecoverable, wall-clock 39min within 2hr cap on V14 trial proper).

**Carries to S75 next-agenda (unchanged from S74 carry-in unless noted)**:

- **S71 minutes backfill** — still pending operator decision (a/backfill from PR#422+#418, or b/treat PR#422+#418 close-comment as sufficient). Not raised this session — operator-selected #428 execution as objective.
- **#426 (observability triage) + #427 (Stage 3 deploy_keys SPC)** — pending pickup; #427 has same SPC-missed-from-list root cause as the #331 workaround that v14 trial used.
- **on_boarding branch handoff** — Junior owns; do not touch.
- **LogiSoluMemory cross-repo cleanup (~28 stale `docs/` refs)** — housekeeping sidebar candidate.
- **ESACP#401 (saconsole) + dev02 intermittent pings** — own infra session.
- **LSKB#11 / #16 / #18 / #21** — Phase 2/3 follow-on.
- **ESACP#387 / #394 / #395 / #396 / #397** — pre-S48 carry items.
- **`sync_check.sh:2 Mighty` (S58 TRIVIAL_FIXES)** — next housekeeping pass.
- **`tools/secrets.py +x` (S47 TRIVIAL_FIXES)** — next housekeeping pass.
- **T3-miss pattern (S58)** — monitor (no recurrence S74).
- **MariaDB-10.6 default PS=OFF** — Packer-baked substrate ships with PS off (S55 carry).
- **LSMem Trigger-3 skip pattern** — 2 events monitor-only.
- **Tablet WG sidebar (#383)** — still ripe.
- **Pages site is live** — tenant-detail scrub gate before any `docs/*` commit.
- **`session_focus.txt` / `session_buckets.txt` controller-root placement** — S60 carry, non-blocking.
- **`project_wip_consolidation_plan.md` `returnable` → `BtlMng` rename note** — soft housekeeping.
- **Stage-6-equivalent M&V check every ~50 substantive closes** — operational reminder.

## Self-classification

**Substantive-class single-issue session** — branch `feat/428-v14-trial-dev02` from main, PR to main, `fixes #428`. Operator-greenlighted exploratory extensions on disposable substrate (V14→V15, V15→V16) remained within #428's parent scope (V14 trial = parent objective; extensions = "while we're here on the same VM" probes per `feedback_dev_vms_are_disposable.md`). Not housekeeping-bundle (substantive code/substrate work). Not introspection-sidebar (no MEMORY.md restructure, no carry-forward attrition — memory addition only, which is content not structural).

Diff-based introspection-sidebar trigger check (per CLAUDE.md): no MEMORY.md restructuring (entry added, not reorganized); no carry-forward operator-reminder attrition (existing reminders carry forward unchanged; new ones added). Trigger negative; not a sidebar. Tag accordingly.