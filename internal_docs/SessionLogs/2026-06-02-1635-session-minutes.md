# 2026-06-02 1635 — Session 95 minutes

## Stated objective

**#521** — decompose `tools/pipeline/stages/common/config.py` (87 lines) to ≤80, satisfying the
80-line pipeline cap. Small self-contained 1:1:1 refactor. Operator chose this over the #456
homepage rebuild, the fresh-substrate clean-run, and the larger #561 PERT view.

## Pre-flight

- `sync_check`: first run **48 pass / 8 warn / 1 fail**; two immediate re-runs **49 / 8 / 0**.
  The failure was **intermittent** (consistent with the known #401 saconsole WG-handshake flake /
  transient probe). Flagged, not worked around. Warnings all expected (dormant dev03/target5,
  manual Chrome-tab verify).
- Open issues at start: ESACP **72**, LSKB **12** — matched the S94 agenda forecast exactly.
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### Deliverable — `config.py` decomposition

The three field-derivation helpers (`_derive_zone`, `_ssh_transport`, `_read_erp_user`) moved
**byte-for-byte** into a new sibling `tools/pipeline/stages/common/config_helpers.py` (39 lines).
`config.py` dropped **87 → 60 lines**; `build_config()` unchanged. Dropped now-unused `yaml` /
`DEFAULT_HYPERVISOR` imports from `config.py`.

Investigation surfaced a fact the issue body missed: `_ssh_transport` was **not** purely private —
`verify_cli.py:17` imported it. That import was redirected to `config_helpers`. The 9 importers of
the public `build_config` were untouched.

Verification: all three `.py` files `py_compile` clean; import smoke test passes; both
`_ssh_transport` branches + `_derive_zone` confirmed identical; no unused imports introduced;
`./tools/pre_commit_size_check.py` exits 0 (ratchet auto-updated config.py 87→60, recorded
config_helpers.py at 39).

### Managerial-overview discussion → governance gap found

Operator asked for a managerial framing, then raised the inverse risk: a proliferation of small
files is also harmful **if** they carry duplicate code or are mis-classified — *do we have de-dup
and classification disciplines?* Investigation of what is **actually wired up** (not just
documented) found a two-tier asymmetry:

- **Mechanically enforced:** exactly one guard — the size ratchet (single git pre-commit hook →
  `pre_commit_size_check.py`). No duplicate-code detector, no classification/placement linter, no
  `.pre-commit-config.yaml`.
- **Judgment-only (esacp-qa + CLAUDE.md prose):** de-dup ("business logic in one place", "same
  primitive across transports", "delete dead code on extraction") and classification (macro→stage→
  unit taxonomy, dispatcher-vs-logic, no-subprocess-in-dispatcher, tests colocated).

Conclusion: **size has a machine guard; duplication and mis-classification have only a reviewer** —
a real silent-erosion gap that grows precisely as the anti-spiral rules succeed at producing many
small files. Filed as **#563**, including the requested evaluation query of OSS tooling.

### QA gates

- **Trigger-1 (commit): approve-with-conditions.** Three conditions: (1) commit format
  (refactor scope + GPG + co-author + `fixes #521`), (2) `fixes #521` present, (3) file a tracking
  issue for `verify_cli.py`'s pre-existing 113-line over-cap if none exists. All three resolved
  before committing — #564 filed for verify_cli.py.
- **Trigger-2 (merge): approve.** GPG signature verified, byte-for-byte move confirmed, dead-code
  deletion complete, 1:1:1 satisfied.

## Decisions

1. Helper module named `config_helpers.py` (operator's call, matching the issue's own suggestion)
   rather than a more descriptive name like `config_derivation.py` — the helpers are cohesive and
   `common/` is the established shared-primitive home.
2. Two observations found during the session were **filed-and-deferred**, not pursued
   (one-objective-per-session): #563 (governance gap) and #564 (verify_cli.py over-cap).
3. Commit type `refactor` (not the issue title's `chore`) — pure restructure, no behavior change.

## Acceptance (#521)

- ✅ `wc -l config.py` → 60 (≤80) on main.
- ✅ `pre_commit_size_check.py` green with new baseline.
- ✅ No behavioral change visible to callers (9 `build_config` importers untouched; byte-for-byte move).

PR #565 merged to main (`mergedAt` non-null 2026-06-02T19:15:59Z, GPG-signed); #521 auto-closed by
`fixes #521`. Local main synced (tip 795b301); tree clean.

## Artifacts

- Code: `config.py` (87→60), `config_helpers.py` (new, 39), `verify_cli.py` (1-line import
  redirect), `size_baselines.json` (PR #565, commit 44fe6c4).
- GitHub state: #521 CLOSED; #565 MERGED; #563 + #564 OPEN (filed this session).
- No memory changes this session.
