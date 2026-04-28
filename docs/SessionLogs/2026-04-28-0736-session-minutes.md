# 2026-04-28 0736 — #202 cloud-init from Jinja2 + hosts_map.yml

## Objective stated at session start
> Land **#202 — `refactor(kvm): generate cloud-init from template + hosts_map.yml`** (priority: high, ladder-support). Path C agreed with operator: minimal scope this session, file `templates.yml` follow-up issue **after** PR merges. 5-minute autoinstall vs cloud-config verify done before drafting plan.

## Outcome
**PR #310 OPEN, awaiting merge.** `mergedAt` null — work is *landed-on-branch*, not *done*. Per `feedback_pr_merge_before_session_close.md`, no DONE claim recorded here.

## What happened — by step

### Pre-flight
- Read [#202 body + comments](https://github.com/martinhbramwell/ESACP/issues/202) and the agenda. Mapped the cloud-init landscape: 4 static `cloud-init/<host>/` dirs on disk; only `cloud-init/saconsole/` had a live consumer (`bootstrap_hub/02_build_seed.sh`); 3 target-VM dirs were vestigial since the Phase-7 dispatcher work routed `buildVM` through `tools/pipeline/stages/stage_1_vm_creation/seed_iso.py`.
- Filed pre-flight finding on #202 ([comment 4334856318](https://github.com/martinhbramwell/ESACP/issues/202#issuecomment-4334856318)): the issue body's "buildVM is broken" claim was stale post-Phase-7.
- Enumerated 3 mechanism paths (A/B/C); recommended C; operator approved.

### Verify (5 min, before plan)
- `bootstrap_hub/04_create_vm.sh` invokes `virt-install --location` with `--extra-args 'autoinstall ds=nocloud'` — that's subiquity ISO install, requires `#cloud-config` + `autoinstall:` schema.
- `seed_iso.py` (target-VM) builds plain `#cloud-config` for qcow2-imported VMs.
- **Verdict**: structurally different formats; cannot share one renderer. Plan finalised on a hub-only renderer that mirrors the target one's shape.

### Implementation (single commit `ec56f2c`)
- **Add** `platforms/kvm/cloud-init/hub-autoinstall.user-data.j2` + `meta-data.j2` (Jinja2; reads from `hosts_map.yml`).
- **Add** `tools/pipeline/orchestration/hub_seed_iso.py` (76 LOC, under 80-line cap) — renderer + `cloud-localds` shim. Standalone-invokable via `PYTHONPATH=$PROJ_ROOT ./tools/.../hub_seed_iso.py`, matching the precedent set by `verify_build_vm.py`.
- **Add** `tools/pipeline/orchestration/test_hub_seed_iso.py` — 3 colocated tests: variable substitution, meta-data exact match, StrictUndefined catches missing keys. All green.
- **Modify** `bootstrap_hub/02_build_seed.sh` (19 → 14 lines) — calls renderer instead of reading static files.
- **Modify** `tools/pipeline/macro/destroy.py` — drop step 8 (`cloud_init_cleanup`); destroy collapses 9 → 8 steps.
- **Delete** 4 vestigial dirs (`cloud-init/{saconsole,toshiba-dev01,toshiba-target1,toshiba-target2}/`).
- **Delete** dead `create_seeds.sh` + `create_vms.sh` (only consumers were retired vbox + stale doc snippets).
- **Delete** `tools/pipeline/orchestration/cloud_init_cleanup.py` primitive.
- **Doc scrubs**: `BuildOutProcedure.md` (§3+§4 → §3), `SystemOverview_tech.md`, `ControlPlaneDesign.md`, `tools/CLAUDE.md` (primitive list + destroy step count).

### Acceptance executed
- `./tools/pipeline/orchestration/test_hub_seed_iso.py` — 3/3 green
- `./tools/pre_commit_size_check.py` — clean (`hub_seed_iso.py` = 76 lines)
- `bash platforms/kvm/sync_check.sh` — 2 ❌ (dev01 carve-out per #278), no new failures
- Render-and-diff of new vs. old `saconsole/user-data` — byte-identical except SSH-key trailer fix (literal `${USER}@${HOSTNAME}` → real comment from `~/.ssh/hasan_mighty.pub`)

### PR
- Opened: https://github.com/martinhbramwell/ESACP/pull/310 (`fixes #202`)
- Diffstat: 21 files, +176 / -443
- State at minutes time: OPEN, `mergedAt: null`

## Decisions logged
- **Path C** (minimal cloud-init refactor; `templates.yml` per-role substrate deferred to follow-up issue) chosen over Path A (kill scope altogether) and Path B (full templates.yml in same session). Reason: per `feedback_not_perfection_project.md`, size fixes to pain. The pain is per-VM dir maintenance — fully addressed by C.
- **Hub renderer kept separate from target renderer** — autoinstall: vs cloud-config: are structurally incompatible because the install methods differ (subiquity ISO vs qcow2 import). Two-renderer split is honest, not a unification candidate.
- **Live hub rebuild deferred** — hub is healthy; render-and-diff plus the next operator-driven `bootstrap_hub.sh` is the live confirmation. Per `feedback_not_perfection_project.md`, not blocking on a destructive test the work doesn't actually need.

## State at session end
- Branch: `refactor/202-cloud-init-templating` @ `ec56f2c`, pushed to origin
- main tip: still `fcf83af` (unchanged this session)
- PR #310: OPEN, `mergedAt: null`
- Open issues: 24 (no change — #202 will close on merge, no new issues filed yet per operator's "file after" decision)
- Sequence position: #308 done → **#202 in-flight (PR open) →** #306 next

## Next session opener
Once PR #310 merges:
1. File `templates.yml` per-role substrate follow-up issue (RAM defaults from #308 / hrms+payments install behaviour from #306 / per-role packages). Reference both #308's [comment 4331594218](https://github.com/martinhbramwell/ESACP/issues/202#issuecomment-4331594218) and the new issue from the merge commit context.
2. Resume operator-approved sequence with **#306** — `feat(generic): provisionGeneric should install hrms + payments by default`.

If PR #310 has not merged, next session reopens with the merge as the first step.
