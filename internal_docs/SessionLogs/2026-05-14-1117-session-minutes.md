# 2026-05-14 1117 — Session 50 minutes

## Objective

**LSKB#20 Path 1 execution** — rebuild dev02 at production-snapshot frappe v13.41.3 / erpnext v13.39.2 versions. Resume the S47/S48 paused work now that ESACP#388 (packer-as-saconsole-dep) was closed in S49. Bucket-2 substrate-readiness session, strict-LSKB#20-only scope per operator pick at session start (no production data restore, no bench migrate; LSKB#15 retry stays a separate session).

## Outcome — paused at packer env-var-passing flaw; ESACP#390 filed; LSKB#20 stays open

Path-1 sub-sequence ran to completion mechanically (exit 0 throughout); acceptance verification revealed the produced template is at version-13 branch tip, not the pinned tags. Root cause is a latent packer-script env-var-passing flaw in the repo since the scripts were authored.

### What ran cleanly on S50

- **Saconsole repo aligned** — `cd /opt/esacp && git pull` from `5230522` (Apr 22) to `3336e4a` (current main). One dirty file (`prototypes/cytoscape/package-lock.json` — 3-line npm-injected `engines` block) stashed as `stash@{0}` before pull, not destroyed.
- **Old metadata preserved on toshiba** — `cp ~/esacp-packer-output/erpnext-v13-latest.json ~/esacp-packer-output/erpnext-v13-2026-03-30.json` (run as the toshiba hypervisor user). Old metadata still readable; old qcow2 `erpnext-v13-2026-03-30.qcow2` retained in esacp libvirt pool.
- **Packer build executed** — `bash /opt/esacp/platforms/packer/build.sh --frappe-branch v13.41.3 --erpnext-branch v13.39.2` from saconsole, 37 min wall (09:00:21 → 09:37:57), exit 0. New artifact `erpnext-v13-2026-05-14.qcow2` in esacp pool (40 GB allocated). All 8 phases reported success.
- **dev02 destroy + rebuild** — `./tools/esacp.py destroy dev02` ran all 8 macro/destroy.py steps clean (WG peer / VM+snapshots / hosts_map / group_vars / inventory / hub WG / SOPS keys / known_hosts). `./tools/esacp.py addHost dev02 --vm-role dev:unspecified --wg-ip 10.10.0.17 --virbr0-ip 192.168.122.27 --hypervisor toshiba --zone development` re-registered. `./tools/esacp.py provisionGeneric dev02 --wizard-mode replay --wizard-arg pseudo-co-wizard.spec.js` ran stages 1-9 + final snapshot `ERPNext v13 Generic Baseline` cleanly.

### Where verification failed

`ssh erpadm@10.10.0.17 'bench list-apps'` reports **`frappe 13.58.22 / erpnext 13.55.2`** — version-13 branch tips, NOT the pinned `v13.41.3 / v13.39.2`. SHA-level confirmation: `apps/frappe` HEAD `5ec534b8...` (= v13.58.22) on branch `version-13`; `apps/erpnext` HEAD `37e00a66...` (= v13.55.2). The packer build log (lines 1434, 1514) shows `git clone … --branch version-13 --depth 1` for both apps despite the build.sh CLI flags requesting v13.41.3 / v13.39.2.

### G7 — packer `execute_command` strips `environment_vars`

`platforms/packer/erpnext-v13.pkr.hcl:77` (and lines 87 / 100 / 107) uses `execute_command = "sudo -Hu ${var.erp_user} env ERP_USER=${var.erp_user} bash {{ .Path }}"`. The `sudo -H` strips environment, then `env ERP_USER=...` resets to **only** that one var, silently dropping the `FRAPPE_BRANCH` and `ERPNEXT_BRANCH` packer set via `environment_vars`. Inside `02_bench_install.sh:20-21` the `${VAR:-version-13}` defaults kick in. Latent since the scripts were written (Mar 2026 mtime); first surfaced now because every prior call to `build.sh` used default flags. No bit-rot framing — the flaw has been present from day one and the calling pattern simply never exercised it before.

### Wizard replay aside (out of LSKB#20 scope)

Playwright wizard `pseudo-co-wizard.spec.js` replay against the rebuilt dev02 timed out (`waitForResponse` 180s exceeded). Stages 1-9 + snapshot landed before the wizard ran; substrate is in a half-configured state (no Company created via the wizard). Not in LSKB#20's strict scope to investigate; recorded here in case it recurs in S52's retry.

## Filed + corrected

- [**ESACP#390**](https://github.com/martinhbramwell/ESACP/issues/390) — `bug(packer): execute_command strips FRAPPE_BRANCH/ERPNEXT_BRANCH env vars — build.sh CLI flags silently ignored`. Proposed fix: explicit `env ERP_USER=… FRAPPE_BRANCH=… ERPNEXT_BRANCH=… bash` in the `execute_command`. Acceptance: end-to-end CLI flag → actual `bench list-apps` versions match.
- **Toshiba metadata correction** — `~/esacp-packer-output/erpnext-v13-latest.json` (in the toshiba hypervisor user's home) rewritten to reflect reality: `frappe_branch: version-13` / `erpnext_branch: version-13`, with `frappe_sha` / `erpnext_sha` / `frappe_version` / `erpnext_version` added and a `note` cross-referencing ESACP#390. Original (misleading) values preserved in the historical record by the qa-log narrative below; the toshiba file is the live single source of truth and now matches the qcow2 contents.

## Pointer-comments posted

- [LSKB#20 issuecomment-4452006631](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4452006631) — Path-1 pause + ESACP#390 cross-link + state-at-pause + updated step sequence (ESACP#390 fix becomes prerequisite #2).
- [ESACP#353 issuecomment-4452009096](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4452009096) — Plan-B parent Session-50 ledger entry; step-result table; ladder state; `fixes` tally unchanged at 16.
- [LSKB#6 issuecomment-4452010889](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4452010889) — Phase 4 ladder state with three-layer block chain (ESACP#390 → LSKB#20 → LSKB#15 → LSKB#16).

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| ESACP#390 | filed (open) | Packer env-var-passing flaw — root-cause of LSKB#20 Path-1 build failure |
| LSKB#20 | pause-comment posted; **stays open** | Blocked on ESACP#390; substrate-version-alignment cannot proceed until packer flag pass-through works |
| LSKB#15 | unchanged; **stays open** | Downstream-of-LSKB#20 |

## Substrate state changes committed (S50 close)

dev02 destroy + addHost regenerated WG keypair and re-wrote 4 repo files. Committed with the session-close batch (vs the 2026-04-26 precedent's separate state commit). Files: `hosts_map.yml`, `ansible/group_vars/all.yml`, `ansible/inventory/kvm.yml`, `config/wireguard/keys.sops.yml`. dev02 wg_pubkey changes from S47-era to S50-era — keys.sops.yml SOPS-decrypted preshared/private keys also rotated. New dev02 identity: same IPs (10.10.0.17 / 192.168.122.27) but fresh keys.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T4 (pre-destroy on dev02) | `a6b1f1c9893d9b21c` | approve | Clean approve, hard_block: true. Three paths enumerated; Path A (pipeline-canonical 2026-04-26 pattern) chosen and operator-confirmed via AskUserQuestion. Anti-rubber-stamp positive on path enumeration substance + production-data-reach check. Non-blocking note: minor 8-step vs 9-step labeling inconsistency between `tools/CLAUDE.md` prose and the macro/destroy.py code labels post-#305 (cosmetic; functionality present at the renamed Step 8 `known_hosts_cleanup`). |
| T1+T3 (this session-close commit) | _pending — irreducible self-referential row per S46/S47/S48/S49 precedent_ | _pending_ | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3. Combined-batch commit: minutes (this file) + next-agenda (S51) + qa-log (this row + T4 row above) + 4 substrate-state files (dev02 WG re-registration). Combined per 2026-04-26 precedent (single closing state commit). |

## Counts at session end

- ESACP open: **38** (was 37; +#390 packer env-var bug).
- LSKB open: **9** (unchanged; #20 paused, not closed).
- ce_sri open: 5 (unchanged); LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged).
- Cross-repo `fixes` tally unchanged at **16**.

## TRIVIAL_FIXES.md status

Unchanged — 2 monitor-only entries (S33 LSM Trigger-3 skip pattern, S47 `tools/secrets.py` `+x` bit).

## Carry-forward operator-reminders (delta)

- **ESACP#390** (NEW) — packer env-var-passing flaw. Blocks LSKB#20 Path 1.
- **LSKB#20** — Path 1 attempted S50, paused on ESACP#390. Old-metadata-preservation pattern executed cleanly; new template artifact at `erpnext-v13-2026-05-14.qcow2` (at version-13 tip, retained); metadata corrected to reflect reality. When ESACP#390 lands, S(N) re-runs `build.sh --frappe-branch v13.41.3 --erpnext-branch v13.39.2` and acceptance is the bench-versions check.
- **LSKB#15, LSKB#16, LSKB#18, ESACP#387** — unchanged from S49 carry-forward.
- **dev02 substrate state** — rebuilt S50 from new template at version-13 tip; fresh WG keys; wizard replay timed out so no Pseudo-Co Company configured; production data + S47 staging gone. Disposable; will be destroyed/rebuilt again in the LSKB#20-resume session.
- **`tools/secrets.py` +x bit (F4)** — unchanged (TRIVIAL_FIXES monitor-only).
- **LogiSoluMemory Trigger 3 skip pattern** — unchanged.
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.
- **Saconsole stash** — `stash@{0}` on `/opt/esacp` saconsole-side preserves the npm-injected `package-lock.json` `engines` block. Restore-on-demand only if a saconsole-side npm operation depends on it; otherwise drop on next saconsole repo touch.

## Shape note

Substrate-investigation-class with one new bug filed and the existing blocked issue still blocked. Tracks the S47 precedent (LSKB#15 paused → LSKB#20 filed) and S48 precedent (LSKB#20 paused → ESACP#388 filed) shape exactly — each session resolves the prior blocker and uncovers the next-layer blocker. Block chain at S50 close: ESACP#390 → LSKB#20 → LSKB#15 → LSKB#16. Minutes ~95 lines — within the S40–S49 73–95 baseline; substrate-state commit + corrected-metadata audit-trail material pushes toward the upper end.

## Saconsole-discipline check

ESACP#390 is bucket-1 substrate-config (build-mechanism flaw), in the same family as ESACP#388 (saconsole-as-fleet-capability-record discipline). Fix lands in the repo; saconsole inherits via `git pull` next session (already aligned to `3336e4a` this session). No new saconsole capability declaration needed for the #390 fix — the env-var pass-through is a self-contained packer-script change.

## Post-close audit-fix

SESSION END audit (UserPromptSubmit hook re-run pattern per S45–S49) ran clean on **all four steps** — first zero-gap close in the S45-S49 precedent window. Discharge: pure clerical verdict-cell finalization (close-row commit-hash `1bdea66` + verdict cells `approve-with-conditions → approve | proceeded` + 2 QA invocation IDs `aaa62d26025e50a81 → a7663a54f0a7808d6`) + this minutes subsection + qa-log self-referential row appended.

1. **Forward-tense scan** — 3 hits, all benign and verified non-S50-commitments: (a) agenda line 25 Candidate A description ("should be harmonised" — describing S51 fix scope); (b) minutes line 77 ("will be destroyed/rebuilt again in the LSKB#20-resume session" — future state of disposable substrate); (c) minutes line 90 ("Fix lands in the repo; saconsole inherits via `git pull` next session" — explanatory analysis of how the S51 fix propagates, not a S50 commitment). No S50 work was deferred or unexecuted.

2. **GH issue references** — every issue with a S50-specific finding received a within-session comment: ESACP#353 ([`issuecomment-4452009096`](https://github.com/martinhbramwell/ESACP/issues/353#issuecomment-4452009096)), LSKB#6 ([`issuecomment-4452010889`](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/6#issuecomment-4452010889)), LSKB#20 ([`issuecomment-4452006631`](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/20#issuecomment-4452006631)). ESACP#390 filed with full root-cause + proposed fix + acceptance in the issue body. ESACP#388/#387/#341 + LSKB#15/#16/#18 + LSKB#9/#10 referenced only in passing carry-forward / agenda backlog text — no S50-specific finding requiring a comment per S48 precedent (comment when the immediate block changes; do not comment when only upstream chain depth changes — LSKB#15's immediate blocker LSKB#20 did not change state, only the chain upstream grew).

3. **PR mergedAt gate** — no PRs opened this session. N/A.

4. **Unresolved doubts** — four AskUserQuestion prompts all resolved within-session: candidate pick (Candidate A); LSKB#20 scope + saconsole repo state (strict + update); wizard mode (replay); path forward on bug discovery (Option 1 file + pause + close).

Zero-gap shape vs S45-S49 1-2-gap precedents reflects S50's explicit improvement on the pointer-comment discipline (all three parent-epic / blocked-issue comments posted within-session rather than surfaced at audit-fix time — averting the S48 close-batch-omission shape). The audit-fix commit's own qa-log row carries residual `_pending_` verdict cells per S48 `0bbd54e` finalization-row irreducible-self-reference convention.
