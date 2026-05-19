# Session Minutes — #220 Run 01 Acceptance (saconsole rebuild via decomposed bootstrap_hub.sh)

**Date:** 2026-04-22 ~19:50–21:00 EDT
**Branch:** `refactor/220-saconsole-decomposition` → merged to `main`
**Merge commit:** `a8fac0e` (merge-commit, 2026-04-22 20:55 EDT)
**PR:** #287 (merged)
**Issues closed:** #220
**Issues opened:** #288 (cleanup-decision follow-up)
**Baseline:** entered at `main @ 5230522` (prior 1903 minutes); exited at `a8fac0e`

## Declared objective

Run 01 acceptance for #220 — live saconsole destroy + rebuild against the
decomposed `bootstrap_hub.sh`, preserving the outgoing qcow2 on toshy
(**no copy to controller**, **out of sight of virsh for the rebuild
name slot**).

## Scope decisions taken mid-session

1. **Preserve mechanism reframed** — initial plan was `sudo mv` the
   qcow2+seed.iso outside the libvirt pool path, into
   `/mnt/esacp-disk/preserved/saconsole-<TS>/`. Operator reframed the
   constraint: "out of sight of virsh" actually meant "no name clash at
   rebuild", not physical separation from libvirt. **Rename-in-place to
   `saconsole_old-2026-04-22-1951.{qcow2,-seed.iso}`** achieves that
   without sudo — hasan on toshy is in the `libvirt` group and the pool
   directory (`drwxrwxr-x root:libvirt`) is group-writable, so `mv`
   within it works directly over `ssh toshy`. Dropped the preserved/
   subdirectory approach entirely.
2. **Merge method** — merge-commit, consistent with recent Phase 7/8/9
   PRs (bf6bdfb, dfcddc9, abab6ef).
3. **#227 scope** — WG-spoke re-enrollment for non-controller spokes
   stayed out of scope. The **controller** spoke was re-enrolled
   automatically by Play 5 of the Ansible provision, which was enough
   for Phase D acceptance. No non-controller spokes currently exist on
   the mesh, so #227 remains open but dormant.
4. **Preserved-files retention** — not decided in-session. Filed as
   #288 so the 33 GiB and domain XML don't become orphan-forever.

## Phase-by-phase log

### Phase 0 — Pre-flight (read-only)
- Checked out `refactor/220-saconsole-decomposition @ 06da8a6`; 12
  phase files present under `platforms/kvm/bootstrap_hub/`.
- toshy inspection: saconsole running (id 61), dev01 running (id 82),
  saconsole.qcow2 at 33.2 GiB in the `esacp` pool, 2 internal
  snapshots (`Fresh Install`, `Stage 2.2 Baseline`), no sibling domain
  references saconsole's volumes, 579 GB free on /mnt/esacp-disk.
- Dumped domain XML to `/tmp/saconsole-preserved-2026-04-22-1951.xml`
  (5.7 KiB) for revert.

### Phase 1 — Preserve on hypervisor (in-place rename, no sudo)
- `virsh shutdown saconsole` → `shutoff` in 8 s (ACPI behaved this
  time — known-flaky per `project_saconsole_acpi_shutdown.md`).
- `ssh toshy 'cd /mnt/esacp-disk/var/lib/libvirt/images/ && \`
    `mv saconsole.qcow2 saconsole_old-2026-04-22-1951.qcow2 && \`
    `mv saconsole-seed.iso saconsole_old-2026-04-22-1951-seed.iso'`
- `scp` the domain XML to `~hasan/saconsole-preserved-2026-04-22-1951.xml`
  on toshy (self-contained revert bundle).
- `virsh pool-refresh esacp` → renamed files visible under new names.
- `virsh undefine saconsole --snapshots-metadata --managed-save --nvram`
  (no `--remove-all-storage`; files already renamed away from the
  paths in the domain XML).
- Verified: `virsh list --all` shows no saconsole; `vol-list esacp`
  shows only `saconsole_old-*` entries.

### Phase 2 — Rebuild via decomposed `bootstrap_hub.sh` (acceptance target)
- Invoked in background: `bash platforms/kvm/bootstrap_hub.sh`
- Exit 0, **39 min wall time** (20:09 → 20:48 EDT).
- All 12 phase files executed in sequence: `01_preflight` → `02_build_seed`
  (reused cached ISO — user-data/meta-data unchanged) → `03_upload_seed`
  (fresh upload, REMOTE_MTIME=0 since the old file was renamed) →
  `04_create_vm` → `05_wait_ssh` → `05b_wait_cloud_init` →
  `06_snapshot_fresh` → `07_ansible_provision` → `08_snapshot_baseline`
  → `09_handoff` → `99_summary`.
- Ansible 5-play recap: `ok=140 changed=83 unreachable=0 failed=0 skipped=3`.
- Transient retries during observability cold-start: 5× on Grafana,
  4× on Loki — Ansible `until` retries, not failures.
- Snapshots created: `Fresh Install`, `Stage 2.2 Baseline`.
- Handoff: hub SSH pubkey installed on toshy, /etc/hosts updated,
  known_hosts seeded, stale pubkeys swept.

### Phase 3 — Acceptance verify
- `bash platforms/kvm/rebuild_saconsole.sh verify` (Phase D only):
  - ping 10.10.0.1 (hub on WG) ✅
  - SSH `you@10.10.0.1` via WG ✅
  - sync_check: all 11 asserted hub-critical + observability rows green
    (MCP grafana, Telegram, github MCP, prometheus, grafana, loki,
    promtail, alertmanager, node_exporter, cadvisor, mcp-grafana).
- Overall sync_check: 44 ✅ / 13 ⚠ / 0 ❌ (baseline 46 ✅ / 11 ⚠ / 0 ❌).
  The 2 ✅→⚠ moves are both about the working-tree being on the
  refactor branch — they revert on merge (and did).

### Phase 4 — Close-out
- Acceptance comment posted on PR #287.
- PR un-drafted via `gh pr ready 287`.
- Merged into main via `gh pr merge 287 --merge` → `a8fac0e`.
- Local pull of main fast-forwarded clean.
- #220 auto-closed by `fixes #220` in PR body; added belt-and-suspenders
  comment with merge SHA.
- #288 filed for preserved-files retention decision (not urgent; no
  disk pressure).

## Files landed via PR #287 (on main)

| File | Change |
|---|---|
| `platforms/kvm/bootstrap_hub.sh` | 425 → 65 lines (thin orchestrator) |
| `platforms/kvm/bootstrap_hub/_helpers.sh` | new (68) |
| `platforms/kvm/bootstrap_hub/01_preflight.sh` | new (27) |
| `platforms/kvm/bootstrap_hub/02_build_seed.sh` | new (19) |
| `platforms/kvm/bootstrap_hub/03_upload_seed.sh` | new (16) |
| `platforms/kvm/bootstrap_hub/04_create_vm.sh` | new (40) |
| `platforms/kvm/bootstrap_hub/05_wait_ssh.sh` | new (53) |
| `platforms/kvm/bootstrap_hub/05b_wait_cloud_init.sh` | new (18) |
| `platforms/kvm/bootstrap_hub/06_snapshot_fresh.sh` | new (4) |
| `platforms/kvm/bootstrap_hub/07_ansible_provision.sh` | new (20) |
| `platforms/kvm/bootstrap_hub/08_snapshot_baseline.sh` | new (4) |
| `platforms/kvm/bootstrap_hub/09_handoff.sh` | new (72) |
| `platforms/kvm/bootstrap_hub/99_summary.sh` | new (35) |
| `platforms/kvm/CLAUDE.md` | note new layout |
| `tools/pre_commit_size_check.py` | +18 lines (`.sh` support + new category) |
| `tools/size_baselines.json` | +13 baseline rows |

## Artifacts on disk (outside the repo)

| Location | Contents |
|---|---|
| `toshy:/mnt/esacp-disk/var/lib/libvirt/images/saconsole_old-2026-04-22-1951.qcow2` | preserved hub qcow2 (33.2 GiB, carries `Fresh Install` + `Stage 2.2 Baseline` internal snapshots) |
| `toshy:/mnt/esacp-disk/var/lib/libvirt/images/saconsole_old-2026-04-22-1951-seed.iso` | preserved seed ISO (375 KiB) |
| `toshy:~hasan/saconsole-preserved-2026-04-22-1951.xml` | preserved domain XML (5.7 KiB) |
| `controller:/tmp/saconsole-preserved-2026-04-22-1951.xml` | controller-side copy of XML (volatile, reboot-lost) |
| `controller:/tmp/bootstrap_hub-2026-04-22-1951.log` | full bootstrap run log (635 lines) |

Retention policy: tracked in #288.

## Memory updates

- `memory/MEMORY.md`:
  - Open-issue count unchanged at 18: **closed #220**, **opened #288**.
  - Swap `#220 (in PR)` for `#288 (retention decision)` in the ledger.
  - Drop the `refactor/220-saconsole-decomposition` pending-merge note.
- New feedback memory: `feedback_enumerate_mechanisms_before_committing.md`
  — before committing to a mechanism, enumerate the underlying goal and
  2–3 paths to it. Boundary-crossings (new sudo, new script, new
  capability) are prompts to re-examine the problem, not to escalate.
  Provenance: this session's sudo-vs-rename reframe.

## Acceptance verification summary

- ✅ Decomposed `bootstrap_hub.sh` runs end-to-end on a live rebuild.
- ✅ Every phase file in `platforms/kvm/bootstrap_hub/` invoked.
- ✅ Ansible `failed=0`.
- ✅ Both pipeline snapshots created.
- ✅ Hub reachable over WG, SSH works.
- ✅ 11 hub-critical sync_check rows green.
- ✅ PR #287 merged (`mergedAt` non-null: 2026-04-23T00:55:38Z).
- ✅ #220 closed (`closedAt` non-null: 2026-04-23T00:55:39Z).

Per `feedback_pr_merge_before_session_close.md`: both `mergedAt` and
`closedAt` are non-null before this minutes is written.

## State handed to next session

- `main @ <this minutes commit>` (after minutes commit+push).
- **Open issues: 18** —
  #48, #65, #138, #153, #156, #157, #187, #202, #219, #223, #235, #240,
  #241, #278, #280, #284, #285, **#288** (preserved-files retention).
- Short-term priority: **ERPNext V13 → V16** with SRI / QR bottles /
  delivery routes / bespoke customizations. Gate: zero open issues.
  Plan file `project_upgrade_v13_to_v16.md` remains a parked stub.
- The 17 non-#288 open issues still deserve mission-alignment passes
  against V13→V16 before scoping (per 1903 minutes' recommendation
  to re-draft `~/.claude/plans/open-issues-purge.md`).

## Reminders to user (unresolved concerns)

1. **`project_upgrade_v13_to_v16.md` is still a stub.** A dedicated
   planning session to flesh it out (scope, approach, sequencing, test
   strategy) remains the natural next gate before any V16 code work.
2. **Open-issues purge plan is stale.** Phase 3B's bundle assumption
   collapsed and the V13→V16 priority reset the frame. Worth
   re-drafting `~/.claude/plans/open-issues-purge.md` against the new
   priority before picking the next open-issue session.
3. **#288 — preserved-files retention decision.** Not urgent (33 GiB
   on a disk with 579 GB free), but worth a disposition call within a
   few weeks before it ages out of memory.
4. **#227 (WG spoke re-enrollment) remains open but dormant.** New
   empirical finding posted as issue comment: Play 5 auto-re-enrolls
   the controller's own spoke, so #227's remaining scope is
   non-controller spokes only. No non-controller spokes currently exist
   on the mesh. Finding comment:
   <https://github.com/martinhbramwell/ESACP/issues/227#issuecomment-4301029085>

## File trail

- Merge commit: `a8fac0e` on `main`
- PR: <https://github.com/martinhbramwell/ESACP/pull/287>
- Closed: <https://github.com/martinhbramwell/ESACP/issues/220>
- Opened: <https://github.com/martinhbramwell/ESACP/issues/288>
- #227 finding comment: <https://github.com/martinhbramwell/ESACP/issues/227#issuecomment-4301029085>
- New feedback memory: `feedback_enumerate_mechanisms_before_committing.md`
- Updated memory: `MEMORY.md` (issue ledger swap)
- This minutes: `internal_docs/SessionLogs/2026-04-22-1951-session-minutes.md`
- Prior minutes: `internal_docs/SessionLogs/2026-04-22-1903-session-minutes.md`
  (Phase 3B saconsole bundle)
