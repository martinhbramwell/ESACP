# 2026-06-08 1240 — Session 112 minutes

> Objective: **#663 — test-execution gate**, bundled with symptom fixes **#664 / #665 / #666**.
> Outcome: **DONE** — PR #667 squash-merged to main (`fa4962d`); all four issues CLOSED. The gate
> is live on three surfaces (CI proven green in 15s) and the colocated suite is 59/59 green.

## What happened

**#663 — the test-execution gate (the objective).**
- The project mandated colocated tests but nothing ran them as a suite (S111 root cause), so they
  rotted unseen. Built a dependency-free gate:
  - **`tools/run_tests.py`** — discovers every `test_*.py` under `tools/` (excludes guest-deployed
    `tools/vm_scripts/`) and runs each **as an executable** (`./path/test_x.py`). A missing `+x`/shebang
    surfaces as a **failure**, never silently masked (the load-bearing #663 contract). Exits non-zero
    on any failure.
  - **`tools/testkit.py`** — ~50-line stdlib substitute for pytest (`monkeypatch`/`tmp_path` shims by
    parameter name) so collector/fixture tests self-run. House style: **no pytest**.
  - **`tools/pre_commit_exec_check.py`** — asserts staged shebanged `tools/**/*.py` and `test_*.py`
    carry index mode `100755` (excludes `vm_scripts/`).
- **Three gate surfaces**: (1) CI — `.github/workflows/tests.yml`, authoritative, on PR + push to
  main; (2) `sync_check.sh §18` — session can't start green while the suite is red; (3) pre-commit
  exec-bit lint chained after the size ratchet (local `.git/hooks/` is untracked → canonical content
  documented in `tools/CLAUDE.md`).

**Baseline investigation drove the design.** Running all 60 `test_*.py` as executables gave 43 pass /
2 fail / 14 not-runnable / 1 not-a-test:
- The **2 fails** were exactly #664/#665. ✅ gate catches real rot.
- `tools/vm_scripts/.../test_data.py` is **not a test** (guest-deployed data module, relative imports)
  → excluded from the runner + exec-lint.
- **#666 undercounted**: the not-invokable footprint is **14 files, not 3** — 9 more `customisation_audit`
  tests missing `+x`, plus 4 collector-style + `test_host_identity` that had **no shebang/main** (so
  `chmod +x` alone would be a false green). Corrected via a scope comment on #666; all 14 fixed.

**Symptom fixes.**
- **#664** `test_hub_seed_iso`: added `vm_user` to `_PARAMS` (stale since #583) + `username:` assertion.
- **#665** `test_hosts_map_remove`: frozen inline fixture + `zzz_test_host` — decouples from the live,
  evolving `hosts_map.yml` and the now-real `dev01`. Keeps the byte-identity round-trip.
- **#666** (14-site): `chmod +x` 12 files; shebang + `sys.path` + `testkit` main on 5 not-self-running
  files.

**Operator decisions this session.**
- Bundle the three symptom fixes with #663 (causally coupled — can't land a green-gating CI while the
  suite is red).
- CI strictness = **full green required**; trigger = **PRs + push to main**.
- **Size-ratchet vs tests**: exempt `test_*.py` from the anti-spiral cap (self-run scaffolding adds
  ~10 mandatory lines; the cap targets *logic* monoliths, not tests). Implemented in
  `pre_commit_size_check.py`; 17 inert `test_*` baselines removed from `size_baselines.json`.

**QA-driven correction.** esacp-qa pre-commit returned `approve-with-conditions`: `testkit.py`/
`run_tests.py` (86/81 lines) fell in the must-split zone yet weren't covered by the `test_*` exemption
(silently unmatched at `tools/` root). Discharged via QA's option (a) — an **explicit named**
`TEST_INFRA = {run_tests.py, testkit.py}` exemption + CLAUDE.md note (chosen over gutting docstrings).
Re-verified, then pre-push/pre-merge `approve`.

## Verification (acceptance)
- **59/59 green** via `./tools/run_tests.py` locally and in a clean venv with only
  `PyYAML Jinja2 ruamel.yaml`.
- **CI passed in 15s** on a clean GitHub runner — the authoritative acceptance.
- Anti-masking proven: drop `+x` → FAIL/rc 1. `test_data.py` correctly excluded.
- Both pre-commit checks pass; `sync_check §18` renders green; `bash -n` clean.

## Issues closed this session
- **#663** (gate), **#664**, **#665**, **#666** — all auto-closed via `fixes` on the squash-merge.

## Memories secured (LogiSoluMemory `255c673`)
- `feedback_tests_with_code.md` — caveat rewritten: the S111 silent-rot gap is **closed**; gate
  surfaces + `testkit` + `TEST_INFRA` exemption documented; lesson "trust the runner, not
  green-by-absence." No MEMORY.md index change (entry already present).

## Session-close audit
Clean. All four issues CLOSED via `fixes`; PR #667 `mergedAt` non-null; gate proven green in CI;
lesson durably homed + pushed. No issues filed this session (one scope-correction comment on #666).

## End state
- **main tip**: `fa4962d` (S112 squash-merge of PR #667; #663/#664/#665/#666 closed).
- **Kept branches** (no prune): `feat/663-test-execution-gate` (merged), plus prior S110/S111 set.
- **Open issues**: ESACP **88** (start-92, −4 closed, 0 filed), LSKB **13**.
- **VMs**: saconsole + dev15_01 (Ubuntu 24.04) running; dev01/dev02 shut off by design.
- **sync_check**: 4 expected FAILs (dev01/dev02 down by design); plus §18 now green.
- **LogiSoluMemory**: clean, pushed (`255c673`).
