# 2026-06-03 1848 — Session 102 minutes

**Objective (operator-pinned):** #591 — replace the hardcoded operator-name
`"hasan"` ProxyJump-user defaults in two pipeline files with the SSoT
`hypervisor_user()` resolver (the operator-identity-literal class left behind
by #582; direct sibling of S101's #583 guest-VM-user pass).

## Outcome — COMPLETE

**#591 ✅** — PR **#595** merged to main (`mergedAt 2026-06-03T21:36:59Z`, merge
commit `4000f3c`); issue auto-closed via `fixes #591` (`21:37:01Z`). Substantive
1:1:1: branch `refactor/591-proxyjump-user` (single commit `20e174b`, GPG `G`),
kept (no prune).

What landed:
- `tools/pipeline/orchestration/hypervisor_helpers.py` —
  `tcp_probe_via_hypervisor` default param `user: str = "hasan"` →
  `user: str | None = None` with `user = user or hypervisor_user()` in-body.
  Only caller relying on the default is `verify_build_vm.py:46`;
  `build_vm_poll.py` passes `hyp_user` explicitly (unaffected).
- `tools/pipeline/stages/env_kvm.py` — `KvmEnv.hypervisor_user: str = "hasan"`
  → `field(default_factory=resolve_hypervisor_user)` (aliased import avoids the
  field/function name shadow). Downstream `upload_seed.py` / `build_vm_seed.py`
  read `env.hypervisor_user`; the `metadata_dir` property already derived it.
- `tools/pipeline/stages/test_env_kvm.py` — NEW colocated standalone test
  (no-pytest convention, executable, exit 0/1); asserts
  `KvmEnv().hypervisor_user == hypervisor_user()` for both constructors.

**Acceptance — all green (byte-identical):** `hypervisor_user()` resolves to
`'hasan'` today (`hosts_map.yml:157`), so behaviour is unchanged. New test exit 0;
existing `test_virt_install_ram.py` PASS; size ratchet exit 0 after baseline
bumps; `grep '"hasan"' tools/pipeline/` clean at the two touched sites. Test
re-confirmed green on merged main.

## Also this session

**#594 ✅ filed** — esacp-qa pre-commit scan surfaced a residual same-class
operator-identity literal in `template_metadata.py:8`
(`METADATA_DIR = "/home/hasan/esacp-packer-output"`); the broader Senior scan
added a second site, `section_a2e_controller_pubkey.sh` (`/tmp/hasan_mighty.pub`
×4). Both pre-existing, NOT introduced by #591, out of its scope. Filed as one
issue enumerating both sites (root-cause-over-symptoms) for a dedicated 1:1:1.

## Discipline notes

- **esacp-qa**: T1 pre-commit on the #591 diff → **approve-with-conditions**
  (hard_block:false, T1 advisory). Two conditions, both met: (1) file the
  residual-literal follow-up → **#594**; (2) Conventional + GPG-signed commit
  with no `"hasan"` literal in subject/body → satisfied (`20e174b`).
- **Size ratchet**: 2 import-only +1 baseline bumps (hypervisor_helpers 69→70,
  env_kvm 40→41) + 1 new test entry (37) in `tools/size_baselines.json`.
  Surfaced, not gamed. (Fifth+ data point on ratchet import-bump ergonomics —
  feeds #563.)
- Junior's untracked `on_boarding/onBoardingQRcode.png` left untouched.

## V16 question (operator-raised)

Operator asked how many sessions remain to an error-free V13→V16 migration.
Answer recorded: live `umbrella:480` → **#456 only**; happy path **~2 sessions**
(#456 homepage + one fresh-substrate clean-run acceptance), realistic budget
**2–4** since the clean-run is itself the defect-discovery mechanism.
**Operator pointed S103 at #456.**

## Counts

- **ESACP**: 75 (start) → **75** (now). **Senior net 0** (#591 closed −1;
  #594 filed +1). Junior on_boarding churn separate.
- **LSKB**: 12 (unchanged). Sibling repos not surveyed (no bucket-2/3 work).
- **dev01/dev02**: untouched (controller-side refactor, byte-identical inventory).
- **TRIVIAL_FIXES.md**: 1 entry (S33 LSMem monitor) — unchanged.

## Diff-based introspection-sidebar trigger

NEGATIVE — no MEMORY.md indexing changes; no carry-forward operator-reminder
attrition this session. S102 is a 1:1:1-substantive close. Sidebar still due
~S103–S105 (S98 was last), but **S103 is operator-pinned to #456** — sidebar
defers to S104+ unless carry-forward reminders cross the 3+ threshold first.
