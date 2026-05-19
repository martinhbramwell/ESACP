# Session Minutes — 2026-04-19 08:05 EDT

**Objective (from 2026-04-18-2205 agenda):** Execute Acceptance Matrix Run 01 — `./rebuild_saconsole.sh` (no arg = `all`) under a Playwright observer (`accept-01-cli-saconsole.spec.js`), asserting topology convergence and hub health.

**Outcome:** Objective partially delivered. Run 01 Playwright spec + param file authored and committed. First launch surfaced a latent bootstrap race (**#231**) that had been hiding behind lucky relative timing since Stage 2.2. User suspended 1:1:1 mid-session to pursue root cause. Race fully diagnosed via auth.log + cloud-init log timestamp correlation, fixed with belt-and-braces (bash + Ansible), verified live by fresh destroy+bootstrap+verify cycle, and shipped via **PR #232** (merge commit `48b7226`). **#231 closed** at 12:03:32Z. Full Playwright end-to-end green not yet recorded — deferred to a clean-replay session.

---

## What actually happened

### Phase 1 — spec authoring (as planned)

- Created `internal_docs/SessionLogs/acceptance-matrix/params/01-cli-saconsole.yml` from the agenda's canonical snippet, with one adjustment agreed with user: `wait_budget_seconds` bumped from 600 to **18000** (the agenda value was inconsistent with the known ~3–4 h rebuild duration per #225).
- Created `prototypes/cytoscape/tests/accept-01-cli-saconsole.spec.js` — spawns `rebuild_saconsole.sh` via `child_process.spawn`, observes Cytoscape UI, asserts subprocess exit 0, UI convergence ≤300 s, 5 WG peers, 8 obs containers, sync_check green, blast radius held.
- Commits `aa0ff85` (spec + params), `0e33a1e` (headless default), `b64bc36` (fix: `test.use()` hoisted out of `describe` — Playwright refuses it inside a describe group).

### Phase 2 — first run, failure

Launched Playwright spec in background. After 2h 40min:
- Phase A (backup, ~2h 38min) ✅ archive at `~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-2238.*`
- Phase B (teardown) ✅
- Phase C (bootstrap) partial — Phases 1–6 ran; Phase 7 Ansible Play 1 failed on `TASK [Gathering Facts]`: `fatal: [saconsole]: FAILED! => {"msg": "Missing sudo password"}`
- Phase D not reached
- Hub offline, full mesh down (0 WG peers, 30/12/8 sync_check)

### Phase 3 — root cause

User challenged my first hypothesis ("cloud-init race") as unproven speculation. Dropped it, investigated from scratch:

- SSH'd to the half-built saconsole via toshy. `sudo -l -U you` → `(ALL) NOPASSWD: ALL`. NOPASSWD sudo IS configured — first hypothesis disproven.
- Reproduced Ansible Play 1 against the half-built hub — **succeeded** (`ok=138 changed=82 failed=0`). Race is timing-dependent, not a static misconfiguration.
- `stat /etc/sudoers.d/you` + `stat /var/lib/cloud/instance/boot-finished` + auth.log correlation:

| Saconsole clock | Event |
|---|---|
| 01:17:55 | sshd accepts |
| **01:17:59.797** | **Ansible sudo → `"you : a password is required"`** |
| 01:17:59.877 | cloud-init writes `/etc/sudoers.d/you` (80 ms too late) |
| 01:18:00.453 | cloud-init writes `boot-finished` |

Controller clock ran ~5 s ahead of freshly-booted saconsole before NTP sync, which is why the Playwright log's Phase 7 timestamp (01:18:04 controller time) and the auth.log sudo timestamp (01:17:59 saconsole time) are the same event.

Second problem (not in original failure path but latent): the "Fresh Install" snapshot was being taken BEFORE cloud-init completed — a revert to that snapshot would produce a permanently broken VM, since cloud-init won't re-run once marked done.

### Phase 4 — fix design

User challenged "why a wait loop" — prompting an architectural comparison:

| Option | Mechanism | Verdict |
|---|---|---|
| (a) `cloud-init status --wait` over SSH | target IPC blocks caller | Chosen (primary) |
| (b) cloud-init `phone_home` (true callback) | target POSTs to controller HTTP listener | Overkill for single-host bootstrap |
| (c) Ansible `wait_for` / `pre_task` | readiness lives in Ansible | Chosen (defense-in-depth) |
| (d) Bash polling loop | controller-side poll | Not proposed — (a) already exists |

Belt-and-braces: (a) before Phase 6 snapshot (fixes the snapshot problem too), (c) in `site-kvm.yml` Play 1 `pre_tasks` (inherited by every future caller of the playbook).

### Phase 5 — fix shipped + verified

- GH **#231** filed with full timeline evidence
- Commit `231be5b` — `bootstrap_hub.sh` Phase 5b + `site-kvm.yml` Play 1 `pre_tasks` (`gather_facts: false` + explicit `cloud-init status --wait` with `become: no` + explicit `setup`)
- Verification: `./rebuild_saconsole.sh teardown` → `bootstrap` → `verify`, exit 0 end-to-end:

```
── Phase 5b: Wait for cloud-init to reach 'done' on hub ──
[07:38:55] ✅ cloud-init done.             # 1 s this run (outcome b — cloud-init already done)
── Phase 6: Snapshot 'Fresh Install' ──
[07:38:56] Creating snapshot 'Fresh Install' ...
[07:39:03] ✅ 'Fresh Install'              # safe — post-cloud-init-done
── Phase 7: Ansible provision hub ──
PLAY [Base configuration — all KVM hosts]
TASK [Wait for cloud-init to reach 'done' state (defense-in-depth vs] ***
TASK [Gather facts (now that cloud-init is finished)] ***
[all roles pass, PLAY RECAP ok=138 failed=0]
```

Post-rebuild:
```
$ ssh you@10.10.0.1 'sudo wg show wg0 | grep -c ^peer:'   → 5
$ ssh you@10.10.0.1 'docker ps --format "{{.Status}}" | grep -c ^Up' → 8
$ bash platforms/kvm/sync_check.sh | tail -2 → 44 ✅ / 10 ⚠️ / 3 ❌ (dev02/dev03/target5 pings only)
```

Verification comment posted at https://github.com/martinhbramwell/ESACP/issues/231#issuecomment-4275850082.

### Phase 6 — merge

- **PR #232** opened → merged at **2026-04-19T12:03:31Z**, merge commit `48b7226`.
- **#231 auto-closed** at 12:03:32Z.
- Branch `accept/01-cli-saconsole` retained per `feedback_keep_merged_branches.md`.

---

## Scope boundary breached (flagged, not apologised for)

1:1:1 was explicitly suspended by user direction after first run failure ("tight theorize → test → edit → test loops… ensure the problem is fully understood, corrected and can never return"). Branch shipped Run 01 acceptance artifacts AND the #231 fix together. This is user-sanctioned scope expansion, not scope creep.

---

## Housekeeping

### MEMORY.md updated

- Acceptance-matrix entry: added #231 discovery + fix + PR #232 merge commit. Noted Playwright end-to-end green not yet recorded.

### Pre-rebuild archive

`~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-2238.{xml,qcow2,seed.iso}` (~33 GB) on disk from the failed Run 01's Phase A. Represents the pre-fix saconsole state. **Decision deferred to user** — keep as historical baseline or discharge now that fix is proven.

No archive retained from today's successful post-fix rebuild (verification skipped `backup`). Acceptable because the rebuild process is now reproducible by construction (race fixed at the source).

---

## Audit trail (session-close)

1. **Forward-tense phrases** — all executed or durably homed. "Full Playwright Run 01 clean-replay" → next agenda (durable home below).
2. **GH issues with new findings** — #231 only (posted to the issue before close). All other issue mentions were context only.
3. **PRs opened** — PR #232, `mergedAt = 2026-04-19T12:03:31Z` (non-null confirmed before writing DONE).
4. **Unresolved concerns** — surfaced to user: archive retention decision, deferred clean-replay run.

---

## Carry-forward

- **Run 01 clean-replay** — execute `accept-01-cli-saconsole.spec.js` end-to-end on the fixed bootstrap path, record the canonical matrix baseline. See next agenda.
- **Pre-rebuild archive disposition** — keep or discharge `~/archives/saconsole/saconsole-pre-rebuild-2026-04-18-2238.*` (~33 GB).
- Open issues unchanged from post-session state: #48, #50, #65, #138, #153, #156, #157, #181, #187, #188, #202, #206, #211, #213, #216, #217, #219, #220, #223, #225.
