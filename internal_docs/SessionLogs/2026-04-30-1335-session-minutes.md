# 2026-04-30 1335 — Session minutes

## Objective

Close out PR #324 (#319 fix) and resolve #322 (`--write-stubs` strips comments
from `customisation_attribution.yml`) — operator authorized doing both in
the same session per CLAUDE.md "closeout of prior work + one new substantive
issue" carve-out.

## State at start

- main tip: `f98fadb` (1204 docs commit, **local-only — not yet on origin**)
- PR #324 OPEN, `mergedAt: null`
- 28 open issues
- sync_check: 45 passed, 9 warnings, **2 expected ❌** (dev02 shut off per
  `feedback_one_vm_at_a_time.md`)

## What happened

### Closeout of #319 / PR #324

1. `gh pr merge 324 --merge` → PR #324 merged at `0b2ef94`
   (2026-04-30T16:43:07Z), merge-commit method matching repo convention
   (#323, #321, #316).
2. #319 auto-closed by `fixes #319` keyword (closedAt 16:43:08Z).
3. Local main (`f98fadb`, unpushed docs commit) had diverged from new
   origin/main tip — `git pull --rebase origin main` replayed the docs
   commit on top of the merge → new commit `b5d0dce` (re-signed). Pushed.

### #322 — `--write-stubs` comment preservation

Branch: `fix/yaml-comment-preservation-322` off main.

**Mechanism chosen** (Path 1 from issue's enumeration, after operator
explicitly accepted the new dep):
- `ruamel.yaml` round-trip mode in `attribution.py:_yaml()`
- `preserve_quotes=True`
- `width=4096` — discovered as necessary during e2e sanity-check against
  the real `config/customisation_attribution.yml`; default `width=80`
  was line-wrapping the long `dt_in` flow list at line 43

**Substrate change**: `sudo apt install -y python3-ruamel.yaml` on
controller (operator-run; not registered in `check_tools.py` —
pre-existing limitation: `check_tools.py` only tracks CLI binaries).

**Tests** (5 added, colocated per `feedback_tests_with_code.md`):

| Test | Acceptance criterion (from issue) |
|---|---|
| `test_322_append_stubs_preserves_header_comments` | (1) header comments survive |
| `test_322_append_stubs_preserves_existing_entries` | (3) operator-resolved entries survive |
| `test_322_append_stubs_adds_new_todo` | (4) new TODO stubs appended |
| `test_322_no_op_rewrite_is_byte_identical` | regression guard for default `width=80` line-wrap on `dt_in` |
| `test_322_append_stubs_preserves_top_level_key_order` | top-level dict insertion order |

Full module suite (19 `test_*.py`) green.

**Real-substrate validation** (per `feedback_test_real_before_commit.md`):
- Backed up `config/customisation_attribution.yml` to
  `/tmp/attr-pre-322.yml.bak`.
- Ran `./tools/identify_bad_customisations.py --substrate dev01 --write-stubs`
  → 203 custom_docperm stubs appended; 38-line schema-doc header preserved
  verbatim; `Customer-compras`, `Delivery Trip-Form`, `IRS 1099 Form`
  intact in their original positions.
- Restored backup (md5 match: `aab898d1...`) — the 203 dev01 stubs are
  Phase 2 attribution work, not part of this bug-fix PR.

### Closeout of #322 / PR #325

- Commit `d97b266` (GPG-signed by `9C6BCEA8...A9704E8`).
- PR #325 opened → body documents mechanism + width=4096 finding +
  ruamel.yaml prereq + the e2e dev01 evidence.
- `gh pr merge 325 --merge` → merged at `0535d1d` (17:34:44Z).
- #322 auto-closed at 17:34:45Z.
- Local main fast-forwarded to `0535d1d`.

## Findings (logged to durable homes)

| Finding | Where it lives |
|---|---|
| ruamel.yaml NOT a transitive dep on this controller (issue's "already a transitive dep" wording was speculative) | PR #325 body |
| Default `width=80` line-wraps long `dt_in` flow list — must set `width=4096` or wider | Commit `d97b266` body + `test_322_no_op_rewrite_is_byte_identical` regression guard |

## What was deferred (filed elsewhere, not as new issues)

| Concern | Disposition |
|---|---|
| `delta_report.json` written to project root by audit script | Mentioned in PR #325 "Out of scope". Not filed — `feedback_not_perfection_project.md` (cosmetic, trivial workaround `--output /tmp/...`) |
| `check_tools.py` doesn't validate Python packages (PyYAML, ruamel.yaml, etc.) | Pre-existing limitation, scope creep to fix here. Not filed — operator can install on demand |
| MEMORY.md line 83 staleness (Open-Issues Purge Plan references 4 closed issues) | Carried forward from 1204 agenda's Backlog. Still pending |
| #278 (dev01 unreachable carve-out in sync_check) | Already filed pre-session; surfaces every sync_check |

## State at close

- main tip: `0535d1d` (#325 merge commit)
- 26 open issues (down from 28: #319, #322 closed)
- branches `feat/auto-rules-attribution-319` and `fix/yaml-comment-preservation-322`
  remain on remote per `feedback_keep_merged_branches.md`
- working tree clean
- `/tmp/attr-pre-322.yml.bak` left in place (transient)

## Audit confirmations

- All forward-tense statements traced to executed tool calls (no
  unresolved promises).
- All findings logged to durable homes (PR body, commit body, test
  files).
- Both PRs (#324, #325) `mergedAt` non-null at session close.
- No new feedback memory file warranted (no new behavioural lesson
  beyond what `feedback_enumerate_mechanisms_before_committing.md`
  and `feedback_test_real_before_commit.md` already cover).
