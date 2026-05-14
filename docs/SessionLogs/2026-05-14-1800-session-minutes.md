# 2026-05-14 1800 — Session 51 minutes

## Objective

**ESACP#390 fix** — pass `FRAPPE_BRANCH`/`ERPNEXT_BRANCH` through `sudo env` in all four `execute_command` lines of `platforms/packer/erpnext-v13.pkr.hcl`, unblocking the LSKB#20 Path-1 substrate-version-alignment ladder. Bucket-1 substantive 1:1:1.

## Outcome — #390 fix verified + merged; new downstream blocker ESACP#392 filed

PR#391 merged at `2026-05-14T18:40:51Z` (squash, merge commit `9ef1aa5`). ESACP#390 auto-closed via `fixes #390` at `18:40:52Z`. Direct build-log evidence confirms the env-var-passing flaw is resolved. Acceptance build then crashed on a separate downstream bug (uv pip vs frappe v13.41.3's yanked-braintree pre-release constraint), filed as ESACP#392 — new top-of-block-chain for Plan-B Phase 4.

### What ran cleanly on S51

- **Branch created off main** — `git fetch origin && git checkout -b fix-390-packer-env-vars origin/main` from `e1fdf9a`. Clean working tree.
- **Edit landed** — `platforms/packer/erpnext-v13.pkr.hcl` lines 77/87/100/107: `execute_command` lines now carry explicit `FRAPPE_BRANCH=${var.frappe_branch} ERPNEXT_BRANCH=${var.erpnext_branch}` inside `env`. Phase 2's redundant `environment_vars` block removed; one-line `NOTE:` comment added explaining why the vars must be inside `env`. 1 file changed, 6 insertions, 8 deletions.
- **Pre-commit packer validate** — staged the modified file via SCP to `you@10.10.0.1:/tmp/pkrtest/`, ran `packer validate .` against the temp tree (full packer dir copied alongside). Output: `The configuration is valid.` `packer fmt -check` returned exit 3, but the unmodified original on `main` returns the same exit — pre-existing whitespace drift, not introduced by this PR (out of scope).
- **Commit + push** — `be9b637`, GPG-signed, Conventional Commits `fix(packer):` scope, Co-Authored-By trailer, `fixes #390` body. Push to `origin fix-390-packer-env-vars` clean.
- **PR opened** — [#391](https://github.com/martinhbramwell/ESACP/pull/391) base main, head be9b637.
- **Packer build acceptance** — kicked off detached via `setsid nohup` on saconsole at `13:59:40` (build process PID `3845548`), watcher armed via `kill -0` poll; harness notified on watcher exit at `18:31:49Z`. Wall-clock `~31m` to crash point (Phases 1-5 + 5m39s into Phase 2 packer provisioner).
- **PR merged** — `gh pr merge 391 --squash --delete-branch=false` post-T2 verdict. Merge commit `9ef1aa5`. ESACP#390 auto-closed via `fixes`.
- **Controller + saconsole synced back to main** — both clones fast-forwarded to `9ef1aa5`. Saconsole's `fix-390-packer-env-vars` branch retained per `feedback_keep_merged_branches.md`.

### Direct evidence the #390 fix works

**Pre-fix S50 build log** (per #390 issue body): `git clone https://github.com/frappe/frappe.git --branch version-13 --depth 1 --origin upstream` — script saw `FRAPPE_BRANCH` defaulted because the CLI override was stripped by `sudo -H`.

**Post-fix S51 build log** (`/tmp/build-390.log:1455` on saconsole):
```
[02_bench 14:30:52] bench init /home/erpadm/frappe-bench (frappe v13.41.3) ...
$ git clone https://github.com/frappe/frappe.git --branch v13.41.3 --depth 1 --origin upstream
```

The script now sees `FRAPPE_BRANCH=v13.41.3`. The env-var-passing flaw is resolved. Build crashed in `bench init` before the `bench get-app erpnext` line could exercise `ERPNEXT_BRANCH`, but the same provisioner block carries the same `execute_command` shape — by-construction the equivalent fix applies to the erpnext branch flag.

### G7-class — uv pip refuses frappe v13.41.3 over yanked-braintree pre-release

`02_bench_install.sh` Phase 2 runs `uv pip install --quiet --upgrade -e .../frappe`. Frappe v13.41.3's `pyproject.toml` pins `braintree>=4.8.0,<4.9.dev0`. PyPI yanked `braintree==4.8.0` (`reason: critical bugs`), leaving only `braintree<=4.8.0` (excluding the yanked) and pre-release `braintree>4.9.dev0`. Default `uv pip` excludes pre-releases; constraint is unsatisfiable. Build exits 167. Latent since frappe shipped v13.41.3, surfaces now because the #390 fix made the pinned-tag path reachable for the first time. Default-branch builds (`version-13` HEAD) are unaffected — that branch tip presumably has the constraint updated downstream of v13.41.3. Filed as ESACP#392 with Option B (`UV_PRERELEASE=allow` env var) recommended.

## Filed + closed

- [**ESACP#390**](https://github.com/martinhbramwell/ESACP/issues/390) — **closed** at `18:40:52Z` via `fixes #390` in PR#391 merge commit `9ef1aa5`. Cross-repo `fixes` tally up by 1 (16 → 17).
- [**ESACP#392**](https://github.com/martinhbramwell/ESACP/issues/392) — `bug(packer): uv pip refuses frappe v13.41.3 over braintree pre-release constraint`. Proposed fix: Option B — set `UV_PRERELEASE=allow` env var in `02_bench_install.sh` before invoking bench app-install. Acceptance: end-to-end build completes; `bench list-apps` reports pinned versions.

## Pointer-comments posted

- [LSKB#20 issuecomment-4453697757](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4453697757) — Path-1 block-chain update: ESACP#390 fix landed; new top-of-chain is ESACP#392; substrate-version-alignment cannot proceed until #392 is also fixed.
- [ESACP#353 issuecomment-4453698874](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4453698874) — Plan-B parent Session-51 ledger entry; `fixes` tally 17; ladder state ESACP#392 → LSKB#20 → LSKB#15 → LSKB#16.
- [LSKB#6 issuecomment-4453699665](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4453699665) — Phase 4 ladder state with new three-layer block chain.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| ESACP#390 | closed via PR#391 `fixes` | env-var-passing flaw resolved; build-log evidence verifies fix |
| ESACP#392 | filed (open) | uv-pip-vs-yanked-braintree downstream blocker uncovered in #390 acceptance |
| LSKB#20 | pointer-comment posted; **stays open** | Block chain advanced one layer; now blocked on ESACP#392 |
| LSKB#15 | unchanged; **stays open** | Downstream-of-LSKB#20 unchanged |
| LSKB#16 | unchanged; **stays open** | Downstream-of-LSKB#15 unchanged |

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1+T3 (combined pre-commit + pre-push on `be9b637` to feature branch) | `ad358a1a30acc05e1` | approve | Clean approve, `hard_block: true`. Four mechanisms enumerated; chosen (explicit `env VAR=val` in `execute_command`) matches issue-body recommendation. Agent confirmed root-cause diagnosis accuracy by independently reading `02_bench_install.sh:18` (`cd "$HOME"`) and verifying `-H` is load-bearing for bench path correctness. Non-blocking observation: `packer` scope absent from CLAUDE.md's listed common scopes (`kvm`, `vbox`, `observability`, ...) — agent treated as descriptive/honest, not blocking. |
| T2 (pre-merge under §2.2 advisory carve-out on PR#391 → main) | `a516eb8f89f0dea04` | approve | Advisory per §2.2 carve-out (all three conditions verified: prior T1+T3 approve on `be9b637`; head SHA unchanged; `mergeStateStatus: CLEAN`, single-commit squash equivalent to ff). Agent independently re-read diff for content-review; flagged that PR-body acceptance items 3/4 (`bench list-apps` versions + metadata match) remain unchecked at merge time and noted per `feedback_no_downstream_of_merge_acceptance.md` this is by-design (those items belong in ESACP#392, not #390). |
| T1+T3 (session-close commit `d2cf4c9`) | `a326056a476ee10b3` | approve | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3. Three files staged: minutes (this file) + next-agenda (S52) + qa-log (close-row + the 2 verdict rows above). Pure doc-only — no substrate-state files this session. Verdict cells filled in by post-close audit-fix commit per S46/S47/S48/S49/S50 precedent. |

## Counts at session end

- ESACP open: **38** (was 38; -#390 closed via PR#391 merge, +#392 filed; net 0).
- LSKB open: **9** (unchanged; #20 still paused, now blocked on #392).
- ce_sri open: 5 (unchanged); LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged).
- Cross-repo `fixes` tally: **17** (was 16; +#390 via PR#391).

## TRIVIAL_FIXES.md status

Unchanged — 2 monitor-only entries (S33 LSM Trigger-3 skip pattern, S47 `tools/secrets.py` `+x` bit).

## Carry-forward operator-reminders (delta)

- **ESACP#390** — **dropped** (closed via PR#391).
- **ESACP#392** (NEW) — uv-pip-vs-yanked-braintree downstream blocker. New top-of-chain for Plan-B Phase 4.
- **LSKB#20** — Path-1 still paused; blocker swapped from #390 to #392.
- **LSKB#15, LSKB#16, LSKB#18, ESACP#387** — unchanged from S50 carry-forward.
- **dev02 substrate state** — unchanged from S50 (rebuilt at version-13 tip with timed-out wizard; disposable; will be destroyed/rebuilt when LSKB#20 resumes after #392 fix).
- **`tools/secrets.py` +x bit (F4)** — unchanged (TRIVIAL_FIXES monitor-only).
- **LogiSoluMemory Trigger 3 skip pattern** — unchanged.
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.
- **Saconsole stash** — `stash@{0}` on `/opt/esacp` saconsole-side still preserves the npm-injected `package-lock.json` `engines` block. Restore-on-demand only.
- **Build-log cleanup** — `/tmp/build-390.log` on saconsole (1455+ lines) and `/tmp/build-390.log` aren't repo state; let saconsole's `/tmp` rotation handle.

## Shape note

Substantive-class with one issue closed via fix landing + one new downstream bug filed. Tracks the S47 (LSKB#15 paused → LSKB#20 filed) and S48 (LSKB#20 paused → ESACP#388 filed) and S49 (#388 closed via fix landing) and S50 (LSKB#20 paused → ESACP#390 filed) precedent — alternating fix-lands / next-blocker-filed pattern. Block chain at S51 close: ESACP#392 → LSKB#20 → LSKB#15 → LSKB#16 (chain length unchanged; top swapped). Minutes ~85 lines — within the S40–S50 73–95 baseline.

## Saconsole-discipline check

ESACP#390 fix landed via PR#391 merge; saconsole inherited via `git pull` during S51 close (controller + saconsole both at `9ef1aa5`). No new saconsole capability declaration triggered — the fix is a self-contained packer-HCL change. ESACP#392 (when fixed) will also be self-contained inside `02_bench_install.sh` (Option B's `UV_PRERELEASE=allow` env var); not a new saconsole capability either.

## Post-close audit-fix

SESSION END audit (UserPromptSubmit hook re-run pattern per S45–S50) ran clean on all four steps — **second consecutive zero-gap close** in the S40-S50 precedent window. Discharge: pure clerical verdict-cell finalization (close-row commit-hash `d2cf4c9` + verdict cells `approve | proceeded` + 2 QA invocation IDs `ad358a1a30acc05e1` and `a516eb8f89f0dea04`) + this minutes subsection + qa-log self-referential row appended.

1. **Forward-tense scan** — 9 hits, all benign: (a) self-referential `_pending_` cells in QA-verdicts table row 3 (expected protocol); (b) future-state of disposable dev02 substrate; (c) forward-looking analysis of #392 fix shape (UV_PRERELEASE env var inside 02_bench_install.sh); (d) agenda's "after Session 51 close-out commit lands" state-at-next-session-start language; (e) historical S41→S51 trail describing Phase 4 ladder; (f) standing operator-decision on `Asignar Producto a Campo` retirement carried verbatim from prior agendas; (g) LSKB#20 block-chain description; (h) QA file-size discipline reminder for future Frappe-patch sessions; (i) S52 estimated wall-clock by candidate. No S51 work was deferred or unexecuted.

2. **GH issue references** — every issue with an S51-specific finding received a within-session comment: ESACP#353 ([`issuecomment-4453698874`](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4453698874)), LSKB#6 ([`issuecomment-4453699665`](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4453699665)), LSKB#20 ([`issuecomment-4453697757`](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4453697757)). ESACP#390 closed via PR#391 `fixes` (the merge IS the closure, no comment needed). ESACP#392 filed with full content in body. LSKB#15/#16/#18 + ESACP#387/#341/#388 referenced in passing only — per S48/S50 precedent, LSKB#15 specifically did NOT receive an S51 comment because its immediate blocker LSKB#20 did not change state (only the upstream chain top swapped from #390 to #392).

3. **PR mergedAt gate** — PR#391 `mergedAt: 2026-05-14T18:40:51Z` (verified pre-session-close). `feedback_pr_merge_before_session_close.md` satisfied.

4. **Unresolved doubts** — two AskUserQuestion prompts (build-acceptance mode = background; #390/#391 merge-path = merge-now-defer-#392-to-S52) both resolved within-session.

Second consecutive zero-gap shape (after S50's first such finalization) suggests the pointer-comment-within-session discipline is now structurally embedded rather than a per-session correction. The audit-fix commit's own qa-log row carries residual `_pending_` verdict cells per S48 `0bbd54e` / S50 `e1fdf9a` finalization-row irreducible-self-reference convention.
