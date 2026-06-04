# 2026-06-03 1717 — Session 101 minutes

**Objective (operator-pinned):** #583 — derive the guest VM user `you` from config
across the pipeline (deferred half of the #567/#582 operator-SSH-identity bundle).

## Outcome — COMPLETE

**#583 ✅** — PR **#592** merged to main (`mergedAt 2026-06-03T21:15:09Z`, merge
commit `e0b7c22`); issue auto-closed via `fixes #583` (`21:15:11Z`). Substantive
1:1:1: branch `refactor/583-guest-vm-user` (single commit `3e81688`), kept (no prune).

What landed:
- **New SSoT resolver** `guest_vm_user()` + `GUEST_VM_USER` constant in
  `tools/host_identity.py`, reading `ansible_user` from `ansible/group_vars/kvm.yml`
  (default `you`); added to the shell-eval emitter. Mirrors #582
  `operator_ssh_key()`/`hypervisor_user()`.
- **22** KVM-active `you@` SSH/SCP/rsync literals in `tools/pipeline/**` → `f"{GUEST_VM_USER}@…"`.
- `tools/cli/_common.py:vm_user()` delegates to the resolver (config param kept for compat).
- cloud-init hub template → `{{ vm_user }}` (StrictUndefined makes it mandatory);
  `hub_seed_iso.py` passes `vm_user=GUEST_VM_USER`.
- `platforms/packer/build.sh` → `VM_USER="${VM_USER:-you}"`; `build_template.py`
  injects `VM_USER={GUEST_VM_USER}` into the remote build (the hub only receives
  `platforms/packer/`, not `tools/`, so it cannot call the resolver itself).
- Colocated tests in `tools/test_host_identity.py` (wiring, constant==resolver, fallback).

**Acceptance — all green (no behavioral change):** 21 touched modules import cleanly;
resolver wiring + fallback assertions pass (run via standalone harness — pytest not
installable here, PEP 668; harness since deleted); cloud-init renders **byte-identical**
to HEAD with `vm_user='you'`; `grep you@ tools/pipeline tools/cli` clean; size check exit 0.

## Also this session (pre-objective)

**#584 ✅** — RUNBOOK §5b + `Cld.sh` satellite-terminal SSH used the guest-VM user
`you@` instead of the controller login user → tmux "session not found". Root-caused
during a support question (operator's `tmux attach -t esacp` kept failing; the actual
trigger turned out to be **Gmail autocorrect** rewriting `esacp`→`escape` in transit,
but the investigation surfaced a genuine doc bug). Fixed both sites to role-based
`${USER}@`, added PowerShell to the double-quote-correct note. Doc-only direct-to-main,
commit `e65792e`, `fixes #584`.

## Discipline notes

- **esacp-qa**: T1 pre-commit + combined pre-push/pre-merge on #592 → **approve-with-conditions**
  (hard_block). Single condition — file a follow-up for the real-name `"hasan"` ProxyJump-user
  defaults it found (`hypervisor_helpers.py:33` + `env_kvm.py:20`, operator-identity / #582 class,
  NOT #583's guest-user scope). **Condition met: #591 filed.** Also a separate `approve` on the
  #584 doc fix. Close-batch T1+T3 on this minutes/agenda commit: self-referential per S58.
- **Size ratchet**: 16 import-only +1/+2 baseline bumps in `tools/size_baselines.json` (S84
  precedent); `build_template.py` kept under the 80-line cap (78) via single-line import; no file
  decomposed (out of #583 scope; would break 1:1:1). Surfaced in the commit body — not gamed.
- **Out of scope, durably homed in the merged commit body**: (a) `you_gh_ce_sri` deploy-key
  *filenames* in stage_3 verify.py (not `you@` targets, outside #583 enumeration); (b) the
  `"hasan"` defaults → now #591.
- Junior's untracked `on_boarding/onBoardingQRcode.png` left untouched throughout (correctly
  unstaged after a `git add -A` swept it in).

## Counts

- **ESACP**: 74 (start) → **75** (now). **Senior net 0** (#583 closed −1; #591 filed +1; #584
  filed+closed net 0). The +1 total delta is **Junior's** concurrent on_boarding churn
  (#585/#587 opened today) — outside Senior jurisdiction.
- **LSKB**: 12 (unchanged). Sibling repos not surveyed (no bucket-2/3 work this session).
- **dev01/dev02**: untouched (no VM ops — refactor was controller-side, byte-identical inventory).
- **TRIVIAL_FIXES.md**: 1 entry (S33 LSMem monitor) — unchanged.

## Diff-based introspection-sidebar trigger

NEGATIVE — no MEMORY.md indexing changes; no carry-forward operator-reminder attrition this
session. S101 is a 1:1:1-substantive close (+ one doc-only direct-to-main fix). Sidebar still
due ~S103–S105 (S98 was the last).
