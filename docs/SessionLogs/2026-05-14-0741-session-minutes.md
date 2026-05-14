# 2026-05-14 0741 — Session 49 minutes

## Objective

**ESACP#388 — declare packer as a saconsole dependency.** Bucket-1 substantive infra fix. Unblocks LSKB#20 Path 1 → LSKB#15 → LSKB#16 (Plan-B Phase 4 critical path).

## Outcome — landed and closed

PR [#389](https://github.com/martinhbramwell/ESACP/pull/389) merged at `2026-05-14T11:40:59Z`; ESACP#388 auto-closed via `fixes` keyword at `2026-05-14T11:41:01Z`. Squash commit on `main`: [`e94e9a5`](https://github.com/martinhbramwell/ESACP/commit/e94e9a534085906acc1b96aad48dc89595800538).

## What landed

- **NEW** `ansible/roles/packer/defaults/main.yml` (14 lines) — declares `packer_min_version: "1.9.0"` (matches `erpnext-v13.pkr.hcl:14` `required_version`) + HashiCorp apt-repo constants.
- **NEW** `ansible/roles/packer/tasks/main.yml` (60 lines) — idempotent: ensure keyring dir, download HashiCorp GPG (`get_url force: no`), dearmor (`creates:` gate), add apt source (`{{ ansible_distribution_release }}`), `apt install packer`, capture version, assert `>= packer_min_version`.
- **MODIFIED** `ansible/site-kvm.yml` (+2 lines) — `{ role: packer, tags: [packer] }` in Play 2 (hub) between `mcp_grafana` and `acme_sh`.
- **MODIFIED** `platforms/packer/build.sh` (−8 lines net) — Phase 1 preflight: replaces the 9-line inline auto-install fallback (curl gpg | dearmor | echo deb | apt update | apt install) with a hard `die` pointing at the canonical ansible role. Docstring updated to match.

## Acceptance (live saconsole `you@10.10.0.1`)

| Check | Result |
|---|---|
| `ansible-playbook --syntax-check` | PASS (`playbook: site-kvm.yml`) |
| `--check --diff` against saconsole | Role structure correct; apt source for `noble` would be added |
| HashiCorp publishes packer for `noble` | Confirmed via apt repo `Packages` index |
| Real apply `--tags packer` | PLAY RECAP `ok=7 changed=4 failed=0` |
| `assert` task | `packer v1.15.3 >= 1.9.0` |
| Direct SSH verify | `/usr/bin/packer`, `Packer v1.15.3` |
| Idempotent re-run | `changed=0` |
| `build.sh` new preflight error path | Validated locally (controller lacks packer) |
| `bash -n build.sh` | OK |

## Audit (per #388 design-direction comment)

Survey of adjacent saconsole-side capabilities flagged in the comment:

| Capability | On saconsole | Declared via | Channel |
|---|---|---|---|
| `cloud-localds` | present | ✓ | `cloud-init/hub-autoinstall.user-data.j2:42` |
| `sops` | present | ✓ | `control_plane` role |
| `node`/`npm` | present (v20.20.2) | ✓ | `control_plane` role (`nodejs_version: 20`) |
| `gpg` | present | implicit | base Ubuntu (used by new packer role) |
| `age` CLI | absent | n/a | not used saconsole-side; sops handles age internally |
| `gh` CLI | absent | n/a | not used saconsole-side |

**No new #388-shape gaps to file.** First explicit instance of the "saconsole-as-fleet-capability-record" discipline (per S48 LSM memory `project_saconsole_as_fleet_capability_record.md`) shipped clean.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1+T3 (commit `ca70cc6` planned) | `a25f67929d71939a5` | approve-with-conditions | Condition 1: supply verbatim planned commit command (verifying conventional-commits format + `-S` flag + `fixes #388` + `Co-Authored-By` trailer + HEREDOC form). Condition 2: T2 cannot be pre-bundled with T1+T3 per §2.2. |
| T1+T3 (commit `ca70cc6` re-verify) | `ae4dfa12a5bce8455` | approve | Condition 1 discharged via re-invocation with verbatim `git commit -S -m "$(cat <<'EOF' … EOF)"`. Clean approve. Anti-rubber-stamp positive: role content, regex_search list-or-None gating, multi-line `die` backslash continuation, GPG `dearmor creates:` idempotency all spot-checked. |
| T2 (PR #389 squash-merge) | `a89ef14ee031ab233` | approve | §2.2 carve-out advisory; all three conditions hold (prior T1+T3 approve on `ca70cc6` + no post-verdict commits + squash strategy). Auto-close of #388 via `fixes` keyword confirmed firing on merge. |
| T1+T3 (this session-close commit) | _pending — irreducible self-referential row per S46/S47 precedent_ | _pending_ | ESACP doc-only direct-to-main per v2.1 §2.1 clause 3. Three files staged: minutes (this file), next-agenda (S50), qa-log (this row + 3 verdict rows above). |

## Counts at session end

- ESACP open: **37** (was 38; −#388 auto-closed).
- LSKB open: **9** (unchanged; #20 unblocked but not yet executed).
- ce_sri open: 5 (unchanged); LogiSoluValidations open: 2 (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged).
- **16th cross-repo `fixes`-keyword auto-close** in the running tally — first same-repo entry, but the tally has been mechanism-agnostic; counting #388 as #16. Direction same-repo on `martinhbramwell/ESACP`.

## TRIVIAL_FIXES.md status

Unchanged — 2 monitor-only entries (S33 LSM Trigger-3 skip pattern, S47 `tools/secrets.py` `+x` bit).

## Carry-forward operator-reminders (delta)

- **ESACP#388** — CLOSED. Removed.
- **LSKB#20** — Path 1 now executable; substrate-version-alignment substrate work can resume next session. Old-metadata-preservation pattern (rename `erpnext-v13-latest.json` to dated archive before build) still designed and ready.
- **LSKB#15, LSKB#16, LSKB#18, ESACP#387** — unchanged from S48 carry-forward.
- **`tools/secrets.py` +x bit (F4)** — unchanged.
- **dev02 substrate state** — unchanged from S47/S48; disposable.
- **LogiSoluMemory Trigger 3 skip pattern** — monitor-only.
- **ce_sri local clone in-progress state** — unchanged.
- **Tablet WG sidebar (#383)** — still ripe.
- **Saconsole fleet-capability discipline (S48 LSM memory)** — first concrete instance landed; pattern proven. Future similar gaps file the same shape.

## Memory updates

None this session. The S48 LSM memory `project_saconsole_as_fleet_capability_record.md` was load-bearing for the framing here and is unchanged by this fix landing.

## Shape note

Substantive bucket-1 substrate-config fix with single-PR landing. Minutes ~75 lines as drafted — tracks the S40–S48 73–95 line baseline. The audit table compresses what would otherwise be a 6-paragraph survey into one row per capability; QA-verdicts table compresses three invocations into the standard form. One issue closed, no new issues filed.
