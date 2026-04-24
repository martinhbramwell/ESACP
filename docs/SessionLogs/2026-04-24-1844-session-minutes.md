# Session Minutes — Run 02 green; Run 03 blocked on #296 (Playwright Complete Setup race)

**Date:** 2026-04-24 ~15:30 → ~18:45 EDT
**Branches touched:** `feat/playwright-wizard-generic-fixture` (sub-2 of `umbrella/ladder-fixture`)
**Commits on sub-2:** `55d6a83`, `73df64a` (both this session)
**Commits on main:** this minutes file + next agenda
**PRs opened:** none
**PRs merged:** none
**Issues filed:** #296 (open — Playwright Complete Setup `waitForResponse` timeout under pipeline-context)
**Issues closed:** none
**Baseline:** entered at `main @ 2f3eb68`; 21 open issues
**Exit:** `main @ <this minutes commit>`; 22 open issues (+#296)

## Declared objective

Re-run matrix acceptance phases 02–07 on a fully-destroyed-and-rebuilt dev02, using the contamination-fixed substrate (sub-1 Stage 6 generic-mode gate, sub-2 clean-bench gate). Produce a clean B03-replacement golden backup, verify the roundtrip, then land sub-2 PR → umbrella, closing #292.

## Outcome

Phase 02 (CLI full company-specific from backup) **green** under sub-1 contamination-fixed substrate. Phase 03 (CLI pseudo-wizard creates backup) **blocked** on a reproducible Playwright failure at the wizard's final *Complete Setup* click. Bug filed as #296. Session closed early per operator decision (option C — stop and document) rather than scope-creep into fix attempts. Phases 04–07 deferred to the post-#296 session.

## What happened

### Session-start review

- `sync_check`: 48 ✅ / 9 ⚠️ / 0 ❌ (warnings as expected — dormant target VMs + manual Chrome verify)
- Open-issues review: 21; #292 confirmed as the active sub-2 objective
- Operator confirmed objective + answered three Q's about Run 02 framing, golden-backup input file, and snapshot naming preferences

### Phase B — pipeline additions on sub-2 (two GPG-signed commits)

| Commit | Files | Change |
|---|---|---|
| `55d6a83` | `tools/pipeline/orchestration/snapshot_ops.py`, `tools/pipeline/orchestration/wizard_run.py`, `tools/size_baselines.json` | New `revert_snapshot()` primitive (parallel to `create_snapshot`); replay-branch post-`capture_golden_backup` snapshot of `"ERPNext Generic Company"` |
| `73df64a` | `tools/pipeline/macro/provision_generic.py`, `tools/pipeline/orchestration/wizard_run.py` | Snapshot-name alignment with operator terminology — `"ERPNext v13 Generic Baseline"` → `"ERPNext V13 before Wizard"`; `"ERPNext Generic Company"` → `"ERPNext V13 Complete Generic"` |

Stage-1 `"Baseline"` snapshot left unchanged this session — `sync_check` and the API `provisioned` detection key off that literal string; rename out of scope.

The `existing` branch's auto-revert wiring was deliberately deferred (snapshot-name drift unresolved + stage-idempotency on a reverted VM untested). For run 04 the new `revert_snapshot` primitive is intended to be invoked manually before `provisionGeneric`, per the prior agenda's explicit allowance.

### Matrix Run 02 — green

Command: `./tools/esacp.py provisionGeneric dev02 --wizard-mode=existing --wizard-arg 20260421_114520-dev01_iridium_blue.tgz`

Sequence: `destroy dev02` → `addHost dev02 --zone development --vm-role dev:full_company_specific --hypervisor toshiba --backend kvm` → 9 stages → wizard-mode=existing restore.

Acceptance:

| Check | Result |
|---|---|
| HTTP 200 on `https://dev02.iridium.blue/` | ✅ (1.06s) |
| `sites/apps.txt` | `frappe`, `erpnext` only (truly generic, sub-1 working) |
| Supervisor processes | 8/8 RUNNING (no `ce_sri_svc`, redis + web + workers) |
| `currentsite.txt` | `dev02.iridium.blue` |
| `verify_stage_6 --mode=generic` | 6/6 ✅ — `/opt/generic/envars.sh` deployed, `/opt/ce_sri` absent, no `you_gh_*` keys, BaRe cloned without ce_sri/route_planner/returnable, Procfile clean, BaRe/envars.sh → /opt/generic/envars.sh |
| Snapshot taken | `"ERPNext V13 before Wizard"` ✅ (rename commit `73df64a` working) |
| Restore time | `handleRestore` 2m 8s |

Pre-run prediction (regression on truly-generic bench) was wrong — input `.tgz` was 1.3 MB, no company-specific app data. `provisionGeneric --wizard-mode=existing --wizard-arg <small-backup>` is a valid combination on the sub-1 substrate.

### Matrix Run 03 — failed at Playwright Complete Setup click (twice)

Command: `./tools/esacp.py provisionGeneric dev02 --wizard-mode=replay --wizard-arg pseudo-co-wizard.spec.js` (after destroy + re-register).

Stages 1–9 all green. `"ERPNext V13 before Wizard"` snapshot taken. Wizard replay started; failed:

```
page.waitForResponse: Timeout 180000ms exceeded while waiting for event "response"
    at pw-replay-1777064079116.cjs:178:10
  name: 'TimeoutError'
```

Spec line 176–183 (the *Complete Setup* click + `waitForResponse` Promise.all):

```js
await waitForFrappeIdle(page);
const [completeResp] = await Promise.all([
  page.waitForResponse(
    r => /setup_complete/.test(r.url()) && r.request().method() === 'POST',
    { timeout: 180_000 },
  ),
  page.getByRole('button', { name: 'Complete Setup' }).click(),
]);
```

### Diagnosis — backend completed, Chrome closed connection mid-flight

Backend state queries (via ProxyJump `toshy` → erpadm@192.168.122.27):

| Query | Result |
|---|---|
| `tabSingles: System Settings.setup_complete` | `1` |
| `tabCompany` | `Pseudo-Co / Canada / CAD / PSC` |
| `COUNT(*) FROM tabAccount WHERE company='Pseudo-Co'` | `86` (CoA seeding completed) |
| Company.creation → last CoA write span | ~13s |
| Company.creation → Company.modified | ~35s |
| nginx access.log for `setup_complete` POST | `499 0` (Client Closed Request, 0 bytes returned) |
| `web.log`, `worker.log`, `frappe.log`, `nginx error.log` | clean — no errors related to setup_complete |

The handler completed in ~35s, well within the 180s `waitForResponse` timeout. The HTTP 499 means Chrome closed the connection before nginx could deliver gunicorn's response — the response never reached Playwright's listener.

### Bisect — reproducible, not flake

Per `feedback_bisect_before_hypothesizing.md`. Reverted dev02 to `"ERPNext V13 before Wizard"` snapshot (via raw `virsh snapshot-revert`), site responded HTTP 200 post-revert, ran `node replay_wizard.js --script pseudo-co-wizard.spec.js --url https://dev02.iridium.blue` directly (skipping `provisionGeneric` to isolate variable). **Same failure**: line 178, same error class, same backend completion footprint.

### #294 acceptance gap

PR #294 (merged earlier today as `473f058`) hardened the wizard with `waitForFrappeIdle`, modal DOM-remove fallback, and 90s `waitForURL`. That hardening targeted the *Industry → Company* transition (per #284). #294's acceptance stanza — *"4× acceptance green (2 manual + 2 pipeline fresh-revert to golden backup)"* — does not cover this path: the 2 pipeline runs used `wizard-mode=existing` (restore, no wizard replay). This session's Run 03 was the first pipeline-replay run after #294 merged, and it failed at a different wizard step.

### Operator decision — option C (stop and document)

Three options presented:
- (A) Fix the spec inline (30–60 min iteration) — scope creep beyond matrix-rerun objective
- (B) Bypass for Run 03 only (manual handleBackup → snapshot → Run 04) — Run 06 (UI pseudo-wizard) still fails, doesn't unblock matrix
- (C) Stop, file blocker, dedicate next session to fix

Operator chose (C). Aligned with one-objective-per-session rule.

## Repository state at session close

| Item | State |
|---|---|
| `feat/playwright-wizard-generic-fixture` (sub-2) | 2 new commits on top of `umbrella/ladder-fixture @ ea5cf92`, pushed to origin |
| `umbrella/ladder-fixture` | unchanged at `ea5cf92` |
| `main` | this minutes commit + next agenda |
| Working tree on sub-2 | dirty: `hosts_map.yml`, `ansible/inventory/kvm.yml`, `ansible/group_vars/all.yml`, `config/wireguard/keys.sops.yml` (dev02 re-registration side-effects from session work; new IPs `192.168.122.27` / `10.10.0.17`, new WG pubkey `QQ9Z9MlsRYmBTOE5oy9fpY+IjW+mIllZ9/Fv8B1HGQk=`) — intentionally not committed; next session decides |
| dev02 VM | running on toshy, in mixed state — reverted to `"ERPNext V13 before Wizard"` then ran replay which silently completed backend wizard (Pseudo-Co + 86 CoA + setup_complete=1 in DB) but failed Playwright assertion. Preserved as evidence for #296. |
| `~/.ssh/config` for `dev02` | stale (still points to old `192.168.122.20`) — operator-environment concern; not a repo bug |

## Issues / artefacts produced

| Issue | Title | Status |
|---|---|---|
| #296 | bug(wizard-replay): Complete Setup POST returns HTTP 499 — Playwright client closes before backend response delivered | open, blocks #292 (matrix sub-2) |

Run logs preserved (not committed): `/tmp/matrix-02.log`, `/tmp/matrix-03.log`, `/tmp/matrix-03-retry.log`.

Old contaminated golden backups (4× `20260424_*-dev02_iridium_blue.tgz`) **not** archived this session — kept in `platforms/kvm/golden_backups/` until matrix completes (avoiding premature cleanup if they prove useful as restore-fallback inputs in #296 debugging).

## What did NOT happen (deliberately)

- No PR opened from sub-2 → umbrella. Matrix is incomplete; sub-2's narrative isn't ready for review.
- No bypass workaround applied. Per option C, the bug is not papered-over.
- No edits to `pseudo-co-wizard.spec.js`. Fix belongs in a dedicated #296 sub-branch.
- No archival of contaminated golden backups. Premature.
- No update to Stage 1 `"Baseline"` snapshot rename — would need coordinated `sync_check` / API change; out of scope.

## Reminders / follow-ups

- **#296** is the next session's objective. Sub-3 of `umbrella/ladder-fixture`, branch suggestion: `feat/wizard-complete-setup-fix`.
- The dev02 mid-debug state is preserved on toshy. Don't destroy it casually — it's evidence for #296 (DB shows wizard completed, nginx shows 499). Capture screenshots / `playwright trace` output before destroying.
- After #296 lands, retry Run 03 → if green, continue 04–07 on the contamination-fixed substrate.
- SSH alias staleness gap (operator's `~/.ssh/config` has stale dev02 IP after destroy + re-register) — file as standalone tech-debt issue if it costs another session's time. Not filed yet — environmental, not a repo bug.

## Lessons (for future sessions)

- **Verify before predicting regression.** Pre-run hypothesis was that `provisionGeneric --wizard-mode=existing` against a sub-1-truly-generic bench would fail because the prod backup's DB references missing apps. Wrong — input file was 1.3 MB (pseudo-data), no missing-app references. Always check the size/contents of the input artefact before predicting failure.
- **#294's acceptance had a path-coverage gap.** "4× green" is not enough if all 4 take the same code path. Future fix-acceptance should explicitly enumerate the dispatch transports (CLI + API + UI) and replay-modes (record + replay + existing), and tick each one. This is the same class of gap that #235 tracks for transport-parity audits.
- **Substrate cleanliness changes wizard behaviour subtly.** Operator's manual run on the polluted Baseline (2026-04-24 morning) passed; pipeline run on the clean post-sub-1 substrate failed. The variables that differ between manual + pipeline contexts are now narrowed enough that #296 can target a specific spec edit. Capture the bisect path explicitly in the issue body.
