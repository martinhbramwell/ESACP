# Session Minutes — 2026-04-08 22:30 → 2026-04-09 09:15

**Objective:** Refactor install.py into functional, modular, idempotent install pipeline.

---

## Completed

- **install.py analysis** — full overview: 1360 lines, 16 tasks, runs on VM as erpadm, depends on 8+ config files, no FP compliance
- **Architecture designed** — split into `install_generic.py` (bench+site+erpnext) and `install_specific.py` (BaRe+envars, future: ce_sri app)
- **install/result.py** — frozen `Result(success, value, error)` replaces `sys.exit()` everywhere
- **install/config.py** — frozen `Config` dataclass, secrets from `~/.ssh/secrets/ce_sri.txt` (never CLI args), `FRAPPE_PYTHON_MAP` derives Python version per Frappe branch
- **install/generic/** — 5-step orchestrator:
  1. `ensure_bench.py` — `bench init --python python3.10 --frappe-branch version-13`
  2. `ensure_erpnext.py` — `bench get-app erpnext` (source only, before new-site)
  3. `pin_deps.py` — force-pin 12 packages that `uv` resolves incompatibly for v13
  4. `ensure_site.py` — `bench new-site --install-app erpnext` (atomic, avoids Module Def duplication bug)
  5. `snapshot.py` — superseded by BaRe approach (can be pruned)
- **install/specific/** — Phase 1 orchestrator:
  1. `ensure_bare.py` — copy BaRe tools to bench dir
  2. `ensure_envars.py` — render envars.sh + BaRe/envars.sh symlink
  3. Optional: `--take-backup` runs handleBackup.sh
- **dev01 rebuilt from scratch** — Ubuntu 24.04 autoinstall via cloud-init, Python 3.10 (deadsnakes), all OS prereqs
- **Ubuntu 26.04 beta attempted and rejected** — deadsnakes PPA not available for Resolute Raccoon, Python 3.14 incompatible with Frappe v13
- **Frappe v13 dependency battle resolved** — `bench 5.29+uv` pulls incompatible modern packages; `pin_deps.py` forces cryptography~=3.4.7, pyOpenSSL~=20.0.1, urllib3~=1.26.4, redis~=3.5.3, etc.
- **Golden backup taken** — `20260409_080145-generic_iridium_blue.tgz` (1.4MB), BaRe-compatible, copied to controller at `platforms/kvm/golden_backups/`
- **VM snapshots**: "Fresh Install" (clean Ubuntu 24.04) + "Demo Co" (ERPNext + wizard + BaRe)
- **Hosts entry**: `127.0.0.1 generic.iridium.blue` added to Mighty /etc/hosts

## Key Decisions

- **Secrets from file, not CLI** — `~/.ssh/secrets/ce_sri.txt` (KEY=VALUE), never exposed as arguments
- **Executable shebanged scripts** — `./install_generic.py` not `python -m ce_sri.install.generic`
- **get-app before new-site** — avoids Frappe v13 Module Def duplication bug; `--install-app erpnext` flag on `bench new-site` does atomic install
- **pin_deps after get-app** — get-app's pip install undoes earlier pins; must re-pin afterwards
- **BaRe backup as golden snapshot** — replaces raw `bench backup`; handleRestore-compatible with site-name morphing
- **Python version parameterized** — `FRAPPE_PYTHON_MAP` in config.py maps branch → interpreter, ready for v13→v16 upgrade path
- **snapshot.py superseded** — the BaRe approach is better; snapshot.py can be pruned or repurposed

## Deferred / Next Session

- **install_specific.py Phase 2** — ce_sri app install, API keys, certs, nginx/supervisor patches, naming series, test data (the post-restore work from old install.py tasks 5–16)
- **Prune snapshot.py** or repurpose to use BaRe format
- **Commit ce_sri repo changes** — install/ package, install_generic.py, install_specific.py
- **Commit ESACP repo** — golden_backups/
- **Remove `/etc/hosts` entry** for generic.iridium.blue when no longer needed
- **`after_restart`** — still needs implementing (blocked by Phase 2)
- **#136** — bench execute deadlock: solved by architecture (no sys.exit in Frappe context)
- **views.ddl MariaDB auth** — handleBackup.sh runs `mysql` as user `you` without credentials; non-fatal for Demo Co but needs fixing for production backups

## Issues Touched

| Issue | Status | Notes |
|---|---|---|
| #136 | Open | Root cause addressed by architecture (no sys.exit, Result type). Formal fix pending Phase 2 + acceptance test |

## VM State at Session End

| VM | State | Snapshots |
|---|---|---|
| dev01 | running | Fresh Install, Demo Co |
| dev02 | shut off | Baseline |
| dev03 | shut off | Baseline, ERPNext v13 Logichem DB Restored |
| saconsole | running | Fresh Install, Stage 2.2 Baseline |
