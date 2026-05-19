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

## Next session opener (superseded — see session-end discussion below)
Original draft: file templates.yml follow-up + proceed to #306. Both happened (PR merged 11:54Z, #311 filed) but the **post-merge discussion produced a direction shift** — see below.

## Session-end discussion — direction shift (2026-04-28)

After PR #310 merged and #311 was filed, the operator surfaced their actual real-world objective: **upgrading the fully customised production ERPNext from V13 to V14**. The dev-VM ladder + matrix + wizard work + #311 + #306 are now framed as **scaffolding** for that, not as the objective itself.

Agent sketched a 7-step pre-migration scaffolding sequence; operator endorsed it. Three operator-supplied data points changed the shape:
1. **No informal customisation inventory exists** — agent's responsibility to produce one
2. **Pipeline can already provision dev VMs from real production BKP** — existing capability, not new work
3. **Production-side backup+restore via BaRe `handle*.sh` is tested** — rollback is rehearsal, not build

The 7-step sequence + plan now lives at [`~/.claude/plans/production-v14-migration-prep.md`](../../../home/hasan/.claude/plans/production-v14-migration-prep.md). The MEMORY.md "Short-Term Priority" entry was updated to match the new framing. The next-agenda was re-written to point at step 2 (customisation inventory) as the next session's objective, not #306.

#306 and #311 are deferred (still on the books, no longer immediately-next). Wizard/replay bugs, #280 chaos, #219 cytoscape decomp, #187 esacp.py, etc. are explicitly **not** on the v13→v14 critical path.

**Next session: customisation inventory (step 2 of the migration-prep plan).** See agenda for pre-flight + scope.
