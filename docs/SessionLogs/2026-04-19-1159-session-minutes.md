# Session Minutes — 2026-04-19 11:59 EDT

**Objective (entered with):** Acceptance Matrix Run 01 clean-replay.

**Objective (pivoted to after user direction):** Matrix Run 02 (CLI) — dev VM full Logichem ERPNext restored from golden backup.

**Outcome:** Run 02 **halted** before Playwright execution. Pre-existing CLI ↔ API transport asymmetry surfaced: the CLI has no host-registration subcommand, blocking the destroy → re-register → rebuild cycle required by every CLI-transport matrix run. Four GitHub issues filed (#233, #234, #235, #236). Dev01 destroy state committed to `main` (`2360ed8`). Next session targets **Issue #233 (addHost)** as the unblocker for Run 02.

---

## What actually happened

### Pivot: Run 01 → Run 02

User opened with: *"I'm sufficiently confident in our saconsole rebuild cycle for the time being. I want to move on to the remaining 6 UI & CLI tests of VM dropping and rebuilding."* 1:1:1 discipline applied — today = Run 02 only; Runs 03–07 each get their own session. Pre-rebuild archive retained (decision: keep). Run 01 clean-replay formally waived; `feedback_test_real_before_commit.md` is satisfied by the live-verified #231 fix on 2026-04-19 07:38 even though the canonical Playwright green was never recorded.

### Investigation (read-only, "Path C" from the dialogue)

The agenda's proposed `./tools/esacp.py provision --params …yml` command was not executable: the CLI only accepts a positional `vm` argument. Read-only trace of `tools/cli/provision.py:13-44` → `tools/pipeline/macro/provision.py` → `stage_3_connectivity/backup.py:10-38` revealed the actual variant/backup input mechanism:

- **Backup source:** `~/projects/Logichem/ce_sri/BKP/` directory; `BACKUP.txt` names the active tarball. Rsynced to the VM; stage 7 restores via `BaRe/handleRestore.sh`.
- **Variant selection** is declared by presence/absence of `BACKUP.txt` — not by any CLI flag. "Full Logichem" vs "skeletal" is a state-of-the-BKP-dir question.

Confirmed live backup pointer is `20260404_162416-erp_logichem_solutions.tgz` (255 MB). User's earlier mention of `~/archives/production/20260419_072801-…tgz` retracted as mistake.

**Resolution — Path D (declarative):** param file becomes documentation of required `BKP/` + VM state; Playwright asserts state → single-subprocess `./tools/esacp.py provision <vm>`. No CLI flag added, no SUT mutation.

### Canary capture from live dev01

Mission-aligned canary: **Company** record via ERPNext REST API (the surface ERPNext MCP will use per `memory/mission_vision.md`). Admin password loaded from `tools/secrets.py` (env > SOPS). Login + `frappe.client.get_list` returned:

- Company: `Logichem Solutions S. A.` (1 record)
- Customer count: 1801

Canary identifier pinned: post-rebuild `GET /api/method/frappe.client.get_list?doctype=Company` must return a list containing `"Logichem Solutions S. A."`. Helper will be reused by Run 05 (UI parity).

### Dev01 destroy (out-of-matrix setup, user-approved)

`./tools/esacp.py destroy dev01` (with `yes` input piped) executed all 8 steps cleanly:

1. WG peer removed from hub
2. VM + 2 snapshots destroyed on toshy
3. `hosts_map.yml` — dev01 block removed
4. `group_vars/all.yml` — `wg_pubkey_dev01` removed
5. Inventory regenerated
6. Hub `wg0.conf` updated via Ansible
7. `keys.sops.yml` — dev01 + PSK removed
8. Cloud-init directory cleaned

`virsh list --all` confirmed: only `saconsole` running. Working tree: 4 modified files (hosts_map.yml, group_vars/all.yml, inventory/kvm.yml, keys.sops.yml).

### Halt — CLI transport asymmetry

Next step would have been `./tools/esacp.py provision dev01`, but `kvm_hosts(config).get("dev01", {})` now returns `{}` — the destroy correctly removed dev01 from `hosts_map.yml`, and **the CLI has no subcommand to re-register it**. Only `POST /api/hosts/add` calls the `host_registration.register_host` primitive.

**Root-cause survey** (git log + API route enumeration):

- `a190475` (2026-03-02): original `esacp.py` — 10 subcommands, no host registration (workflow was hand-edit `hosts_map.yml` + `buildVM` + `provisionVM`).
- `4399a1b` (2026-03-21): Cytoscape UI + FastAPI added; `POST /api/hosts/add` introduced for UI only. CLI never gained the symmetric surface.
- `ebe2124` (2026-04-16, #190): `host_registration` primitive extracted — still consumed only by three API routes.

Gap has existed since 2026-03-21. Not a regression — the matrix is the first workflow to exercise destroy → re-register → rebuild via CLI transport. Previous CLI usage was always provision-once against pre-registered hosts.

17 FastAPI endpoints total; **only 2 have CLI equivalents**. 15 are API-only. Matrix-blocking subset: host-add (Runs 02/03/04) and provision-generic (Run 03).

### Issues filed

| # | Title | Scope | Status |
|---|---|---|---|
| **#233** | `feat(cli): addHost subcommand for symmetric CLI/UI host registration` | Blocks Run 02 | Open — next session |
| **#234** | `feat(cli): provisionGeneric subcommand (skeletal ERPNext + wizard)` | Blocks Run 03 | Open — later |
| **#235** | `audit(tools): CLI/API transport parity gap survey` | Tracker for 13 non-blocking asymmetries | Open — post-matrix |
| **#236** | `process: adopt umbrella-branch model for multi-session refactors and broad-context work` | Branching-policy discussion (user-raised) | Open — deferred |

### User-raised policy point (#236)

User raised that main is currently accumulating incrementally-tested refactoring PRs without broad-context integration gating, and the correct pattern is a long-lived umbrella branch per multi-session effort with sub-branches per 1:1:1 unit, umbrella merged to main only on full certification. User explicitly deferred adoption — *"Finish this phase, continuing as we were."* — and captured the thinking as #236 for later. No change to current workflow.

### Destroy state committed to main

- Commit `2360ed8` on `main`: `chore(kvm): capture dev01 destroy state (pre-Run-02 setup)` — GPG-signed (G), pushed to `origin/main`.
- Abandoned branch `accept/02-cli-full-logichem` deleted (had no unique commits).

---

## Housekeeping

### Pre-rebuild archive disposition

**User decision: keep.** `~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-2238.{xml,qcow2,seed.iso}` (~33 GB) retained as historical baseline.

### Playwright Run 01 canonical green

Not recorded this session — Run 01 clean-replay formally waived. Live-verified rebuild on 2026-04-19 07:38 stands as the #231-fix acceptance record.

---

## Audit trail (session-close)

1. **Forward-tense phrases** — all executed or durably homed. Next steps captured in next-agenda file (durable home below).
2. **GH issues with new findings** — #233, #234, #235, #236 filed with full context. No existing issues left under-fed.
3. **PRs opened** — none. Single direct commit to main (`2360ed8`) for destroy state capture.
4. **Unresolved concerns** — none carried in-session; all homed to issues or next agenda.

---

## Carry-forward

- **Next session: Issue #233 (addHost CLI subcommand)** — unblocker for Run 02. Agenda: `docs/SessionLogs/2026-04-19-1159-next-agenda.md`.
- **Then Run 02** — on the addHost merge, Run 02 becomes possible. Separate session.
- **Open issues** post-session: #48, #50, #65, #138, #153, #156, #157, #181, #187, #188, #202, #206, #211, #213, #216, #217, #219, #220, #223, #225, **#233**, **#234**, **#235**, **#236**.
