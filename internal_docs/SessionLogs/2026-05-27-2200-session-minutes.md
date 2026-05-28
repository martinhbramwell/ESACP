# 2026-05-27 2200 — Session 85 minutes

## Stated objective (chosen at session start, then swapped mid-session)

Initial pick at session start: Candidate **C** from the S85 next-agenda
— **#440 snapShotVM dispatcher fix** (4th-encounter promotion long
overdue per S77 carry rule). Investigation complete, plan written,
approval requested. **Operator paused before approval** and pivoted to
unblock Junior's on_boarding chain — issue **#505** (feat(ci): GitHub
Pages workflow — Jekyll build on_boarding/docs/ + raw-serve persona
doc; unblocks #497). #440 shelved at "plan-approved-no-code-touched,
clean working tree" state for S86. The pivot took the substantive slot
of the session.

## Class

**1:1:1 substantive code/CI session.** New branch
(`feat/505-jekyll-pages-workflow`), single commit (`a45fd80`), PR
(#506), merge-commit (`a579336`) mergedAt `2026-05-28T02:09:36Z`.
Direct-to-main per single-PR single-session convention. **No `fixes`
keyword** — issue #505 stays open per
`feedback_no_downstream_of_merge_acceptance.md`; full AC has post-merge
operator + Junior steps. Not a sidebar (no MEMORY.md edits, no
carry-forward attrition).

## What happened — substantive sequence

### Pre-flight

- sync_check: 49 pass / 8 warn / 0 fail (long-standing WG hub peer
  drift + dormant-VM + Chrome manual-verify warnings; non-blocking
  per agenda).
- Open ESACP issues: **71** (matches S85 agenda expectation).
- LSKB issues: **12** (matches agenda).
- Branch state: `main`, clean tip = `d7dc633` (S84 close-batch).
- TRIVIAL_FIXES.md: 3 open items unchanged.
- Memory PROTOCOLS.md + MEMORY.md auto-load: clean.

### Original objective (#440) — investigation done, then shelved

Read issue #440 in full (via `--json` workaround for the gh
Projects-classic deprecation bug #434). Located dispatcher
`tools/cli/snapshot_vm.py:15,18` (calls `list_snapshots(vm)` and
`create_snapshot(vm, name, emit=print)` without `hypervisor=` kwarg)
and primitive `tools/pipeline/orchestration/snapshot_ops.py:_virsh_cmd`
(supports `hypervisor=` correctly). Confirmed sibling dispatcher
`tools/cli/provision_vm.py:13-14` already does the right thing
(`kvm_hosts(config).get(vm, {}).get("hypervisor") or None`) —
mirrorable pattern. Live-tested both `ssh toshiba` and `ssh toshy`
on this controller: **both return OK**, so the issue body's caveat
about SSH-alias mismatch is stale and no alias-mapping helper is
needed. Caller audit: exactly 2 callers of `snapshot_ops`
(`cli/snapshot_vm.py` = bug; `orchestration/ansible_provision.py`
= already correct). Sizes: `snapshot_vm.py` 27 lines (baseline 27,
cap 80); fix would add ~2 lines.

Plan drafted in plain-language prose; presented to operator for
approval. **Operator did not approve** — pivoted to #505 instead.
Plan + investigation findings preserved in this minutes section
so S86 can resume without re-derivation. No branch was cut; no code
was edited.

### Pivot to #505 (Junior unblock)

Operator restated the chain-of-command framing: Senior owns ESACP,
LogiSolu, and bucket-2 trackers; Junior is constrained to on_boarding
work. Junior had filed #505 against Senior's tracker because the
workflow file lives at `.github/workflows/` — outside `on_boarding/`,
outside Junior's jurisdiction — per
`feedback_chain_of_command_cross_branch.md`. Junior is **blocked**
until Senior lands the workflow; this is the gating piece for the
Session-9 invite-line + iteration #1 + #497 closure chain.

Read #505 in full via `--json` workaround. Verified on_boarding branch
contents via `gh api` (no checkout, honoring "Do NOT touch
on_boarding/ from this controller" carry-forward operator-reminder):
`on_boarding/docs/{_config.yml,Gemfile,_layouts,assets,index.md}` and
`on_boarding/internal_docs/mode_a_persona_v0.md` confirmed present;
no `Gemfile.lock` (CI resolve each run, noted as Junior follow-up);
`_config.yml` has `baseurl: ""` (justifies Option A overlay).
`.github/workflows/` directory did not exist on main — clean
greenfield.

### Planning + approval

Plan presented in plain-language prose per
`feedback_plain_language_approval_requests.md`:

- Branch `feat/505-jekyll-pages-workflow` off main.
- One new file: `.github/workflows/jekyll-pages.yml`.
- Trigger: push on `on_boarding` branch path-filtered to
  `on_boarding/docs/**`, `on_boarding/internal_docs/mode_a_persona_v0.md`,
  and the workflow file itself. Plus `workflow_dispatch:` for manual
  fires.
- Build job: Ubuntu, `ruby/setup-ruby@v1` with `ruby-version: '3.3'`
  and `bundler-cache: true` (working-directory `on_boarding/docs`);
  `bundle exec jekyll build --baseurl "/ESACP"` (Option A per Junior's
  recommendation — keeps shipped `_config.yml` at `baseurl: ""` for
  localhost-serve ergonomics); copy persona doc into
  `_site/persona/mode_a_v0.md` (`.md` extension kept; GitHub Pages
  serves `text/markdown` content-type by default);
  `actions/upload-pages-artifact@v3` of `on_boarding/docs/_site`.
- Deploy job: `actions/deploy-pages@v4` with environment `github-pages`.
- Two-job pattern + top-level `permissions` + `concurrency: { group:
  pages, cancel-in-progress: false }`.

Operator approved.

### Implementation

- **Branch** `feat/505-jekyll-pages-workflow` cut off `main` tip
  `d7dc633`.
- **One new file** `.github/workflows/jekyll-pages.yml` (68 lines).
  Contains the two-job build+deploy structure exactly as planned.
- **Pre-commit size check** — ran `python3 tools/pre_commit_size_check.py`
  BEFORE invoking T1, per S82–S84 recurring-trap discipline rule. Exit
  0 (the script only checks `.py` and `.sh` extensions — the new `.yml`
  file is not in scope. Preflight ran clean but was vacuous for this
  specific change; rule still observed correctly).

### QA verdicts

- **T1 pre-commit** (agent ID a6a30079862847d59): **approve-with-conditions**
  / hard_block: false. Two conditions:
  1. **Trigger topology gap** — workflow fires on `on_boarding`
     pushes but file lands on `main`; GitHub Actions reads workflows
     from the branch receiving the push, so auto-trigger is inert
     until the file propagates to `on_boarding`. Real concern; not
     in the parent's enumeration.
  2. **Commit must include `fixes #505`** per bug-workflow close
     requirement.

  Parent addressed (1) by documenting the gap and the planned
  propagation path (Junior-side `main → on_boarding` sync) in the
  commit message body. Parent **deliberately overrode (2)**: AC in
  #505 explicitly requires post-merge verification (operator Pages
  source flip; first workflow run; curl confirms persona doc serves
  200 + text/markdown). Per
  `feedback_no_downstream_of_merge_acceptance.md`, `fixes`-closed
  issues must not gate on post-merge steps. T1 agent didn't see this
  constraint. Override rationale documented in commit body's final
  paragraph (survives in git log) and in T3 prompt for transparency.
- **T3 pre-push** (agent ID a18ae62932485a384): **approve** /
  hard_block: true. All seven T3 checks pass: commit on branch tip,
  clean tree, GPG sig verified, Co-Authored-By trailer, push target
  is a feature branch, T1 condition (1) addressed in commit body,
  override rationale for (2) documented in-message.
- **T2 pre-merge** (agent ID a97a2e67fcd7032a3): **approve** /
  hard_block: true. §2.2 carve-out cleanly held (T1 conditions
  addressed + clean T3 + no rebase since); full T2 checklist run
  anyway as belt-and-suspenders on infra change. All clean.
- **T5 not triggered** — no `fixes` keyword by design; issue stays
  open.

### Outputs

- **Commit** `a45fd80` `feat(ci): GitHub Pages workflow — Jekyll
  build on_boarding/docs/ + raw-serve persona doc (#505)`. GPG-signed,
  Co-Authored-By trailer, Conventional Commits format, trigger-topology
  disclosure in body, `fixes`-omission rationale in body.
- **PR** #506 → merge-commit `a579336`, mergedAt `2026-05-28T02:09:36Z`.
- **Issue #505 stays open** per `feedback_no_downstream_of_merge_acceptance.md`
  — handoff comment posted (issuecomment-4560313410) documenting landed
  state + operator-action-done + Junior-side step-by-step closeout
  procedure.
- **Operator action** — Settings → Pages → Source flipped to **GitHub
  Actions** post-merge. Screenshot confirmation provided. Side effect:
  legacy "Deploy from branch: main /docs" auto-build deactivated. Site
  at https://martinhbramwell.github.io/ESACP/ now frozen at last
  legacy deploy (2026-05-28T02:09:38Z) until next on_boarding push
  fires our workflow.

## Counts at session close

- **ESACP open**: 71 → 71 (net 0; #505 stays open, no new filed).
- **LSKB open**: 12 → 12 (unchanged).
- **Sibling-tracker counts** (ce_sri 6 / ce_sri_svc 2 /
  LogiSoluValidations 2 / BaRe 2): unchanged.
- **dev02 state**: unchanged from S84 close. R1 + R3 pipeline-applied
  with aligned invocation; R5 + R6 nginx template parity intact.
  Pre-S83-r1-acceptance snapshot persists on toshy.
- **dev01 state**: unchanged from S84 close.
- **Saconsole**: 4 GiB; live.
- **TRIVIAL_FIXES.md**: 3 entries unchanged.
- **`.github/workflows/jekyll-pages.yml`** now present on main
  (a45fd80 → a579336).

## Decisions

- **Mid-session pivot from #440 (Candidate C) to #505** — Junior was
  blocked; #505 takes priority over self-directed primary candidate.
  #440 shelved at plan-approved-no-code state for S86 (now 5th-encounter
  at next pickup; overdue threshold fully crossed).
- **Option A (baseurl flag at build) over Option B (in-repo config
  edit)** — per Junior's recommendation in #505 body. Preserves
  local-serve ergonomics (operator iterates on landing page locally
  with `bundle exec jekyll serve` at `localhost:4000/`, not
  `localhost:4000/ESACP/`).
- **No `fixes #505`** in commit — issue stays open per
  `feedback_no_downstream_of_merge_acceptance.md`. T1 agent
  recommended `fixes #505` (Condition 2); parent overrode with explicit
  rationale in commit body. Operator-visible because the override is in
  the git log and PR body, not just transcript.
- **Persona doc extension `.md` (not `.txt`)** — GitHub Pages serves
  `.md` files with `text/markdown; charset=utf-8` content-type by
  default; Claude.ai webfetch handles `.md` reliably. Junior's #505
  left this open; Senior chose `.md`.
- **`workflow_dispatch:` included** — for manual fires after the
  workflow file propagates to `on_boarding`. Operator cannot
  fire-test before the propagation (`--ref main` fails: no
  `on_boarding/docs/` content on main; `--ref on_boarding` fails:
  no workflow file on that branch yet). Sync must precede.

## Carry-forward (new from S85)

- **#505 stays open** — pending Junior closeout after first deploy
  confirms 200 + text/markdown on both URLs. Handoff comment
  documents step-by-step.
- **Legacy Pages auto-build deactivated** — "Deploy from branch:
  main /docs" no longer fires. `docs/` directory at main root
  exists but is no longer being deployed. Out of scope this
  session; do NOT touch unless Junior surfaces a follow-up.
- **#440 promote-to-primary now 5th-encounter for S86** — was 4th
  at S85 start, shelved without engagement. Carry rule threshold
  passed; **must** be S86 primary unless operator pivots again.
- **Size-baseline preflight discipline — verbally observed but
  vacuous for this session** — parent ran
  `tools/pre_commit_size_check.py` before T1 invocation per recurring
  S82–S84 trap reminder. Exit 0, but the new file is `.yml` (not in
  `CHECKED_SUFFIXES`), so the preflight was vacuous. Rule still
  observed correctly; trap streak technically broken (no ratchet
  trip), but not in a way that proves the discipline works for
  `.py`/`.sh` changes. Re-test on next substantive Python session.

## Unchanged carry-forward (continues from S84)

- ESACP#440 (4th→5th encounter on next pickup; S86 primary).
- S71 minutes backfill decision.
- S81 minutes backfill decision.
- ESACP#426 / #427 — pending operator pickup.
- `on_boarding` branch handoff — Junior owns; #505 handoff comment
  added.
- LogiSoluMemory cross-repo cleanup (~28 refs).
- ESACP#401 + dev02 intermittents.
- LSKB#11 / #16 / #18 / #21 — Phase 2/3 follow-on.
- LSKB#24 (trivial doc edit) / LSKB#31 (File doctype role lockdown).
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry.
- TRIVIAL_FIXES.md monitors (3): `sync_check.sh:2 Mighty` (S58);
  `tools/secrets.py +x` (S47); LSMem T3-miss pattern (S33).
- MariaDB-10.6 default PS=OFF (S55 carry).
- Tablet WG sidebar (#383).
- Pages site tenant-detail scrub gate.
- `session_focus.txt` / `session_buckets.txt` controller-root.
- Stage-6-equivalent M&V check every ~50 substantive closes.
- Sub-rule #6 (operator walkthrough on systematic audits ≥2 findings).
- Frame-shift discipline (platform vs tenant M&V).
- Qualys regression-check as standard nginx-change acceptance.
- `applyV16PostMigrateFixups` primitive — canonical extension entry
  for V13→V16 post-migrate fixes; R6e.2 (#496) next.

## Diff-based introspection-sidebar trigger

**NEGATIVE.** No MEMORY.md edits this session; no operator-reminder
attrition; pure substantive 1:1:1 (with mid-session objective pivot,
not a class change). Not a sidebar.

## SESSION END audit (4 prongs)

1. **Forward-tense audit** — no orphaned "I'll"/"will" promises.
   #505 handoff comment posted (issuecomment-4560313410) before
   minutes-write. The "next Junior session" / "operator must flip
   Pages" promises in commit + PR + comment have durable homes in
   those artifacts. #440 deferred-to-S86 has durable home in this
   minutes file + next-agenda.
2. **GH issue references** — #505 stays open with full handoff
   comment; #497 referenced as downstream beneficiary (Junior closes
   that one too); #440 deferred with state preserved in this minutes
   file. No new issues filed this session.
3. **PRs opened** — #506 opened and merged in-session per
   `feedback_pr_merge_before_session_close.md`; `mergedAt`
   confirmed non-null (2026-05-28T02:09:36Z) before this file written.
4. **Unresolved operator doubts** — none lingering. Pivot was
   operator-initiated and clean. Pages source flip handled directly
   with screenshot confirmation. Live-site investigation (legacy
   `pages build and deployment` runs vs new workflow) clarified
   in-prompt; operator visible-state aligned with reality.
