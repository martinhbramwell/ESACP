# Session Minutes — 2026-04-09 09:40 → 11:30

**Objective:** Develop install_specific.py — standalone VM differentiation script replacing bench execute ce_sri.install calls.

---

## Completed

- **install_specific.py created** (tools/install_specific.py, 700 lines, 37 functions) — standalone Python script with 4 subcommands: phase1, gate, before-install, after-restart
- **phase1 tested on dev01** — BaRe git pull, envars symlink, bash_aliases (skip expected — no templates at /tmp)
- **gate tested on dev01** — BACKUP.txt found, handleRestore ran, "Demo Co" restored in 2 minutes, site healthy
- **before-install tested in full pipeline on dev03** — Refresh triggered via API, full production DB restore (14m40s), install_specific.py before-install ran successfully: ce_sri.conf written, site_config.json patched (developer_mode=1, ce_sri_url), nginx.conf patched
- **api.py updated** — SCP install_specific.py to VM in both Provision and Refresh paths; H4d/H4g replaced with install_specific.py subcommand calls
- **dev03-differentiate.sh updated** — H4d uses install_specific.py, DEFER_SOCIAL_LOGIN=1 added to handleRestore
- **tools/CLAUDE.md updated** — documented install_specific.py subcommands
- **Golden backup committed** — platforms/kvm/golden_backups/20260409_080145-generic_iridium_blue.tgz (1.33MB)
- **Path.home() bug found and fixed** — sudo -u erpadm -E leaves HOME=/root; replaced with user_home() derived from TARGET_BENCH

## Key Decisions

- **Subcommand architecture** — install_specific.py provides phase1/gate/before-install/after-restart; differentiate.sh calls them at the right pipeline stages. Clean separation: Python owns business logic, bash owns orchestration + transport.
- **No diff_match_patch** — nginx/Procfile/supervisor patches use simple string-search + insert-if-absent instead of the old diff_match_patch library
- **HTTP via stdlib urllib** — no requests dependency; auth via `Authorization: token key:secret`
- **No sys.exit() in functions** — only main() exits; avoids #136-class deadlocks
- **Home dir from TARGET_BENCH** — `user_home()` derives `/home/<user>` from bench path, immune to sudo HOME pollution

## Deferred / Next Session

- **after-restart acceptance test** — the API work subcommand (custom scripts, logo, naming series, test data) has zero runtime verification. Needs a VM with gunicorn running + all secrets deployed.
- **Integrate phase1 + gate into differentiate.sh** — currently BaRe clone, envars symlink, handleRestore, bash_aliases are still inline bash in saved scripts
- **dev01/dev02 differentiate.sh regeneration** — stale scripts need fresh provision or manual update
- **Scheduler disabled on dev03** — bench doctor showed "Scheduler disabled/inactive" after restore
- **#136 formal closure** — architecturally solved but needs after-restart passing as acceptance test

## Issues Touched

| Issue | Status | Notes |
|---|---|---|
| #136 | Open | Root cause addressed (standalone script, no sys.exit). Formal close pending after-restart acceptance test |

## VM State at Session End

| VM | State | Notes |
|---|---|---|
| dev01 | shut off | "Demo Co" snapshot with golden backup; generic.iridium.blue site |
| dev02 | shut off | Baseline snapshot |
| dev03 | running | Refresh completed successfully; production DB restored; install_specific.py before-install verified |
| saconsole | running | Observability stack healthy |

## Commit

- `e66e9c4` — feat(kvm): add install_specific.py — standalone VM differentiation script
