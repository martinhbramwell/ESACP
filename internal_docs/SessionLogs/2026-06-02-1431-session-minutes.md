# 2026-06-02 1431 — Session 94 minutes

## Stated objective

**#560** — mechanize the close-time agenda↔tracker reconciliation: an `umbrella:480`
grouping label on the #480 children + an agenda-lint helper that flags bare CLOSED issue-refs.
The code half of the S93 introspection sidebar; a small self-contained 1:1:1. Operator chose
this over the #456 homepage rebuild and the fresh-substrate clean-run.

## Pre-flight

- `sync_check`: **49 pass / 8 warn / 0 fail** — warnings all expected (dormant dev03/target5,
  manual Chrome-tab verify). No workarounds.
- Open issues at start: ESACP **73**, LSKB **12** — matched the S94 agenda forecast.
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### Deliverable 1 — `umbrella:480` grouping label

Created label `umbrella:480` and applied it to the #480 defect-fix children: **#456** (open) +
#483 #486 #498 #481 #472 #492 #503 #473 (closed). Excluded #480 itself (the umbrella), #488
(deferred Qualys acceptance gate, tangential), #560/#561 (process/view cross-refs). Closed
children labelled too so the #561 PERT view can render done+remaining. Result: the
"remaining on the #480 path" sentence is now a live query —
`gh issue list --repo martinhbramwell/ESACP --label umbrella:480 --state open` → just **#456**.

### Deliverable 2 — `tools/agenda_lint.py` (70 lines, exec)

Scans a next-agenda for `#N` refs, looks up each one's live ESACP tracker state via
`gh issue view`, and flags any CLOSED ref left **bare** (no `done`/`closed`/`✅`/`~~` stamp on
its line). ESACP-repo-scoped: `REF_RE`'s lookbehind `(?<![A-Za-z_])#(\d+)` skips letter-prefixed
cross-repo refs (`LSKB#16`). Pure core `bare_closed_refs(text, states)` is offline-testable;
`fetch_states` + `main` do the I/O. Exit 1 = flagged, 2 = `gh` lookup failed (incomplete), 0 =
clean. Colocated `tools/test_agenda_lint.py` — 7 tests, all pass.

### Live proof + two discoveries

Run against the S94 agenda, the lint flagged **#548** — a genuine bare CLOSED ref that #560
itself predicted. It also surfaced the agenda's `LSKB#11 / #16 / #18 / …` **distributed-prefix
shorthand**: the trailing refs are written bare, so an ESACP-scoped lint mis-reads them as ESACP
issues (which happen to be closed). Resolution: not fragile prefix-distribution parsing but an
**authoring discipline** — cross-repo refs must carry their explicit prefix (`LSKB#16`), now
documented in the tool docstring + `tools/CLAUDE.md` + the memory.

### QA + no-masking fix

Pre-commit verdict: **approve-with-conditions**. Genuine catch — `fetch_states` originally mapped
a failed `gh` call to `"OPEN"`, producing a false-clean result (violates "No masking of errors").
Fixed: failures are recorded and surfaced (stderr warning + exit 2). Reclaimed the 4 added lines
by tightening docstrings to land back at 70. Pre-merge verdict: **approve**.

## Decisions

1. Label **closed** #480 children too (not just open) — the #561 PERT view needs the full step
   list, not only remaining work.
2. Cross-repo refs in agendas use **explicit prefixes** (`LSKB#16`), never bare — the lint stays
   ESACP-scoped rather than growing brittle multi-repo parsing.
3. Agenda-lint is **not** auto-wired into a pre-commit hook this session — kept standalone +
   documented; run at session close. (#560 marked the hook optional.)

## Acceptance (#560)

- ✅ #480 children carry `umbrella:480`.
- ✅ Lint flags any bare CLOSED carry-forward `#N` — proven on #548; 7/7 unit tests.
- ✅ Zero bare closed-refs in the next-agenda — the S95 agenda below was authored then
  `agenda_lint` run to exit 0 (criterion demonstrated in-workflow).

PR #562 merged to main (`mergedAt` non-null, GPG-signed); #560 auto-closed by `fixes #560`.

## Artifacts

- Code: `tools/agenda_lint.py`, `tools/test_agenda_lint.py`, `tools/CLAUDE.md` (PR #562, commit a412608).
- GitHub state: `umbrella:480` label on 9 issues; #560 CLOSED; #562 MERGED.
- Memory (LogiSoluMemory): `feedback_agenda_author_from_state_not_body.md` — updated How-to-apply
  to the mechanized gate (#560 DONE) + explicit-prefix rule.
- Non-blocking future note: lint queries `gh` serially per ref; batch only if agendas grow large.
