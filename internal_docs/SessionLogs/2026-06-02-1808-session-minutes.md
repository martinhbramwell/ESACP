# 2026-06-02 1808 — Session 97 minutes

## Stated objective

**#568** — decompose `tools/pipeline/stages/common/ssh.py` (83 lines) to ≤80, satisfying the
80-line pipeline cap. Small self-contained 1:1:1 refactor. Operator set #568 directly (the S96
agenda's lead suggestion).

## Pre-flight

- `sync_check`: first run **48 pass / 8 warn / 1 fail**; immediate re-run **48 / 9 / 0**. The failure
  was the known **#401 saconsole WG-handshake flake** — intermittent, clean on re-run (consistent
  with the S96 agenda note). Flagged, not worked around.
- `clearKnownHosts`: 3 stale entries removed.
- Open issues at start: ESACP **74**, LSKB **12** — matched the S96 agenda forecast exactly.
- `umbrella:480` live query: **#456** only.
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### Deliverable — `ssh.py` decomposition along the target-VM-vs-hub seam

`ssh.py` carried two transport clusters: **target-VM** helpers (`_ssh_base`, `ssh_run`,
`scp_to_vm`, `rsync_to_vm`, all `you@target_ip`) and a **hub** helper (`hub_ssh_run`, ProxyJump
through the hypervisor to `HUB_VIRBR0_IP`) plus the `saconsole_ssh_run` backward-compat alias. That
seam is the natural decomposition boundary — not cosmetic line-shaving.

- **`ssh_hub.py`** (new, 28) — `hub_ssh_run()` + `saconsole_ssh_run` alias, moved verbatim with the
  `DEFAULT_HYPERVISOR` / `HUB_VIRBR0_IP` imports it needs.
- **`ssh.py`** (83 → **69**) — keeps the target-VM helpers; re-exports `hub_ssh_run` +
  `saconsole_ssh_run` from `ssh_hub` (`# noqa: F401`). Dropped the now-unused `DEFAULT_HYPERVISOR` /
  `HUB_VIRBR0_IP` imports.

Importer survey: target-VM helpers used across ~25 sites; `hub_ssh_run` has exactly **one** external
importer (`stage_2_network/tls_cert.py`); `saconsole_ssh_run` has **zero** (compat alias); `_ssh_base`
is private.

### Course-correction — ratchet blocked the approved option B

Plan offered two paths for the single hub importer: **A facade** (ssh.py re-exports) vs **B clean
repoint** (update tls_cert.py's import to `ssh_hub`). Operator chose **B**. On implementation, B
tripped the size ratchet: splitting tls_cert.py's combined `from …ssh import hub_ssh_run, ssh_run`
into two import lines grew it **63 → 64**, and the ratchet forbids *any* growth past baseline — even
on a file unrelated to #568. Rather than cosmetically shave a line off tls_cert.py (gaming the
ratchet), the constraint was **surfaced** to the operator, who switched to **A**. The facade keeps
tls_cert.py byte-identical.

This is the **second consecutive session** the ratchet's no-growth-past-baseline rule actively shaped
refactor mechanics (S96: `config_helpers.py` 39→46 blocked the `_load_host_cfg` extraction). Logged
as a cross-cutting constraint #563's tooling evaluation should fold in.

### QA gates

- **Trigger-1 (commit): approve** (hard_block false). Confirmed verbatim move, facade preserves the
  lone importer byte-identically, dead-code (`DEFAULT_HYPERVISOR`/`HUB_VIRBR0_IP`) deleted from
  ssh.py same commit, genuine two-path enumeration with operator sign-off.
- **Trigger-2 (merge): approve** (hard_block false). Re-read full diff + both files + baselines;
  GPG signature verified; `tls_cert.py` confirmed absent from diff.

## Decisions

1. **Decompose along the target-VM-vs-hub seam** — a genuine conceptual boundary, not line-shaving.
2. **Facade (A) over clean-repoint (B)** — forced by the size ratchet (B grows tls_cert.py 63→64,
   forbidden). Operator confirmed the switch. Keeps tls_cert.py byte-identical.
3. **`saconsole_ssh_run` alias kept** (zero importers, but removing a public name is a behavior
   change — out of scope for a pure refactor).
4. Commit type `refactor` (not the issue title's `chore`) — pure restructure, no behavior change.

## Acceptance (#568)

- ✅ `wc -l ssh.py` → 69 (≤80) on main; `ssh_hub.py` 28.
- ✅ `pre_commit_size_check.py` green with new baselines (83→69, ssh_hub 28).
- ✅ No behavioral change: import smoke test (all symbols resolve to same objects, alias intact,
  tls_cert.hub_ssh_run is ssh_hub.hub_ssh_run); live e2e stage_5 3/3 (`ssh_run`) + stage_6 6/6
  (`ssh_run` + `scp_to_vm`) against dev02.

PR #569 merged to main (`mergedAt` non-null 2026-06-02T22:01:23Z, GPG-signed); #568 auto-closed by
`fixes #568`. Local main synced (tip `7432cd5`); tree clean.

## Artifacts

- Code: `ssh.py` (83→69), `ssh_hub.py` (new, 28), `size_baselines.json` (PR #569, commit `9bf0792`).
  `tls_cert.py` untouched (byte-identical to HEAD).
- GitHub state: #568 CLOSED; #569 MERGED. No new issues filed this session.
- No memory changes this session — the ratchet-shapes-refactor-mechanics observation is logged here
  + carried in the next agenda as a #563 input, not yet promoted to memory (two data points; promote
  if it recurs a third time).
