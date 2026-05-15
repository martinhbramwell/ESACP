# 2026-05-14 2130 — Session 52 minutes

## Objective

**ESACP#392 fix** — uv pip refuses frappe v13.41.3 over the yanked-braintree pre-release constraint. Apply the fix, run end-to-end packer-build acceptance, merge to main, unblock LSKB#20 Path-1 substrate-version-alignment. Bucket-1 substantive 1:1:1.

## Outcome — #392 fix landed via corrected mechanism; downstream surfaces a separate issue; Plan-C pivot recommended for LSKB#20

PR#393 merged at `2026-05-15T01:16:24Z` (squash, merge commit `e283716`). ESACP#392 auto-closed via `fixes #392` at `01:16:25Z`. The in-scope mechanism (uv refusal of yanked-braintree exact pin) is resolved by a tag-gated `uv.toml override-dependencies` config — verified at three levels. Two new issues filed: ESACP#394 (packer-scripts size-band coordinated decomposition tracking, per T2 condition) and ESACP#395 (downstream pyyaml/Cython-3 source-build failure surfaced by the corrected fix; mooted by Plan-C). Plan-C tag pivot recommended on LSKB#20 — substrate-version-alignment to step away from v13.41.3 to a later v13 tag where upstream cleaned both pins.

### Iteration narrative — first attempt was a no-op

S51's #392 issue body proposed "Option B": `export UV_PRERELEASE=allow` in `02_bench_install.sh`. S52's first commit `e481ac3` implemented exactly that. The Session-52 v1 acceptance build (saconsole `/tmp/build-392-v1-fail.log`) confirmed the export executed (script-level marker `[02_bench HH:MM:SS]` visible; bench inherited the env via `subprocess.call(env=None)` per direct read of `/usr/local/lib/python3.10/dist-packages/bench/utils/__init__.py:179`) — but uv ignored it. Direct test on dev02 (uv 0.9.30) replicated the failure across env-var and CLI-flag modes:

| Invocation | Result |
|---|---|
| `uv pip install "braintree>=4.8.0,<4.9.dev0"` | unsatisfiable |
| `UV_PRERELEASE=allow uv pip install ...` | unsatisfiable (env var no-op) |
| `uv pip install --prerelease=allow ...` | unsatisfiable (CLI flag no-op) |
| `uv pip install "braintree==4.8.0"` (exact pin) | installs (yanked warning) |
| `uv.toml` with `override-dependencies = ["braintree==4.8.0"]` | installs (yanked warning) |

uv's diagnostic hint (`try --prerelease=allow`) was misleading. The actual mechanism is PEP 592 yanked-version handling: uv excludes yanked versions from RANGE constraints regardless of pre-release setting, but accepts them when pinned exactly via `==`. Frappe's `>=4.8.0,<4.9.dev0` had no satisfiable pool member. Per `feedback_no_passive_causal_framing.md` — the issue body's analysis was wrong (mis-read of uv's own hint), not "decay" or "drift".

### Corrected mechanism

Commit `6cc33fc` replaced the no-op `UV_PRERELEASE=allow` with a tag-gated `case` block writing `~/.config/uv/uv.toml` with `override-dependencies = ["braintree==4.8.0"]`, only when `FRAPPE_BRANCH=v13.41.3`. The override forces the exact yanked pin, which uv accepts (with a yanked warning). Tag-gated because applying the override on other tags would downgrade braintree from working versions.

Both commits live on the branch; squash-merge dropped the no-op into the corrected landed commit. The squash body is the corrected mechanism's narrative + `fixes #392`.

### Build acceptance — in-scope mechanism verified end-to-end

S52 v2 acceptance build (saconsole `/tmp/build-392-v2.log`):

```
[02_bench 19:23:24] applying uv override for v13.41.3: braintree==4.8.0 (yanked, only candidate)
[02_bench 19:23:24] bench init /home/erpadm/frappe-bench (frappe v13.41.3) ...
```

The tag-gated case block fires. `bench init` proceeded past the resolver stage. `grep braintree /tmp/build-392-v2.log` returns ONLY the "applying uv override" log line — braintree is no longer mentioned as a failure cause anywhere downstream. The in-scope mechanism is proved.

### Downstream — pyyaml 5.4.1 / Cython 3 (out-of-scope of #392)

After braintree clears, the v2 build still exits 167 — but on `Failed to build pyyaml==5.4.1 / Call to setuptools.build_meta.build_wheel failed (exit status: 1)`. PyYAML 5.4.1's `setup.py` calls a Cython API removed in Cython 3.0. This is a build-from-source failure (not resolver), a different mechanism, and unrelated to yanked-version policy. Filed as ESACP#395 for institutional memory.

### Strategic pivot — Plan-C for LSKB#20 (operator decision)

After the second decayed-pinned-dep surfaced in v13.41.3, operator chose Plan-C (over peeling each decay individually): pivot LSKB#20 Path-1 to a later frappe v13 tag where upstream has cleaned both pins. The `version-13` branch HEAD (currently 13.58.22) is known to build clean. Tag selection deferred to LSKB#20 owner; recorded as a comment on LSKB#20 ([issuecomment-4456005757](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4456005757)). PR#393's mechanism is harmless on other tags (case block doesn't fire) so it ships independent of the pivot — useful institutional record for any future yanked-dep situation.

### What ran cleanly on S52

- **Branch + first commit + push** — `git checkout -b fix/392-uv-prerelease-allow main` from `ae0a3ac`. Commit `e481ac3` (no-op first attempt), GPG-signed, Conventional Commits, Co-Authored-By trailer, `fixes #392` body. Pushed and PR#393 opened on `e481ac3`.
- **v1 acceptance + diagnosis** — saconsole pulled feature branch (drop carried-forward stash `e8b30af` per S51 carry-forward), build launched at 17:05, exited 167 at 17:36 (~31 min) with same braintree error. Diagnosis: read `bench` source on dev02 to verify env propagation path; ran 5-row uv constraint matrix on dev02 to confirm both env-var and CLI-flag are no-ops in the yanked-only-candidate case.
- **PR#393 do-not-merge marker + #392 corrected-diagnosis comment** — posted within-session ([PR#393 comment 4455173697](https://github.com/martinhbramwell/ESACP/pull/393#issuecomment-4455173697), [#392 comment 4455173018](https://github.com/martinhbramwell/ESACP/issues/392#issuecomment-4455173018)) before any further commits.
- **Operator decision via AskUserQuestion** — chose Path 1 (uv.toml override).
- **Revised commit + push** — commit `6cc33fc` (corrected mechanism), GPG-signed Conventional Commits, `fixes #392` in body. T1 verdict required `lib_uv_overrides.sh` extraction; attempted but reverted because packer's `shell` provisioner uploads only one file per phase — sourcing a sibling fails on the build VM. ESACP#394 filed to track the coordinated decomposition (T3 condition 1).
- **PR#393 title + body update** — `gh pr edit` failed on Projects-classic deprecation graphql; switched to `mcp__github__update_pull_request` which succeeded.
- **v2 acceptance** — saconsole pulled to `6cc33fc`, build launched at 18:53, exited 167 at 19:23 (~30 min). Mechanism marker visible; braintree barrier cleared; downstream pyyaml failure surfaced.
- **Plan-C decision via AskUserQuestion** — chose pivot LSKB#20 to later v13 tag; PR#393 still merges.
- **In-scope acceptance comment + #395 + LSKB#20 pivot comment posted within-session** — sustained S50/S51 within-session-pointer-comment discipline.
- **PR#393 squash-merge** — `gh pr merge 393 --squash --subject ... --body ...` with the corrected commit's body (T2 condition 2). `mergedAt: 2026-05-15T01:16:24Z`. ESACP#392 auto-closed at `01:16:25Z`.
- **Controller + saconsole synced back to main** — both clones fast-forwarded to `e283716`. Saconsole's `fix/392-uv-prerelease-allow` branch retained per `feedback_keep_merged_branches.md`. v1-fail.log and v2.log preserved on saconsole `/tmp` for evidence.

## Filed + closed

- [**ESACP#392**](https://github.com/martinhbramwell/ESACP/issues/392) — **closed** at `01:16:25Z` via `fixes #392` in PR#393 squash commit `e283716`. Cross-repo `fixes` tally up by 1 (17 → 18).
- [**ESACP#394**](https://github.com/martinhbramwell/ESACP/issues/394) — `refactor(packer): all four packer scripts exceed CLAUDE.md size gradient — single coordinated decomposition pass`. Filed per T3 condition. Tracks `01_os_prep.sh` 132 lines + `02_bench_install.sh` 77 lines (both in must-split band). Coordinated decomposition recommended over piecemeal because packer's one-file-per-shell-provisioner upload makes naive split require new infrastructure (`file` provisioner + hardcoded `/tmp` path).
- [**ESACP#395**](https://github.com/martinhbramwell/ESACP/issues/395) — `bug(packer): pyyaml 5.4.1 source-build fails on Cython 3 (frappe v13.41.3 transitive)`. Filed for institutional memory. Mooted by Plan-C tag pivot; reactivates only if a future tag-pivot brings us back to a v13.x.y that still pins pyyaml 5.4.1.

## Pointer-comments posted

- [LSKB#20 issuecomment-4456005757](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4456005757) — Plan-C pivot recommendation (away from v13.41.3 to a later v13 tag); tag selection deferred to LSKB#20 owner.
- [ESACP#392 issuecomment-4455173018](https://github.com/martinhbramwell/ESACP/issues/392#issuecomment-4455173018) — corrected diagnosis (yanked vs prerelease) with v1 acceptance evidence + dev02 5-row test matrix.
- [ESACP#392 issuecomment-4456006779](https://github.com/martinhbramwell/ESACP/issues/392#issuecomment-4456006779) — in-scope mechanism verified by v2 build evidence + #395 + LSKB#20 pivot link.
- [PR#393 issuecomment-4455173697](https://github.com/martinhbramwell/ESACP/pull/393#issuecomment-4455173697) — do-not-merge marker after v1 failure; pointer to corrected diagnosis on #392.
- [PR#393 issuecomment-4455385208](https://github.com/martinhbramwell/ESACP/pull/393#issuecomment-4455385208) — corrected mechanism pushed; #394 filed; acceptance re-run incoming.

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| ESACP#392 | closed via PR#393 `fixes` | yanked-braintree resolver-stage barrier resolved by uv.toml override; mechanism verified at 3 levels |
| ESACP#394 | filed (open) | T3 verdict condition — packer-scripts size-band tracking; coordinated decomposition required by structural constraint |
| ESACP#395 | filed (open) | downstream pyyaml/Cython-3 finding surfaced by #392 fix; mooted by Plan-C |
| LSKB#20 | comment posted; **stays open** | Plan-C pivot recommendation; tag selection deferred to LSKB owner |
| LSKB#15, #16, #18 | unchanged; **stays open** | downstream of LSKB#20; no state change to comment on (S48/S50 precedent) |
| ESACP#387, #353, #331, #278 | referenced in passing | no S52-specific finding requiring a comment |

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1 (pre-commit, e481ac3 first attempt — `UV_PRERELEASE=allow` per #392 Option B) | `a4c3094cc0526435d` | approve-with-conditions | `hard_block: false` per qa-contract §2 row 1 (T1 advisory). Single condition: acceptance-test evidence required at T2; deferred (correct sequencing). 1:1:1 ✓; Conv-Commits + GPG + trailer ✓; no third-party mod ✓; size 67 lines (within 51-70 advisory band). Enumeration: agent flagged that the issue body's 4-option enumeration was the canonical record and the commit cited it correctly. |
| T3 (pre-push, e481ac3 → feature branch) | `a3b2758a6b01d0d4a` | approve | `hard_block: true` per qa-contract §2 row 3 (push to remote). Clean approve. Push target = feature branch (not main, not umbrella) ✓. T1 acceptance condition correctly defers to T2 ✓. |
| T1 (pre-commit, 6cc33fc revised — uv.toml override-dependencies) | `aaf8200f5a7bce96b` | approve-with-conditions | `hard_block: false`. THREE conditions: (a) extract case block to sourced helper to bring 02_bench_install.sh below 70 lines; (b) `fixes #392` in commit body (already planned); (c) T2 must wait for end-to-end acceptance. Mechanism verification (5-row matrix) accepted. Heredoc usage classified as TOML data (carve-out applies). |
| T3 (pre-push, 6cc33fc → feature branch) | `a454372fb8407cc44` | approve-with-conditions | `hard_block: true` (status approve, push permitted). Helper-extraction condition addressed via packer-template-constraint argument: extracted helper would not be uploaded by packer's one-file-per-shell-provisioner — split requires new `file` provisioner + hardcoded `/tmp` path; ESACP#394 filed to track coordinated decomposition of all four packer scripts together. T2 acceptance gate condition reaffirmed. |
| T2 (pre-merge, PR#393 → main, squash) | `a88fb7fa8595d1de3` | approve-with-conditions | `hard_block: true` (status approve, merge permitted). §2.2 advisory carve-out NOT claimed (head SHA `6cc33fc` had a separate T1+T3 invocation but the carve-out requires a single combined T1+T3 invocation per the contract — cleanly treated as full hard-block). Two conditions: (a) #394 must remain open (debt tracking); (b) squash commit body must contain `fixes #392` from `6cc33fc`'s body, not the first commit's. Discharged via explicit `--subject` + `--body` flags on `gh pr merge --squash`. Anti-rubber-stamp positive: agent worked through whether reframing #392 acceptance as "in-scope mechanism only" was a post-hoc rescope or principled application of `feedback_no_downstream_of_merge_acceptance.md` — concluded latter, with #395 documenting the downstream gap institutionally. |

## Counts at session end

- ESACP open: **39** (was 38; -#392 closed via PR#393, +#394 filed, +#395 filed; net +1).
- LSKB open: **9** (unchanged; #20 still paused, blocker swapped from #392 to "Plan-C tag pivot" decision).
- ce_sri open: 5 (unchanged); LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged).
- Cross-repo `fixes` tally: **18** (was 17; +#392 via PR#393).
- Phase 4 ladder block chain: was `ESACP#392 → LSKB#20 → LSKB#15 → LSKB#16`; now `LSKB#20 (Plan-C tag-pivot decision pending) → LSKB#15 → LSKB#16` (chain shortened by one layer; #392 fully discharged).

## TRIVIAL_FIXES.md status

Unchanged — 2 monitor-only entries (S33 LSM Trigger-3 skip pattern, S47 `tools/secrets.py` `+x` bit).

## Carry-forward operator-reminders (delta)

- **ESACP#392** — **dropped** (closed via PR#393).
- **ESACP#394** (NEW) — packer-scripts size-band coordinated decomposition; institutional debt; T2 verdict condition requires #394 stay open.
- **ESACP#395** (NEW) — pyyaml 5.4.1 / Cython 3 finding; moot under Plan-C; reactivates only if future tag-pivot brings us back to a tag pinning pyyaml 5.4.1.
- **LSKB#20** — Path-1 pivot decision pending; needs LSKB-side tag selection (between v13.41.3 broken and v13.58.22 working HEAD); chain blocker is now strategic (Plan-C tag choice) not mechanical.
- **LSKB#15, #16, #18, ESACP#387** — unchanged from S51 carry-forward.
- **dev02 substrate state** — unchanged from S51 (version-13 tip with timed-out wizard; disposable).
- **`tools/secrets.py` +x bit (F4)** — unchanged (TRIVIAL_FIXES monitor-only).
- **LogiSoluMemory Trigger 3 skip pattern** — unchanged.
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.
- **Saconsole stash** — **dropped** (S52 dropped `e8b30af` per S51 authorization; clean stash list now).
- **Build-log preservation** — saconsole `/tmp/build-392-v1-fail.log` (1485 lines, S52 v1 evidence) and `/tmp/build-392-v2.log` (S52 v2 evidence with mechanism marker); not repo state; saconsole's `/tmp` rotation handles cleanup.

## Shape note

Substantive-class with one issue closed via fix landing + two new issues filed (one debt-tracking, one downstream-finding) + one strategic pivot. Tracks the alternating fix-lands / next-blocker-filed pattern (S47/S48/S49/S50/S51) but with a new shape: the corrected-mechanism iteration within the same PR. The S52 first-commit no-op + second-commit corrected-mechanism + squash-merge sequence is novel — the squash dropped the no-op cleanly so main never sees the wrong attempt, while the PR history preserves the iteration story for institutional memory. Per `feedback_no_passive_causal_framing.md`: the issue body's wrong analysis was MY first-acceptance-of-the-issue's-recommendation without independent validation — the mechanism investigation should have happened BEFORE the first commit, not after the first build failed. Lesson: when an issue body's analysis cites a "uv hint says try X" pattern, validate the hint applies to the actual constraint shape before implementing. Minutes ~120 lines — above S51's 85 baseline because this session had two acceptance builds, two QA T1+T3 cycles, and a strategic pivot decision; substantive-class scope justifies the depth.

## Saconsole-discipline check

ESACP#392 fix landed via PR#393 squash-merge; saconsole inherited via `git pull` during S52 close (controller + saconsole both at `e283716`). No new saconsole capability declaration triggered — the fix is a self-contained `02_bench_install.sh` change. The `~/.config/uv/uv.toml` write is INSIDE the build VM (ephemeral, destroyed at end of packer build), not on saconsole itself. Per `project_saconsole_as_fleet_capability_record.md`: bootstrap_hub.sh + ansible roles unchanged.

## Plan-C as a meta-pattern

This session is the first explicit instance of "stop peeling, pivot the substrate". S47-S51 walked the LSKB#20 ladder by fixing each downstream blocker as it surfaced. S52 hit a second decay class (build-from-source vs resolver) within v13.41.3 and surfaced the diminishing-returns shape: each peel costs ~30 min build + diagnosis, with no upper bound on how many remain in a ~2-year-old tag. The Plan-C call moves the substrate-version-alignment target instead of fixing each decayed pin. Worth filing as a feedback memory if a future session sees the same pattern recur on a different aged tag. (Not filing this session — single instance is not yet a pattern.)

## Post-close audit-fix

SESSION END audit (UserPromptSubmit hook re-run pattern per S45–S51) ran clean on all four steps — **third consecutive zero-gap close** in the S40-S51 precedent window. Discharge: pure clerical verdict-cell finalization (close-row commit-hash `fbeb384` + verdict cells `approve | proceeded` + QA invocation ID `ae41ab1f5a8570409`) + this minutes subsection + qa-log self-referential row appended.

1. **Forward-tense scan** — 7 categories of hits in minutes/agenda but all benign: (a) S53 agenda candidates A/B/C/D forward-looking by definition; (b) parked backlog items; (c) carry-forward operator-reminders; (d) self-referential `_pending_` cells in qa-log close-row; (e) Plan-C conditional "if future tag-pivot brings us back" language in #395 carry-forward note; (f) standing `Asignar Producto a Campo` operator-decision carried verbatim from prior agendas; (g) general-principle reminders ("any future production-snapshot restore"). No unresolved S52 commitments.

2. **GH issue references** — every issue with an S52-specific finding received a within-session comment: ESACP#392 ([issuecomment-4455173018](https://github.com/martinhbramwell/ESACP/issues/392#issuecomment-4455173018) + [4456006779](https://github.com/martinhbramwell/ESACP/issues/392#issuecomment-4456006779)), PR#393 ([issuecomment-4455173697](https://github.com/martinhbramwell/ESACP/pull/393#issuecomment-4455173697) + [4455385208](https://github.com/martinhbramwell/ESACP/pull/393#issuecomment-4455385208)), LSKB#20 ([issuecomment-4456005757](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4456005757)). ESACP#392 closed via PR#393 `fixes` (the merge IS the closure, no comment needed). ESACP#394 + #395 filed with full content in body. LSKB#15/#16/#18 + ESACP#387/#341/#353/#388 referenced in passing only per S48/S50/S51 precedent.

3. **PR mergedAt gate** — PR#393 `mergedAt: 2026-05-15T01:16:24Z` verified pre-session-close. `feedback_pr_merge_before_session_close.md` satisfied.

4. **Unresolved doubts** — three AskUserQuestion prompts (acceptance shape = full build / direction after v1 failure = update #392 + decide / pyyaml finding = Plan-C pivot) all resolved within-session.

Third consecutive zero-gap shape (after S50/S51) confirms the pointer-comment-within-session discipline is structurally embedded rather than a per-session correction. The audit-fix commit's own qa-log row carries residual `_pending_` verdict cells per S48 `0bbd54e` / S50 `e1fdf9a` / S51 `ae0a3ac` finalization-row irreducible-self-reference convention.
