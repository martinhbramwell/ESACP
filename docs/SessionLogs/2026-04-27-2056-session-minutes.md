# 2026-04-27 2056 — #308 default dev VM RAM 4 → 6 GiB

## Objective stated at session start
> Land #308 (config(pipeline): default dev VM RAM 4 → 6 GiB in `virt_install.py`) under 1:1:1 — branch, fix, test, PR, merge, close. Sequential plan: #308 this session, #202 next, #306 after. No bundling.

## Outcome
**Achieved.** PR [#309](https://github.com/martinhbramwell/ESACP/pull/309) merged (`fcf83af`); #308 auto-closed via `fixes` trailer. Main tip is `fcf83af`.

## What happened — by step

| # | Step | Result |
|---|---|---|
| A | Pre-session housekeeping commit on main (`9a63372` — 1730 minutes + agenda from prior session) | ✅ pushed |
| B | Survey of `virt_install.py`, `KvmEnv`, `run_stage_1`, `provision.py`, `memory_guard`, `hosts_map.yml` to map every site that touches VM RAM | ✅ |
| C | Mechanism enumeration: A unconditional / B role-conditional plumbing / C `ram_mib` in hosts_map / D virt_install reads role | ✅ presented to operator |
| D | **Operator confirmed Option A** (unconditional 6 GiB) — sized to pain; per-role defaults belong in #202's `templates.yml` | ✅ |
| E | Branch `config/308-default-vm-ram-6gib` cut from `9a63372` | ✅ |
| F | Edit `virt_install.py:18` — `--ram 4096` → `--ram 6144` (1 char change) | ✅ |
| G | Add colocated regression guard `test_virt_install_ram.py` (62 lines, under 80-line cap) — invokes `virt_install_import` with `subprocess.run` stubbed; asserts assembled ssh argv contains `--ram 6144` and no stale `4096` | ✅ PASS |
| H | Operator chose acceptance option (i): mechanism test sufficient (vs ~10-min stage-1 e2e or ~30-min full provisionGeneric) — per `feedback_not_perfection_project.md` | ✅ |
| I | Commit `eb28318`, GPG-signed, conventional `config(pipeline)` scope, `fixes #308` trailer, Co-Authored-By trailer | ✅ |
| J | Push branch + open [PR #309](https://github.com/martinhbramwell/ESACP/pull/309) | ✅ |
| K | Merge via `gh pr merge 309 --merge` (merge commit, branch retained per `feedback_keep_merged_branches.md`) | ✅ `mergedAt: 2026-04-28T00:56:24Z` |
| L | `git pull --ff-only` on main → `fcf83af`; #308 auto-closed | ✅ |

## Mechanism note (for future reference)

`memory_guard.check_memory()` reads RAM from `virsh dominfo` dynamically — there is no constant in the guard that needed updating alongside the `virt_install.py` literal. Useful to remember when the next RAM tweak comes.

## Acceptance gap (intentional, not a blocker)

The issue body's stated checkbox — "dev0N build via addHost → provisionGeneric come up with 6 GiB" — was **not** exercised this session. The mechanism test confirms the assembled ssh argv contains `--ram 6144`; the next time dev03 is cold-provisioned for unrelated reasons, the dominfo will confirm the e2e half. Per `feedback_not_perfection_project.md` this is sized to pain, not gating.

## State at session close

- **main tip**: `fcf83af` (clean tree, no PRs ahead)
- **dev02**: V14, 6 GiB, running (untouched this session)
- **dev01**: still shut down per strict 1-VM rule
- **Open issues**: 24 (closed #308; opened none — net −1)
- **Branch retained**: `config/308-default-vm-ram-6gib` (per keep-merged-branches policy)

## Reads for the next session

- These minutes
- `2026-04-27-2056-next-agenda.md` (queues #202 per the operator-approved sequence)
- #202 issue body (cloud-init from template + `hosts_map.yml`; `priority: high`, ladder dependency)

## Branch / commit policy

- 1:1:1 honoured: 1 issue (#308) = 1 branch (`config/308-default-vm-ram-6gib`) = 1 session.
- Session-start docs commit (`9a63372`) was prior-session residue (1730 minutes/agenda), landed direct-to-main per housekeeping convention before branch was cut.
- Session-close minutes + next agenda land direct-to-main (this commit) — same convention.
