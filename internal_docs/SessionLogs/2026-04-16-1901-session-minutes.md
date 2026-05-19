# Session Minutes — 2026-04-16 19:01

**Intended objective:** Phase 7 — Dispatcher layer (#195)
**Actual work completed:** Phase 4 recovery (PR #203 landed) + Phase 2 (PR #207 landed)
**Branches merged this session:**
- `fix/192-destroy-macro` → main (PR #203, commit `0134de1`)
- `fix/190-host-registration` → main (PR #207, commit `f877e91`)
**Plan file:** `~/.claude/plans/synthetic-mapping-pretzel.md`

---

## Pre-session state

- `sync_check.sh`: 42 pass / 11 warn / 4 fail (four expected ping failures against unprovisioned dev VMs — `feedback_one_vm_at_a_time.md`; not blockers).
- `internal_docs/Ideas/` untracked (content drafts, not engineering). Added to `.gitignore` this session.
- Prior agenda (`2026-04-16-1620-next-agenda.md`) targeted Phase 7 with Phase 8 deferral for `cmd_destroy`.

---

## What actually happened (in order)

### 1. Phase 7 survey surfaced a regression

Planning Phase 7's `cmd_destroy` migration required routing to `tools/pipeline/macro/destroy.py`. That file did not exist in `HEAD`, despite memory claiming Phase 4 (#192) was DONE. Investigation found:

- PR #203 **open**, never merged. `b9f2256` (Phase 4 commit) was on `origin/fix/192-destroy-macro` only — not an ancestor of `main`.
- `tools/destroy_helpers.py` (208 lines) still live on main, still imported by `esacp.py` and `job_worker.py`.
- `MEMORY.md` had written "Phase 4 (#192) DONE (PR #203)" before the merge completed. Phases 5 and 6 branches were then cut from a main that lacked Phase 4.
- User reaction: "Yet another incomprehensible mess!"

### 2. Root-cause rule captured before moving on

Added [`feedback_pr_merge_before_session_close.md`](../../memory/feedback_pr_merge_before_session_close.md) and linked it from `MEMORY.md`:

> A phase/issue/session is not complete until its PR's `mergedAt` is non-null.
> "PR opened" ≠ "done". Only merged-to-main counts.

### 3. Phase 4 recovery — rebase-and-merge

User delegated technical decisions ("these are details I should not have to worry about"). Execution:

1. Fetched `origin/fix/192-destroy-macro` to scratch branch.
2. Rebased onto `origin/main`. Two conflicts:
   - `tools/job_worker.py`: both halves of the conflict block were **dead code** after the rebase — Phase 5's `build_template` orchestration obsoleted `HUB_SSH/PLATFORMS_PACKER`, Phase 4's `macro/destroy.py` obsoleted `HOSTS_MAP/GROUP_VARS_ALL/KEYS_SOPS/CLOUD_INIT_DIR`. Kept only `from tools.host_identity import ZONE_DOMAINS`.
   - `tools/size_baselines.json`: merge of monolith-size entries. Took HEAD's real sizes (api 907, esacp 883, etc.) plus Phase 4's new orchestration primitives; the ratchet auto-shrinks on commit.
3. Reverted 4 test-artifact files that the #192 branch carried (`hosts_map.yml`, `ansible/inventory/kvm.yml`, `ansible/group_vars/all.yml`, `config/wireguard/keys.sops.yml`) to `origin/main`'s state.
4. Sanity-checked: `py_compile` OK, `from tools.pipeline.macro.destroy import run` importable, GPG-signed commit preserved.
5. `git push --force-with-lease=fix/192-destroy-macro:b9f2256 …` — only force-push this session, on a private feature branch with a lease guard; main never force-pushed.
6. PR #203 re-verified `CLEAN + MERGEABLE`, merged via standard merge commit. #192 autoclosed from the `fixes #192` trailer.

### 4. Nine-phase status sanity check — Phase 2 never started

User asked for the whole-operation status table, noticed **Phase 2 (#190) — host registration primitive** was `⏳ not started`. It had been leapfrogged: execution went 1 → 3 → 4 → 5 → 6 without looping back. This matters for Phase 7: if Phase 7 split the duplicated registration logic into route modules first, Phase 2's dedup would then have to chase it across three new files.

Decision: **do Phase 2 before Phase 7**, in this same session.

### 5. Phase 2 — host registration primitive

Cut `fix/190-host-registration` from `main` (which now includes Phase 4). Refactor:

- `tools/pipeline/orchestration/host_registration.py` (74) — `register_host()` + `HostRegistrationError` / `HostConflictError`.
- `tools/pipeline/orchestration/host_registration_block.py` (35) — YAML block builder + `ZONE_GROUPS` + `MARKER`, split out so `host_registration.py` stays under the 80-line pipeline cap.
- `tools/pipeline/orchestration/vm_state_query.py` (54) — moved from `api._query_provisioned`.
- `tools/pipeline/orchestration/host_cleanup_check.py` (52) — `check_cleanup_needed()` + `HostAlreadyProvisionedError`.

`api.py` endpoints (`/api/hosts/add`, `/api/provision/erpnext`, `/api/provision/erpnext-generic`) each collapsed to a register-or-cleanup-check + `_spawn_job` call. FastAPI `@app.exception_handler` maps primitive exceptions to HTTP 400/409. `re` import removed.

Result: **`api.py` 907 → 742 (−165)**, matches the plan's ~170-line target. PR #207 merged (commit `f877e91`), #190 autoclosed.

### 6. Acceptance — post-merge (wrong order, recorded for next time)

Wrote `tools/verify_host_registration.py` (stdlib-only, hits live uvicorn on :8088) and ran it against the reloaded server. 4/4 pass:

| Case | HTTP | Body excerpt |
|---|---|---|
| Invalid hostname (`BadName`) | 400 | `hostname: lowercase letters/digits/hyphens, must start with a letter` |
| Duplicate hostname (`dev01`) | 409 | `'dev01' already exists in the kvm group` |
| Duplicate virbr0 IP | 409 | `virbr0 IP 192.168.122.21 already used by 'dev01'` |
| Duplicate WireGuard IP | 409 | `WireGuard IP 10.10.0.13 already used by 'dev01'` |

The already-provisioned → 409 path on `/api/provision/erpnext` was not e2e-tested (would need a real VM with a `Baseline` snapshot); primitive source and handler registration were code-reviewed instead.

**Protocol miss:** the verify script was written *after* PR #207 merged. It should have been part of the PR. Captured as a closure concern below.

---

## Design decisions made during the session

1. **Phase 4 recovery via rebase, not re-implementation** — the #192 commit was valid work; rebasing preserved its authorship and avoided duplicated effort. Conflicts were minimal (job_worker was pure dead-code deletion on both sides; baselines are auto-ratcheted anyway).

2. **Exception handlers, not try/except in routes** — `@app.exception_handler(HostRegistrationError)` etc. lifts the 400/409/500 mapping out of every route handler. Primitives stay transport-agnostic (raise `ValueError` subclasses); FastAPI handles the HTTP encoding.

3. **Split YAML-block builder into its own module** — `register_host` naturally runs to ~95 lines with docstrings + the f-string block. Splitting the block builder into `host_registration_block.py` (35 lines) keeps both files under the 80-line pipeline cap without compromising readability. The issue text said "3 primitives"; delivered 4 files (3 primitives + 1 helper).

4. **Acceptance via live uvicorn + stdlib urllib, not TestClient** — `httpx` wasn't available (system Python is PEP-668 protected). The running uvicorn has `--reload`, so it picked up the merged code automatically. Plain `urllib.request.urlopen` is all the test needs.

---

## Acceptance evidence

### Phase 4 (PR #203)
| Criterion | Result |
|---|---|
| `tools/pipeline/macro/destroy.py` on main (75 lines) | ✅ |
| `tools/destroy_helpers.py` deleted | ✅ |
| `cmd_destroy` in esacp.py → thin wrapper (30 lines) | ✅ |
| GPG-signed, merge-committed, #192 autoclosed | ✅ |

### Phase 2 (PR #207)
| Criterion | Result |
|---|---|
| `api.py` shrinks by ~170 lines | ✅ 907 → 742 (−165) |
| Each new file ≤80 | ✅ 74 / 35 / 54 / 52 |
| Exception-handler mapping | ✅ 400, 409×2, 409 — verified live |
| No `subprocess.run` / YAML mutation left inline in api.py | ✅ |
| Pre-commit ratchet | ✅ auto-updated baselines |
| FastAPI app imports, 22 routes (unchanged) | ✅ |

---

## Housekeeping / closure

- `internal_docs/Ideas/` added to `.gitignore` (content drafts, not engineering).
- `tools/verify_host_registration.py` tracked in the closure PR so future regressions can be caught.
- Local branches retained per `feedback_keep_merged_branches`: `fix/190-host-registration`, `fix/192-destroy-macro`.
- `MEMORY.md` corrected: Phase 2 + Phase 4 both marked DONE, open-issues list trimmed (#190, #192 removed; #206 present).

---

## State at end of session

- `main` at the closure PR merge commit.
- **All Gen 3 pipeline extractions done.** Monolith sizes: `api.py` 742, `esacp.py` 811, `job_worker.py` 227. Targets: ≤300 / ≤150 / ≤100. Remaining work is pure dispatcher thinning (Phases 7, 8, 9).
- Open Gen 3 issues: #195 (Phase 7 — next), #196 (Phase 8), #197 (Phase 9).
- Other open issues: #48, #50, #65, #138, #153, #156, #157, #181, #187, #188, #202, #206.
- **New open issue filed this session:** #206 — snapshot_vm subprocess violation (Phase 7 deferral).

## Rules added this session

- [`feedback_pr_merge_before_session_close.md`](../../memory/feedback_pr_merge_before_session_close.md) — "PR opened" ≠ "done". Only merged-to-main counts.
