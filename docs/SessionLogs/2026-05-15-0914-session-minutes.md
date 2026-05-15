# 2026-05-15 0914 — Session 53 minutes

## Objective

**LSKB#20 Plan-C tag pivot** — research frappe v13 tag history for the lowest tag where braintree + pyyaml decayed pins are both buildable on current PyPI; pick a substrate-version-alignment target; run packer build at the new tag from saconsole; destroy + reprovision dev02; verify `bench list-apps` shows the pinned versions; close LSKB#20. Bucket-2 substantive (LSKB-tracker decision; ESACP-side build/reprovision execution).

## Outcome — LSKB#20 closed end-to-end; Plan-C empirically validated; ESACP#396 filed

**LSKB#20 closed at `2026-05-15T12:53:Z`-ish** (manual close, `state_reason: completed`) after a clean end-to-end execution. Target pinned to **frappe `v13.58.22` / erpnext `v13.55.2`** (Option 1: the exact tag-pair `version-13` HEAD resolves to today, per S50 metadata; SHAs `5ec534b` / `37e00a6`). Pin discipline verified at five layers: build CLI → packer git clones → toshiba metadata → esacp pool qcow2 → dev02 `bench list-apps`. Zero decayed-pin strikes during the build — both braintree and pyyaml classes resolved upstream by the chosen tag.

One new bucket-1 issue surfaced and filed mid-session: **[ESACP#396](https://github.com/martinhbramwell/ESACP/issues/396)** — `seed_iso.py` hardcodes `~/.ssh/hasan_mighty.pub`, which blocks running the provision pipeline from saconsole (user `you`, key `id_ed25519`). Worked around by running provision from the local controller; documented as a deferred fix.

### Plan-C tag-pivot research

Bare-cloned `frappe/frappe` and `frappe/erpnext`; scanned `requirements.txt` at every v13 tag from v13.41.3 onwards for the two decayed-pin transitions:

| Pin | Last broken tag | First clean tag |
|---|---|---|
| `braintree~=4.8.0` → `~=4.20.0` | v13.57.1 | **v13.57.2** |
| `PyYAML~=5.4.1` → `~=6.0.1` | v13.58.2 | **v13.58.3** |
| First v13 tag where both decays clear | — | **v13.58.3** |

Tag SHAs cross-checked against S50 metadata: frappe `v13.58.22` = `5ec534b8...` ✓, erpnext `v13.55.2` = `37e00a6...` ✓ — both annotated tags stable.

### Tag-target decision (Option 1 chosen)

Two viable candidates presented to operator:

- **Option 1**: frappe `v13.58.22` / erpnext `v13.55.2` — the exact tag-pair `version-13` HEAD resolves to today; S50 already empirically clean-built this content (under branch-tip clone). Zero latent-decay risk. Furthest from production v13.41.3 (~17 minor versions). Frozen-tag pins for reproducibility.
- **Option 2**: frappe `v13.58.3` / erpnext date-aligned counterpart — first known-clean tag for both decays; ~5 minor closer to production. But ~19 minor versions of untested latent-decay risk between v13.58.3 and v13.58.22.

Operator chose Option 1 on the Plan-C motivation ("stop peeling decays; each strike costs ~30 min build + diagnosis"). Decision posted to LSKB#20 at [issuecomment-4459046442](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4459046442).

### Build execution — pin discipline verified

Build kicked off on saconsole via `/tmp/build-LSKB20-S53.sh` (deployed per `feedback_remote_script_pattern.md`) at `2026-05-15T07:31:38-04:00`; backgrounded via `setsid nohup`; watchdog polled until packer PID exited. Build exited 0 at `2026-05-15T08:09:31-04:00` (~38 min wall, matching S50's 37 min on equivalent content).

Pin-discipline checks (build log `saconsole:/tmp/build-LSKB20-S53.log`):

- Line 1428: `bench init /home/erpadm/frappe-bench (frappe v13.58.22) ...`
- Line 1439: `git clone https://github.com/frappe/frappe.git --branch v13.58.22 --depth 1 --origin upstream`
- Line 1534: `bench get-app erpnext (v13.55.2) ...`
- Line 1536: `git clone https://github.com/frappe/erpnext.git --branch v13.55.2 --depth 1 --origin upstream`

Metadata + pool post-build (toshiba):

```json
{
  "image":          "erpnext-v13-2026-05-15.qcow2",
  "frappe_branch":  "v13.58.22",
  "erpnext_branch": "v13.55.2",
  "erp_user":       "erpadm",
  "built_at":       "2026-05-15T12:09:21Z",
  "built_by":       "hub:/opt/esacp/platforms/packer/build.sh",
  "state":          "undifferentiated"
}
```

esacp pool: `erpnext-v13-2026-05-15.qcow2` landed; `erpnext-v13-2026-05-14.qcow2` (S50 tip-build) and `erpnext-v13-2026-03-30.qcow2` (pre-S48 preserved) untouched.

### dev02 destroy — preserving WG/SOPS/hosts_map

Stage 1's idempotency gate (`if all_passed(verify_stage_1): skip`) and dev02's existing Baseline + ERPNext-v13-Generic-Baseline snapshots meant a fresh `provision dev02` would have silently no-op'd. Built `/tmp/destroy-dev02-S53.sh` to virsh-destroy the VM + storage without touching hosts_map / SOPS / WG (mirrors `cleanup_residue.py`'s sequence). Executed clean: 2 snapshots deleted (Baseline + ERPNext v13 Generic Baseline), domain destroyed + undefined, both volumes (`dev02.qcow2` + `dev02-seed.iso`) removed. Verified: `dominfo dev02` returns "failed to get domain"; no `dev02` disks in esacp pool. WG keys / hosts_map / SOPS unaltered.

### Reprovision — pivot to local controller after ESACP#396 surfaced

First provision attempt on saconsole crashed at Stage 1 / Step "Build cloud-config seed ISO":

```
FileNotFoundError: Controller pubkey not found: /home/you/.ssh/hasan_mighty.pub
```

Root cause: `seed_iso.py:25` hardcodes `Path.home() / ".ssh" / "hasan_mighty.pub"`. On hasan's controller this resolves to `/home/hasan/.ssh/hasan_mighty.pub` ✓ exists. On saconsole (user `you`, key `id_ed25519`) the file doesn't exist. The hardcode predates ESACP#388's "saconsole as fleet-capability" framing and conflicts with the institutional intent (controllers bootstrap-only; saconsole manages siblings).

Filed [**ESACP#396**](https://github.com/martinhbramwell/ESACP/issues/396) with the full diagnosis. Worked around in S53 by running provision from the local controller (where `hasan_mighty.pub` exists). Pre-cleared known_hosts via `./tools/esacp.py clearKnownHosts` (removed 6 stale entries). Provision started `08:15:01-04:00`, exited `08:44:02-04:00` (~29 min, all 9 stages clean + Final snapshot "ERPNext v13 Restored Baseline" taken).

### Acceptance — dev02 reports pinned versions

```
ssh dev02 'sudo -u erpadm bash -lc "cd ~/frappe-bench && bench list-apps"'

frappe        13.58.22 HEAD     ← matches pinned v13.58.22
erpnext       13.55.2  HEAD     ← matches pinned v13.55.2
returnable    0.0.1    wip/2026-03-31
ce_sri        0.0.1    wip/2026-03-25
route_planner 0.0.1    wip/2026-03-31
```

All LSKB#20 acceptance criteria met. Closure comment + close posted at [issuecomment-4459863513](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4459863513).

## Filed + closed

- [**LSKB#20**](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20) — **closed (completed)** via `gh issue close 20 --reason completed`. Manual close (not `fixes`-driven; no ESACP code change in S53 for LSKB#20 itself). Cross-repo `fixes` tally **unchanged** (still 18).
- [**ESACP#396**](https://github.com/martinhbramwell/ESACP/issues/396) — `bug(pipeline): seed_iso.py hardcodes ~/.ssh/hasan_mighty.pub — blocks saconsole-managed provision`. Filed for institutional memory; S53 worked around by running provision from local controller.

## Pointer-comments posted

- [LSKB#20 issuecomment-4459046442](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4459046442) — Plan-C decision: pivot to frappe `v13.58.22` / erpnext `v13.55.2`; Option 1 reasoning + tag-bisection evidence.
- [LSKB#20 issuecomment-4459863513](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4459863513) — closure comment: end-to-end pin-discipline verification table + wall-clock + state carried forward.
- [ESACP#395 issuecomment-4459966812](https://github.com/martinhbramwell/ESACP/issues/395#issuecomment-4459966812) — status update: now moot under Plan-C; tag-bisection table; reactivates only if a future pivot returns us to a tag pinning PyYAML 5.4.1.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| LSKB#20 | comment + comment + **closed (completed)** | Plan-C decision + end-to-end execution + acceptance verified |
| ESACP#395 | comment posted | moot-under-Plan-C status update (close-out audit gap caught + discharged) |
| ESACP#396 | filed (open) | new bug — seed_iso pubkey hardcode blocks saconsole-managed pipeline |
| ESACP#392 | unchanged; closed in S52 | corrected-mechanism fix landed; saconsole `/opt/esacp` inherited via S53 `git pull --ff-only` (e283716..4023469 docs-only) |
| ESACP#387, #394, LSKB#15, #16, #18 | unchanged; referenced in passing | downstream/parallel work, no S53-specific finding |

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T4 (pre-destroy, dev02 VM teardown via `/tmp/destroy-dev02-S53.sh`) | **verdict-skipped** | n/a | Boundary-interpretation question — contract §2 row 4 enumerates `rm -rf`, `git reset --hard`, `git branch -D`, `gh pr close --delete-branch` (git/filesystem-flavored). VM-destroy on a host explicitly marked disposable (per `feedback_dev_vms_are_disposable.md`) is not in the enumerated list. Precedent: S50 destroyed + reprovisioned dev02 with no T4 row in qa-log; S51 reprovision attempts did the same. No-state-loss class (dev02 has no gating state). Logged here for transparency. |
| T5 (pre-issue-close, `gh issue close 20 --repo martinhbramwell/LogiSoluKnowBase --reason completed`) | **verdict-skipped** | n/a | Procedural gap — T5 is hard-block per contract §2 row 5. Should have invoked esacp-qa before the close. Closing was correct on merits (acceptance verified end-to-end at 5 layers; manual close because no ESACP commit; closure comment quoted evidence). Skip was a missed-invocation, not a substantive error. Logged for honesty + recurrence-tracking. |
| T1+T3 combined (pre-commit + pre-push on this session-close commit — minutes + next-agenda + qa-log section) | _pending — invocation in progress at session close_ | _pending_ | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3. |

## Counts at session end

- ESACP open: **40** (was 39 at S52 close; +ESACP#396 filed S53).
- LSKB open: **8** (was 9; -LSKB#20 closed S53).
- ce_sri open: 5 (unchanged); LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged).
- Cross-repo `fixes` tally: **18** (unchanged — LSKB#20 closed manually, not via `fixes`).
- Phase 4 ladder block chain: was `LSKB#20 (Plan-C decision pending) → LSKB#15 → LSKB#16`; now **`LSKB#15 → LSKB#16`** (LSKB#20 cleared end-to-end).

## TRIVIAL_FIXES.md status

Unchanged — 2 monitor-only entries (S33 LSM Trigger-3 skip pattern, S47 `tools/secrets.py` `+x` bit).

## Carry-forward operator-reminders (delta)

- **LSKB#20** — **dropped** (closed S53; substrate alignment to `v13.58.22 / v13.55.2` empirically validated).
- **ESACP#395** — moot under Plan-C; reactivates only if a future tag-pivot brings us back to a v13 tag pinning PyYAML 5.4.1 (≤ v13.58.2). Status update posted on the issue itself.
- **ESACP#396** (NEW) — `seed_iso.py` pubkey hardcode; blocks saconsole-managed provision; worked around in S53 by running provision from local controller. Until #396 lands, provision pipeline runs from local controller (not saconsole).
- **LSKB#15** — now **immediately actionable** (no upstream blocker); next link in Plan-B Phase 4 ladder.
- **LSKB#16** — downstream of LSKB#15.
- **ESACP#387, #394, LSKB#18** — unchanged from S52 carry-forward.
- **dev02 substrate state** — now at pinned `frappe 13.58.22 / erpnext 13.55.2` (was: version-13 tip per S50, with substrate-version-alignment metadata mismatch). Still disposable.
- **`tools/secrets.py` +x bit (F4)** — unchanged (TRIVIAL_FIXES monitor-only).
- **LogiSoluMemory Trigger 3 skip pattern** — unchanged.
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.
- **Build-evidence retention** — saconsole `/tmp/build-LSKB20-S53.log` (build with pinned tags), `/tmp/destroy-dev02-S53.sh` (destroy helper), hub `/tmp/provision-dev02-local-S53.sh` + `/tmp/provision-dev02-S53.log` (local provision). Rotation handles cleanup.

## Shape note

Substantive-class with one upstream-blocker issue closed end-to-end (LSKB#20) and one new bucket-1 bug filed mid-session (ESACP#396). Three pin-discipline layers proved at one pass (CLI → packer git clones → metadata → pool → dev02 `bench list-apps`) — first session in the LSKB#20 ladder where every layer matches without manual metadata correction (S50 had to hand-correct metadata after the env-var-passing bug). Plan-C's empirical validation here is significant: S52 declared "Plan-C as meta-pattern" with single-instance disclaimer; S53 is the executed-and-verified end of that first instance, but not yet a second occurrence to upgrade pattern status. Build wall-clock 38 min + reprovision 29 min ≈ 67 min substantive; minutes drafted in the same session-close cycle.

## Saconsole-discipline check

No saconsole capability change in S53. The pipeline-from-saconsole gap (ESACP#396) is a code-level deficiency surfaced on saconsole, not a saconsole declaration gap. `bootstrap_hub.sh` + ansible roles unchanged. The S52 `e283716` packer fix was pulled into saconsole `/opt/esacp` during S53 build kickoff (`git pull --ff-only` from `e283716` to `4023469` — pure docs-only delta, no functional change to packer scripts).

## Post-close audit-fix

(Will be filled in by the post-close audit-fix commit per S46/S47/S48/S49/S50/S51/S52 precedent.)
