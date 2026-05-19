# Session Minutes — 2026-04-16 0100

**Objective**: Audit monolith problem, plan Gen 3 pipeline completion, establish anti-spiral rules

**Outcome**: Planning complete. No code shipped (all changes reverted). 10 issues filed. Rules in CLAUDE.md.

---

## What happened

1. **Sync check**: 42 passed, 4 failures (all expected — dev VMs not running), 11 warnings
2. **Reviewed agenda** from 2026-04-15-2300: E2E acceptance test for `esacp.py provision/destroy`
3. **Discovered provision mode gap**: `provision.py` (restored) and `provision_generic.py` (generic) are near-identical — differ by 2 parameters
4. **Attempted fix**: Merged into one parameterised `provision.py`, added `--generic` flag to CLI
5. **Discovered wizard completion gap**: Generic path has record/replay/existing wizard steps. CLI didn't have them.
6. **Made it worse**: Added 59 lines to esacp.py. User caught it. Extracted to `wizard_completion/run.py`. Still duplicated with job_worker.py.
7. **Root cause identified**: 4 monoliths (esacp.py 1693 lines, api.py 999, job_worker.py 339, install_specific.py 721) survived the pipeline decomposition. They partially duplicate, partially wrap, partially contain trapped business logic that should be pipeline primitives.
8. **Full audit conducted**: Catalogued every function in all 4 monoliths. Found ~8 trapped operations, ~124 dispatch functions, ~15 proper delegations. Also found dead Gen 1 orchestrators (~1160 lines).
9. **Ansible overlap audit**: Zero proposed primitives duplicate Ansible. Python owns orchestration, Ansible owns infrastructure-as-code. Clean boundary.
10. **Plan written**: 9-phase extraction plan + 9 anti-spiral rules
11. **All code changes reverted**: Working tree matches origin/main
12. **10 issues filed**: #189-#198
13. **Anti-spiral rules added to CLAUDE.md** — dispatcher file size limits, business logic location rules, pre-commit enforcement

## Issues opened

| Issue | Title |
|---|---|
| #189 | Phase 1: Pre-flight validation primitives |
| #190 | Phase 2: Host registration primitive |
| #191 | Phase 3: VM build primitives (remote + local) |
| #192 | Phase 4: macro/destroy.py |
| #193 | Phase 5: Packer build + memory guard + VM power |
| #194 | Phase 6: VPN verify + observability creds + Ansible filter |
| #195 | Phase 7: Dispatcher layer — thin monoliths |
| #196 | Phase 8: Delete dead Gen 1 files |
| #197 | Phase 9: install_specific.py decomposition |
| #198 | Phase 0: Anti-spiral rules + pre-commit hook |

## Key decisions

- **No code changes this session** — plan only, revert all attempts
- **Phase 0 (#198) must be done first** — rules before implementation
- **provision_generic.py stays for now** — will be merged during Phase 7 when dispatchers are thinned
- **Pre-commit hook** is the enforcement mechanism, not aspirational rules
