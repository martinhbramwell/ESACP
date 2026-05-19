# Session Minutes — 2026-04-18 1907

**Objective (declared at start):** Build `platforms/kvm/rebuild_saconsole.sh` step-by-step against live lab state with per-step user approval, executing the rebuild once, landing the script on `main` via PR, and closing **#222**. Session A of the acceptance matrix unblocker — not Run 01 itself.

**Objective outcome:** **Partial — delivered as-chartered + scope gap surfaced.**  Phases A (backup), B (teardown), C (bootstrap), D (verify) all landed on `main` via PR #228 (merge commit `e12a2c2`) and were each tested live against the running lab. #222 closed. Phase E work (discovered during live verify) filed as #226 and #227 for follow-up sessions — no scope-creep into this session.

## Branch + PR

- Branch: `fix/222-rebuild-saconsole` (5 commits, GPG-signed).
- PR: #228 — merged 2026-04-18T23:06:41Z as merge commit `e12a2c2d37a0071323aeff71262917c9bcc4fd0f`.
- Closed: #222 (delivered). Merged-branch kept per `feedback_keep_merged_branches.md`.

## What happened (chronological)

1. **Session-start review** — MEMORY.md + agenda `2026-04-18-0652-next-agenda.md` loaded. `sync_check.sh` → 46 ✅ / 8 ⚠ / 3 ❌ (the 3 expected unprovisioned dev VMs; no unexpected failures). PR #224 (prior matrix-restructure) already merged. Objective stated in one sentence; user acknowledged.

2. **Preconditions cleared** — #222 OPEN; no in-flight provisioning jobs; toshy `/mnt/esacp-disk` 572 GiB free; controller 183 GiB free on `/`; saconsole running, vda 32.5 GiB physical. Archive location + retention agreed: `~/archives/saconsole/`, last-3-generations, not in git. Transport: `virsh vol-download` via `qemu+ssh://` (no sudo on toshy).

3. **Step 1 — pre-rebuild state capture** — libvirt domain, block devices, snapshots, WG peer state (from hub), `hosts_map.yml` + `config/wireguard/keys.sops.yml` hashes recorded as evidence. Committed as `docs/SessionLogs/2026-04-18-0720-saconsole-pre-rebuild-capture.md`.

4. **Phase A — backup (first attempt failed, redesign, second attempt green)**
   - First attempt: `ssh toshiba 'virsh vol-download ... /dev/stdout' > archive.qcow2` dropped at 1.1 GiB (SSH pipe break under sustained throughput). Also failed on `PYTHONPATH=... python3 -c` layering which violated `feedback_shebang_executable.md` / `feedback_invoke_as_executable.md` (user correctly flagged).
   - Redesign: (a) added shell-eval `__main__` emitter to `tools/host_identity.py` + `chmod +x`, replacing the python-prefix hack with `eval "$(./tools/host_identity.py)"`. (b) Switched transport from raw SSH pipe to `virsh -c qemu+ssh://toshiba/system vol-download` writing locally on controller.
   - Second attempt: ran 2h 46m @ ~4 MB/s steady — libvirt RPC ceiling. Produced 32.5 GiB qcow2, both pre-existing snapshots (`Fresh Install`, `Stage 2.2 Baseline`) preserved, `qemu-img info` clean, SHA256 sidecar written.
   - Perf finding (4 MB/s ceiling) + development-quadrant volume right-sizing filed as **#225** (not a #222 blocker — rebuild_saconsole.sh produces a correct archive, just slowly).

5. **Phase B — teardown** (first attempt aborted cleanly, fixed, second attempt green)
   - First attempt: pre-teardown guard passed (listed all 5 other domains, confirmed no shared volumes), then `undefine --remove-all-storage` failed with "cannot delete inactive domain with 2 snapshots".
   - Fix: added snapshot-delete loop before undefine. Snapshots are preserved in the archived qcow2 anyway; destroying them on the live domain is correct.
   - Second attempt: 2 snapshots cleared, domain undefined, both volumes (qcow2 + seed.iso) removed from pool. Dev01 + other VMs unaffected. Committed.

6. **Phase C — bootstrap** — thin delegation to existing `bootstrap_hub.sh`. No decomposition (#220 parked post-matrix). 21 min end-to-end: preflight → seed → upload → virt-install → autoinstall (Phase 5 `wait_ssh`) → Ansible (138 ok / 83 changed / 0 failed / 0 unreachable) → "Fresh Install" snapshot → "Stage 2.2 Baseline" snapshot → handoff (hub pubkey installed on toshiba). Saconsole Id 55, running.

7. **Phase D — verify** (narrow asserts passed; broader sync_check surfaced the scope gap)
   - First attempt failed on SSH because `saconsole` hostname in `/etc/hosts` maps to 192.168.122.10 (hypervisor-side virbr0, unreachable from controller). Fixed by SSH-ing directly to `you@10.10.0.1` over WG, matching `config.sh`'s `VM_USER="${ESACP_VM_USER:-you}"` pattern.
   - Narrow asserts (MCP grafana, Telegram bot, github MCP entry) all green.
   - Broader `sync_check.sh` showed Passed 34 / Warnings 11 / **Failed 12** vs. pre-rebuild baseline of 3. 9 new failures: 8 observability containers (prometheus/grafana/loki/promtail/alertmanager/node_exporter/cadvisor/mcp-grafana) not running, + 0 WG peers on the fresh hub.

8. **Scope-gap decision — halt + investigate + file issues**
   - Correctly attributed: `bootstrap_hub.sh`'s contract is "produce a *fresh* hub"; re-attaching the pre-existing world (containers stored on the old qcow2 only; peer table reconstruction) is the **rebuild coordinator's** job. Not a `bootstrap_hub.sh` bug; a rebuild_saconsole.sh scope gap.
   - Filed **#226** — Phase E-1: start observability stack on fresh hub.
   - Filed **#227** — Phase E-2: re-register pre-existing WG spokes on fresh hub from SOPS keyring.
   - Decided: close #222 with what's on the branch (scope was "the primitive"; primitive exists + tested through Phase D). Phase E is a distinct follow-up under #226 + #227 rather than an overrun of #222. Matches 1:1:1; respects no-monolith-patching (`bootstrap_hub.sh` untouched).

9. **Close-out** — PR #228 body documents phases delivered, test results, known Phase E gaps, rules respected. Full A→B→C→D cycle executed live. Script header fleshed out with end-to-end manual revert procedure from an archived generation + Phase E pointer. PR merged; #222 closed with merge SHA.

## Findings recorded permanently

- **#225** (infrastructure) — Backup transport perf ceiling (~4 MB/s via libvirt qemu+ssh for 32.5 GiB) + development-quadrant volume right-sizing opportunity.
- **#226** (infrastructure) — Phase E-1: start observability stack on fresh hub in rebuild_saconsole.sh.
- **#227** (infrastructure) — Phase E-2: re-register pre-existing WG spokes on fresh hub in rebuild_saconsole.sh.

## Scripts / files now on `main`

| Path | Purpose |
|---|---|
| `platforms/kvm/rebuild_saconsole.sh` | Phases A/B/C/D, header, usage, revert procedure. 217 lines (Phase E pending lifts this further). |
| `docs/SessionLogs/2026-04-18-0720-saconsole-pre-rebuild-capture.md` | Pre-rebuild state evidence. |
| `tools/host_identity.py` | Added `__main__` shell-eval emitter + `chmod +x`. |
| `tools/CLAUDE.md` | Documented the executable emitter. |

## Rules adhered

- Confirm before acting — every phase required explicit user approval; halted on each failure for design conversation instead of patching around.
- No `sed`, no heredocs feeding code — awk used for column extraction; Python text transforms off-script.
- No hardcoded params — hub identity via `tools/host_identity.py`; VM user via `${ESACP_VM_USER:-you}` matching `config.sh`.
- No modification of third-party / parked code — `bootstrap_hub.sh` untouched.
- Conventional Commits + GPG-signed + co-author trailer on every commit.
- GitHub Issues as institutional memory — #225 / #226 / #227 filed immediately upon discovery, before any fix work.
- 1:1:1 — one issue (#222), one branch, one session; scope-gap discoveries routed to separate issues for separate sessions.
- PR merged before session closes — `mergedAt` non-null before writing these minutes.

## Lab state at session close

- `saconsole` running on toshiba, fresh from bootstrap; Phase E pending.
  - `hub has 0 WG peers`.
  - Observability containers not running.
- `dev01` untouched, still running. Its WG peer config points at the hub's unchanged keys + WG IP — once Phase E-2 adds dev01 back on the hub, the mesh should re-establish without controller intervention on the dev01 side.
- Controller `wg0` still up at 10.10.0.2; ping to `10.10.0.1` succeeds; SSH `you@10.10.0.1` works. So controller-hub link is live, just one-directional (controller reaches hub; hub's peer table is empty → hub can't initiate back).
- Archive `~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-0757.{qcow2,seed.iso,xml,sha256}` retained as revert point.

## Memory updated

- `MEMORY.md` open-issues line: #222 removed; #225, #226, #227 added.
- `MEMORY.md` acceptance-matrix line: Session A status updated.
