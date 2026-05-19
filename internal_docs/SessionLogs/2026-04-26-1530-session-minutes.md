# Session Minutes — 2026-04-26/27 — #303 fix (BaRe envars.sh in generic mode)

## Origin

Acted on agenda `2026-04-25-2100-next-agenda.md` ("V13→V14 framework migration on dev02"). Pivoted away from V14 entirely after the very first acceptance step (Stage A substrate prep) surfaced a foundational bug.

## What happened

### Stage A attempt 1 (failed) — surfaced the foundational bug

Operator approved Stage A path (a): restore Pseudo-Co substrate via canonical matrix Run 04 pattern.

```
./tools/esacp.py provisionGeneric dev02 \
  --wizard-mode existing \
  --wizard-arg 20260422_112724-dev01_iridium_blue.tgz
```

Stages 1–9 ran green; final snapshot taken (with a benign duplicate-name WARN from #289 acceptance leftover); B03 `.tgz` rsync'd; `BACKUP.txt` written; then `handleRestore.sh` exit 1:

```
A required symlink '/home/erpadm/frappe-bench-dev0/BaRe/envars.sh'
to a file of environment variables was not found. Cannot proceed.
```

### Initial framing (wrong) — reframed by operator

First-pass framing (filed as #303): "BaRe shouldn't run in generic mode". Operator pushed back:

> BaRe in both generic ERPNext installations, and in the fully customized ERPNext installations, is a clear unavoidable requirement. Which BaRe directory are you using?

Investigation showed three coexisting BaRe states:
- `~/projects/Logichem/PRODUCTION_20260404/BaRe/` — read-only prod snapshot, ships `envars.sh` (full prod, real secrets)
- `~/projects/Logichem/BaRe/` — github BaRe repo, 4 lab-improvement PRs ahead of prod, **missing `envars.sh`**
- `~/frappe-bench-dev0/BaRe/` on dev02 — clone of github BaRe, mirrors the absence

Operator's architectural intent: github BaRe should ship a stripped-down `envars.sh` (no secrets, deployer-populates) modelled on prod.

### Session-objective pivot

Operator declared:
> Shelve all other work until you can use the pipeline to build a generic V13 using a suitably refactored github BaRe to restore B03.

V14 ladder rung deferred. New objective: fix #303 properly across BaRe + ESACP.

### Investigation — env-var surface

Static grep against `handleRestore.sh` + `utils.sh`: 6 vars actually consumed (`ERPNEXT_SITE_URL`, `TARGET_BENCH`, `MYPWD`, `RESTORE_SITE_CONFIG`, `KEEP_SITE_PASSWORD`, `KEYS`). All site-identity boilerplate; no ce_sri-specific content.

Surprise finding mid-investigation: `utils.sh:20` demanded `BaRe/envars.sh` be a **symlink** (`[[ -L … ]]`) — even shipping a real file wouldn't have worked without that gate being loosened.

ESACP side: Stage 4's `render_envars` already produces `/tmp/rendered/envars.sh` on the VM in **both** modes (the existing `envars.sh.j2` template is purely site-identity, no ce_sri content). The fix collapsed to: in generic mode, copy that pre-rendered file to `BaRe/envars.sh` instead of skipping section_c.

### Two-PR fix

| Repo | PR | Commit | Change |
|---|---|---|---|
| BaRe | #7 (closes #6) | `818c37f` (merge), `57086eb` | Add `envars.sh` (real file, safe defaults, no secrets); loosen `utils.sh:20` to accept symlink OR real file; drop `envars.sh` from `.gitignore` |
| ESACP | #304 (closes #303) | `be441a1` (merge), `c68a0a0` | Rename `section_c_bare_symlink.sh` → `section_c_bare_envars.sh`; in generic mode `cp /tmp/rendered/envars.sh → BaRe/envars.sh` (real file); ce_sri-mode symlink path unchanged. `verify.py` `check_bare_symlink` → `check_bare_envars`; accept symlink OR real file |

Filed adjacent issue **#302** (verify-stage `provision_mode` awareness for Stages 3/6/7/8/9) at session start; out of scope for today, deferred.

### Acceptance e2e (passed)

Full destroy + addHost + provisionGeneric on dev02 against ESACP `c68a0a0`:

| Check | Result |
|---|---|
| Pipeline exit 0 | ✅ |
| All stages 1–9 + final snapshot | green |
| Stage 6 section C output | `=== C: BaRe/envars.sh deployment (mode=generic) ===` → `[OK] /home/erpadm/frappe-bench-dev0/BaRe/envars.sh (real file, generic-mode site identity)` |
| handleRestore.sh | `[OK] Golden backup restored` (was exit 1 pre-fix) |
| HTTPS 200 on https://dev02.iridium.blue | ✅ |
| `BaRe/envars.sh` on dev02 | real file, 466 B, 14 vars populated (ERPNEXT_SITE_URL=dev02.iridium.blue, etc.) |
| `tabCompany` four-field canary | `Pseudo-Co` / `PSC` / `CAD` / `Canada` ✅ |

Closing state commit `c5cbd4d` records dev02 WG re-registration.

### Side-effect: #300 third occurrence

Manual `ssh-keygen -R 10.10.0.17` was needed during acceptance verification to clear stale known_hosts entry from the destroy/rebuild cycle. Posted as third-occurrence observation directly to #300 (comment `4327134438`); pattern is now self-evident, scope-stable fix candidates listed in the comment.

## Branch / repo hygiene

- Local BaRe was on stale `fix/117-defer-social-login` (PR-residue from a previous Claude session, merged at `e2d3b89` four commits behind origin/main). Switched to origin/main before branching.
- BaRe untracked file `bkup_cron (copy 1).sh` left alone (operator residue per `feedback_clean_up_your_own_residue.md`).

## State at session close

- ESACP `main` tip: `c5cbd4d` (state commit) preceded by `be441a1` (PR #304 merge)
- BaRe `main` tip: `818c37f` (PR #7 merge)
- Working tree clean
- sync_check: 48 OK / 8 expected warnings / 0 failures
- dev02: HTTPS 200, Pseudo-Co Company present in DB with intact four-field canary, snapshotted as `ERPNext v13 Generic Baseline`
- Open issues: 23 → still 23 (closed #303 + opened #302 = net zero)

## Time accounting

Spanned date change 2026-04-26 → 2026-04-27 UTC. Substantive work concentrated on 2026-04-27 between roughly 07:50–09:25 EDT (commits `57086eb`, `c68a0a0`, `c5cbd4d`, `0546d7a`).

## Session extension — post-original-close work

After the first session-end audit, operator directed three additional units. Following the audit/agenda directive:

### Extension 1: BaRe cleanup tracking issue

Combined the two flagged unresolved concerns (drift review vs `PRODUCTION_*/BaRe/`; envars.sh extension for non-restore BaRe scripts) into a single tracking issue: **martinhbramwell/BaRe#8** ("BaRe cleanup — drift vs production + extend envars.sh for non-restore scripts"). Two sub-tasks documented; per-script follow-up issues to be filed as those scripts get exercised.

### Extension 2: #300 fix (known_hosts cleanup) — PR #305 merged

**Closed via PR #305 / `65e3e63`** at 2026-04-27 13:41 UTC.

| File | Change |
|---|---|
| `tools/pipeline/orchestration/known_hosts_cleanup.py` (new, 42 lines) | Primitive `clear_known_hosts(keys, emit)` — `ssh-keygen -R` per key, idempotent |
| `tools/pipeline/macro/destroy.py` | Step 9 at end of teardown |
| `tools/pipeline/orchestration/host_registration.py` | Defense-in-depth call after registration. Drive-by: replaced inline `subprocess generate_inventory.py` with existing `regenerate_inventory()` primitive |
| `tools/CLAUDE.md` | destroy macro now 9-step; primitives table updated |

Smoke-tested three cases (nonexistent / empty / real entry) — all pass. e2e validation will happen organically the next session that runs a destroy.

Pre-commit ratchet caught growth twice during implementation; resolved by (a) replacing duplicated subprocess logic in host_registration.py with the existing primitive, (b) tightening destroy.py's 8-step docstring list to a 1-line summary. Both files net at their previous baselines.

### Extension 3: V14 branch fast-forward

`feat/v13-to-v14-upgrade-experiment` had zero unique commits vs main; fast-forwarded to current tip `65e3e63`. Pushed to remote (was previously local-only). Ready for V14 work in next session — no rebase friction expected.

## Updated state at extended session close

- ESACP `main` tip: `65e3e63` (PR #305 merge) preceded by `0546d7a` (#300 fix), `37ca83e` (1530 minutes), `c5cbd4d` (state), `be441a1` (PR #304 merge)
- BaRe `main` tip: `818c37f` (PR #7 merge)
- `feat/v13-to-v14-upgrade-experiment` tip: `65e3e63` (matches main)
- Working tree clean
- Open ESACP issues: 23 (closed #300, opened #302; #303 was opened+closed within session)
- BaRe filed-this-session: #6 (closed via PR #7), #8 (open, tracking)
