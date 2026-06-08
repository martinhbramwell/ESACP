# 2026-06-07 2204 — Session 110 minutes

**Pinned objective:** #643 — build `template_v15` on Ubuntu 24.04 and rebuild `dev15_01`@24.04 as the acceptance box.

**Outcome:** #643 **COMPLETE and merged.** PR #659 merged to main (`2924664`); **#643 and #657 closed**. `template_v15` now builds on Ubuntu 24.04; `dev15_01` rebuilt from it and accepted. Six distinct noble-porting gaps and one hub-OOM incident were found and resolved en route — all caught by building before committing.

## What happened

1. **Session-start review** — sync_check 48✓ / 10⚠ / 2❌; both ❌ are the expected-down `dev02` (parked V16, agenda-sanctioned). ESACP open 83 / LSKB 13 confirmed. Branch cut `feat/643-os-per-major-template`; memory-grepped the #643 feedback set.

2. **Implementation** (`build.sh`, `01_os_prep.sh`, `cloud-init/packer-build/user-data`):
   - `build.sh` — OS-per-major `case` table (13→22.04 constrained ISO / 15→24.04.4 esacp-disk / 16→guarded-refuse), `--ubuntu-iso`/`--os-variant` overrides, `ubuntu_version` in metadata.
   - `01_os_prep.sh` — noble breakage points, each **v13-guarded so the v13 build stays byte-identical**.
   - Research corrected the locked plan: **wkhtmltopdf needs NO change** (no noble build exists; the jammy patched-Qt deb installs on noble via apt — plan item B.3 dropped).

3. **Six noble-porting gaps (each a distinct class):**
   1. **Stale uvicorn on :8088** spawned a *v13* build for a `version-15` request (dropped args → empty `{}`). Caught in ~45s, cleaned up. → **#654**. Worked around by invoking `job_worker.py` directly.
   2. **osinfo-db lacks `ubuntu24.04`** (toshiba's db caps at 20.04) → use `ubuntu20.04` hint for all arms (already documented `platforms/kvm/CLAUDE.md:9`; plan's `ubuntu22.04`-for-v13 suggestion would have broken v13).
   3. **RAM oversubscription OOM'd the hub** — see incident below. → **#655**.
   4. **24.04 fast-boot race** — passwordless sudo via first-boot `runcmd` lost to sshd/Packer; moved to install-time `late-commands`.
   5. **pipx isolated `uv` off PATH** → `bench init` `FileNotFoundError: 'uv'` → switched to `pip3 --break-system-packages` (brings bench + uv onto PATH, PEP-668 override).
   6. **Final-snapshot transient failure masked** by the pipeline (operator catch) — see below. → **#658**.

4. **Hub OOM incident** — the 4 GiB Packer build VM started while saconsole + dev01 + dev15_01 were all up (4+3+6+4 = 17 GiB > 15) → OOM killer took out **saconsole**, killing the detached build. Root cause: `build.sh`/`build_template` has **no host-memory guard** (the API VM-start path does). Recovered: restarted saconsole, cleaned leftovers, v13/v15 metadata intact. Operator correctly identified the deeper failure — I had **dropped the saconsole+1 rule** (`feedback_one_vm_at_a_time.md`) because it was not indexed in MEMORY.md. Rule honored thereafter (both dev VMs shut down for the build). → **#655**; memory updated + indexed.

5. **Build green** — with correct args + os-variant + RAM headroom, `template_v15`@24.04 built: `erpnext-v15-2026-06-07.qcow2`, metadata `ubuntu_version: 24.04`. `03_dep_fix` correctly skipped on v15.

6. **dev15_01 rebuild + acceptance** — added `provisionGeneric --wizard-mode none` (**#657**; record=interactive, replay=no recording, existing=V13 backups — none valid for a fresh v15 box) to drive a headless stages-1-9 rebuild. esacp-qa pre-destroy (approve-with-conditions; both met: verified clone resolves the 24.04 artifact, snapshots deleted before undefine). VM-only teardown (kept hosts_map/WG/DNS identity), then rebuild. **Acceptance: Ubuntu 24.04.4 / Python 3.12.3 / frappe+erpnext 15.110.0 / HTTPS 200 / apps installed.**

7. **Snapshot masking (operator catch)** — the final post-provision snapshot failed transiently ("Extra element disks in interleave" on old libvirt, right after heavy bench/site I/O) and the pipeline **masked it** (`create_snapshot` returns False but the macro reports "complete"). Operator: "if the new VM cannot make snapshots, the build failed." Investigated: NOT a 24.04 wall — dev01 (identical cdrom config) snapshots fine; the command succeeds on retry; stage-1's Baseline DID succeed. Real bugs = masking + no-retry. dev15_01 given its `ERPNext v15 Generic Baseline` snapshot manually (both snapshots now present). → **#658** (next 1:1:1).

8. **Persona side-bar** — operator proposed a **"Vizier"** knowledge-bearing infrastructure/hypervisor **skill** (CloudStack/KVM/Hyper-V/VPS + OpenTofu MCP), per-fork, centred on the Buzz user experience (non-tech owner never touches virsh; guardrails prevent self-inflicted outages like the OOM). Filed **#656** (child of #536). Read Junior's persona-audit note (`/dev/shm/NoteToSenior.txt`): current personas are thin served-docs/archetypes; Vizier would be the first real knowledge-bearing skill.

9. **Land** — esacp-qa pre-commit (approve-with-conditions: disclose the #643/#657 bundling → done in commit body + PR). Size ratchet bumped (`provision_generic.py` 75→76, `wizard_run.py` 68→70, both ≤80). GPG-signed `2924664`. esacp-qa pre-merge: approve. **PR #659 merged; #643 + #657 closed.**

## Issues filed this session
- **#653** — repeated per-edit permission prompts (memory-dir + session_close_audit) → add allowlist (housekeeping).
- **#654** — stale uvicorn on :8088 silently builds wrong major (args dropped).
- **#655** — `build.sh` creates the build VM with no host-memory guard → OOM-killed the hub.
- **#656** — "Vizier" infra/hypervisor skill (per-fork, Buzz-UX) — child of #536.
- **#658** — `create_snapshot` masks failures (provision reports success without a snapshot) + transient final-snapshot → **the agreed next 1:1:1**.
- (#657 — `provisionGeneric --wizard-mode none` — filed and **closed** by this PR.)

## Memories secured (LogiSoluMemory)
- `feedback_one_vm_at_a_time.md` — added: the Packer build VM counts toward saconsole+1; S110 OOM incident; any VM-creating op checks RAM first.
- `reference_template_build_newer_ubuntu.md` — **new**: noble/numbat porting playbook (reuse for v16@26.04).
- `project_end_state_v16_lts_current_stack.md` — #643 landed (template_v15@24.04 + dev15_01@24.04).
- `MEMORY.md` — **indexed** `one_vm_at_a_time` + `toshiba_environment` (the un-indexed gap that caused the OOM) + the new reference.

## Session-close audit
- Forward-tense promises → all executed (PR merged; issues filed; memories written). No "lesson noted" left only in prose — the saconsole+1 lesson maps to a memory-file write + MEMORY.md index.
- GH: #643/#657 closed by `fixes` on merge; #653/#654/#655/#656/#658 filed at moment of discovery.
- PR #659 `mergedAt` non-null before "done."
- Open-count drift: started 83; +#653/#654/#655/#656/#658 opened, −#643/#657 closed (#657 also opened this session) → re-confirm at S111 start.

## End state
- `main` synced, clean apart from Junior's untracked `on_boarding/onBoardingQRcode.png`. Tip = #659 merge (`2924664`).
- Kept branches (no prune): `feat/643-os-per-major-template` (merged), plus pre-existing `feat/480-*`, `feat/631-*`, `feat/617-*`, `feat/626-*`, `umbrella/v16-clean-run`.
- **VMs**: saconsole + **dev15_01** (new, 24.04) running; **dev01 shut off** (saconsole+1 honored — start-of-session had both dev01+dev15_01 up, a standing violation). dev02 parked.
- **#658** is the pinned next objective.
