# 2026-06-02 1738 — Session 96 minutes

## Stated objective

**#564** — decompose `tools/pipeline/stages/common/verify_cli.py` (113 lines) to ≤80, satisfying the
80-line pipeline cap. Small self-contained 1:1:1 refactor. Operator chose this over the #456
homepage rebuild, the fresh-substrate clean-run, the #563 de-dup tooling eval, and the larger #561
PERT view.

## Pre-flight

- `sync_check`: **49 pass / 8 warn / 0 fail** on first run. The #401 saconsole WG-handshake flake
  did **not** recur. Warnings all expected (dormant dev03/target5, manual Chrome-tab verify).
- Open issues at start: ESACP **73**, LSKB **12** — matched the S95 agenda forecast exactly.
- `umbrella:480` live query: **#456** only (homepage rebuild).
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### Deliverable — `verify_cli.py` decomposition

Root of the bloat: the 16-field `VerifyContext` dataclass (18 lines) and `parse_verify_args`'s
16-field keyword return (17 lines) coexisted in one file — together they cannot fit under 80, so a
three-module split was required:

- **`verify_context.py`** (new, 26) — `VerifyContext` frozen dataclass, extracted verbatim.
- **`verify_args.py`** (new, 64) — `parse_verify_args()`, extracted. Now **reuses**
  `config_helpers._derive_zone()` and `_read_erp_user()` instead of the prior inline duplicates —
  closing the exact duplication the #564 body (and #563) flagged. The `hosts_map.yml` load was left
  inline (see Decisions).
- **`verify_cli.py`** (113 → **35**) — kept as a thin **facade**: defines `print_results()` and
  re-exports `parse_verify_args` + `VerifyContext` via `__all__`, so all 10 stage `verify.py`
  import sites (`from …verify_cli import parse_verify_args, print_results`) stay **unchanged**.

Zero call-site churn; nothing imports `VerifyContext` directly (confirmed by grep).

Verification: all three files ≤80 (35/64/26); import smoke test passes; `parse_verify_args('dev02')`
derives identical fields (target_ip, ssh_opts, bench_dir, site_url, domain, …) — confirming the
de-dup reuse did not change behavior; **live e2e against dev02** — stage_5 verify **3/3**, stage_7
verify **5/5**, exit 0; `config_helpers.py` confirmed byte-identical to HEAD;
`./tools/pre_commit_size_check.py` exits 0 (ratchet auto-updated verify_cli 113→35, recorded
verify_args 64 + verify_context 26).

### Ratchet constraint caught mid-flight

The plan originally added a shared `_load_host_cfg()` to `config_helpers.py`. Staging it tripped the
size ratchet — `config_helpers.py` would grow 39 → 46, over its baseline of 39. The ratchet forbids
**any** growth past baseline (files shrink, never grow), regardless of remaining headroom under the
80 cap. Rather than fight the gate, the hosts_map load was **inlined** in the new `verify_args.py`
(a new file, bound only by the 80 cap). The flagged duplication (zone + erp_user) was still
de-duped via the two pre-existing helpers; the hosts_map YAML read was never a *named-helper*
duplicate, so leaving it inline is proportionate.

### QA gates

- **Trigger-1 (commit): approve** (hard_block false). Confirmed dead-code deletion in the same diff,
  facade completeness across all 10 call sites, correct de-dup disposition, ratchet auto-update.
  Flagged the pre-existing `hasan_mighty` SSH-key hardcode carried verbatim from HEAD.
- **Trigger-2 (merge): approve** (hard_block false). Re-read full diff + both new files + facade +
  ratchet JSON + PR metadata. Advisory observation: `ssh.py` baseline records 83 — pre-existing
  cap violation worth a filed issue.

## Decisions

1. **Three-module split, not two** — `VerifyContext` + `parse_verify_args` exceed 80 together, so
   they had to live in separate files. Facade pattern chosen to keep all 10 call sites unchanged.
2. **`hosts_map.yml` load left inline** in `verify_args.py` rather than extracted to
   `config_helpers.py` — extraction would breach the ratchet baseline (39) on `config_helpers.py`.
   Respecting the mechanical gate took precedence over marginal further de-dup.
3. Commit type `refactor` (not the issue title's `chore`) — pure restructure, no behavior change.
4. Two observations found during the session were **filed-and-deferred**, not pursued
   (one-objective-per-session): #567 (`verify_args.py` hardcode) and #568 (`ssh.py` over-cap).

## Acceptance (#564)

- ✅ `wc -l verify_cli.py` → 35 (≤80) on main.
- ✅ All three files ≤80 (35/64/26); `pre_commit_size_check.py` green with new baselines.
- ✅ No behavioral change: derivation identical for dev02; live e2e stage_5 3/3 + stage_7 5/5;
  10 import sites untouched.

PR #566 merged to main (`mergedAt` non-null 2026-06-02T21:21:30Z, GPG-signed); #564 auto-closed by
`fixes #564`. Local main synced (tip `81f0d9d`); tree clean.

## Artifacts

- Code: `verify_cli.py` (113→35), `verify_args.py` (new, 64), `verify_context.py` (new, 26),
  `size_baselines.json` (PR #566, commit `866a10c`).
- GitHub state: #564 CLOSED; #566 MERGED; #567 + #568 OPEN (filed this session). `config_helpers.py`
  untouched (byte-identical to HEAD).
- No memory changes this session — clean execution of the established #521 decomposition pattern.
