# Session Minutes — Phase 2B Orphan Orchestration Audit (#211)

**Date:** 2026-04-22 ~07:00–07:30 EDT
**Branch:** `chore/211-orphan-orchestration-audit` (merged to `main` via `c044d93`)
**Issues closed:** #211 (1)
**Issues opened:** #280 (chaos KVM re-implementation follow-up)
**PR:** #281 — merged 2026-04-22T11:27:57Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ 858d631`

## Objective

Close #211 by auditing the three orphan scripts in `orchestration/`
(`chaos/run_scenario.py` + `scenarios.yml`, `fake_attack.py`,
`revertToBaseline.py`), deciding delete / migrate / park-with-plan per
file, and scrubbing active doc refs to deleted scripts.

## Outcome

All three scripts deleted. Chaos scenario design preserved verbatim
in new issue #280 for a KVM re-implementation. Doc scrubs applied to
active docs; historical docs intentionally left alone. Open count
unchanged at **22 → 22** because the follow-up (#280) was filed to
keep the chaos design alive (plan target had been 22 → 21; decision
discussed and approved).

## Design discussion — VBox vs Hyper-V vs KVM for future Windows hypervisor support

Paused the audit mid-session to discuss a design question: if a future
Hyper-V backend is added, is it better to adapt KVM code or the old
VBox code? **Recommendation recorded:** adapt from KVM. The VBox code
is a thin VBoxManage wrapper from Stage 1, predates `hosts_map.yml`,
the pipeline IoC pattern, remote-hypervisor support, and WireGuard
integration — "adapting" it really means rebuilding to the current
architecture anyway. Porting KVM swaps `virsh` → PowerShell cmdlets
(`New-VM`, `Checkpoint-VM`, `Get-VMSnapshot`) inside `virsh.py` /
`snapshot_ops.py` / `vm_power.py`, plus a replacement for
`build_vm_seed.py`'s NoCloud cloud-init injection (Hyper-V uses
unattend.xml or Cloudbase-Init). **Main tradeoff to flag when the
time comes:** SSH + ProxyJump is Linux-centric; Hyper-V needs OpenSSH
for Windows / WinRM / PSRemoting chosen up-front because it shapes
the whole adapter. This discussion is captured here but no code was
changed — if/when a Hyper-V issue is filed, reference this note.

## Per-file disposition

### `orchestration/revertToBaseline.py` — DELETE

VBoxManage-only; VBox permanently retired 2026-03-17 (hardware failure).
KVM equivalent already exists at `tools/pipeline/orchestration/snapshot_ops.py`
(the primitive Phase 2A's #206 rewired to last session). Live callers were
only `platforms/vbox/revert_to_fresh.sh` (reference-only per CLAUDE.md) and
`chaos/run_scenario.py` (also deleted).

### `orchestration/fake_attack.py` — DELETE, no follow-up

Hardcoded `HUB_LAN_IP = "192.168.40.50"` (VBox-era), explicit `TODO: VBox
retired` comment already in source. Targets `target1` which doesn't exist
in current `hosts_map.yml`. Per "not a perfection project" rule: no
follow-up issue filed. If red-team observability resumes, design fresh
against current KVM topology; the fail2ban → Loki regression check is
arguably better-placed inside `validate_observability.py` anyway.

### `orchestration/chaos/run_scenario.py` + `scenarios.yml` — DELETE + file #280

Script was VBoxManage-bound (snapshot/revert plumbing) and called the also-
deleted `revertToBaseline.py`. But `scenarios.yml` had real design value —
ten chaos scenarios with expected Grafana manifestations covering the
current observability stack. **Preserved verbatim in #280** (including the
timing parameters, recoverable from git history for a literal port).

Architectural question from #211 body ("5th Cytoscape quadrant for chaos?")
enumerated in #280 with three options (5th quadrant / per-VM right-click /
CLI-only-first) so the primitive decomposition can precede the UI shape —
deliberately not pre-committed here.

## Files changed

| File | Change |
|---|---|
| `orchestration/chaos/run_scenario.py` | **deleted** (480 lines) |
| `orchestration/chaos/scenarios.yml` | **deleted** |
| `orchestration/fake_attack.py` | **deleted** (207 lines) |
| `orchestration/revertToBaseline.py` | **deleted** (205 lines) |
| `docs/RUNBOOK.md` | Top banner — retired, points at #280; body intact as historical reference for the 10 scenarios |
| `README.md` | Removed `revertToBaseline.py` from dir tree + Snapshot-Based Iteration example |
| `platforms/vbox/PLATFORM.md` | Replaced stale script table with pointer to `tools/pipeline/` (provision.py and chaos/run_scenario.py rows were already broken after Phase 8) |
| `orchestration/requirements.txt` | Trimmed stale comments referencing deleted Stage 1 / 1.5 scripts |

**Intentionally untouched:** `Stage 1.5 completion checklist.md` and
`SETUP_GUIDE.md` — both already explicitly banner-marked historical.

**Remaining `orchestration/` surface after merge:** `validate_observability.py`
(kept per Phase 8 decision) + `requirements.txt`.

## Acceptance verification

- ✅ `./tools/verify_phase7.py` — 6/6 green (dispatcher caps, subprocess
  guard, help loads).
- ✅ `grep -rn` across `tools/` `ansible/` `platforms/kvm/` `scripts/`
  for the four deleted filenames: **zero hits**.
- ✅ Working tree clean after commit; main fast-forwarded cleanly.

## PR + merge

- Commit `a947f65` on `chore/211-orphan-orchestration-audit` (GPG-signed,
  verified). Pinentry succeeded first attempt.
- PR #281 opened with `fixes #211` in the body.
- Merged via `gh pr merge 281 --merge` (branch kept per
  `feedback_keep_merged_branches.md`). `mergedAt` = 2026-04-22T11:27:57Z.
- Merge commit: `c044d93`. #211 auto-closed 2026-04-22T11:27:58Z.

## Plan update

`~/.claude/plans/open-issues-purge.md` Phase 2B row marked ✅ with merge
hash `c044d93` and note that count is 22→22 (not 22→21) due to the
deliberate #280 filing. Plan next hop: **Phase 2C** (#236 — process doc
for umbrella-branch model, no SUT surface).

## State handed to next session(s)

- `main @ c044d93`, working tree clean.
- Open issues: **22** — #48, #65, #138, #153, #156, #157, #181, #187,
  #202, #219, #220, #223, #225, #235, #236, #240, #241, #250, #271,
  #276, #278, #280.
- Plan next hop: **Phase 2C** (#236). Verification: none (policy doc).
  Expected delta: 22 → 21.

## Reminders to user (unresolved concerns)

None live. The Hyper-V design discussion is captured in this minutes
(see "Design discussion" above) but intentionally not filed as an
issue — no active work warrants it yet. If/when Hyper-V support is
on the roadmap, reference this session's discussion for the KVM-adapt
recommendation and the SSH/WinRM/PSRemoting tradeoff.

## File trail

- Phase 2B commit: `a947f65` on `chore/211-orphan-orchestration-audit`
- Merge commit: `c044d93`
- PR: <https://github.com/martinhbramwell/ESACP/pull/281>
- Follow-up issue: <https://github.com/martinhbramwell/ESACP/issues/280>
- Plan status edit: `~/.claude/plans/open-issues-purge.md` (Phase 2B ✅)
- MEMORY.md edits: open-issues line (22 → 22 + Phase 2B entry); new
  "Parked / Future" pointer to chaos orphan audit memory
- New memory file: `memory/project_chaos_orphan_audit.md`
- This minutes: `docs/SessionLogs/2026-04-22-0700-session-minutes.md`
- Prior-session minutes: `docs/SessionLogs/2026-04-21-2100-session-minutes.md`
  (Phase 2A #206/#275 snapshot_ops rewiring)
