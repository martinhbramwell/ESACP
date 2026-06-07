# 2026-06-07 0748 — Session 108 minutes

## Objective (operator-pinned)

**#480 — re-target the V13→V16 umbrella to V13→V15 and re-validate the defect catalog against the
live `dev15_01` V15 baseline.** Deliverable: a written v15 defect-catalog delta on the #480
umbrella + the umbrella re-targeted. **Achieved**, plus a mid-session architectural decision
captured (OS-per-major, ESACP#643).

## Class

Analysis + tracker + planning session under the #480 umbrella. No substantive ESACP code change —
the deliverables landed on GitHub (#480 retarget + delta), an external plan file, and the
LogiSoluMemory repo. The ESACP branch (`feat/480-v15-catalog-delta`) carries only these session
logs. **Not** an introspection-sidebar (no MEMORY.md indexing edits; no carry-forward attrition of
the mechanical kind). One new issue filed mid-session (#643, deferred to its own 1:1:1).

## What happened

### Pre-flight
sync_check 48✅/10⚠️/2❌ — both ❌ are dev02 (parked V16 box, expected-down per agenda). Issues
ESACP 83 / LSKB 13 (matched agenda's ~85/13). TRIVIAL_FIXES: 1 monitor-only entry (S33), no action.
Branch `feat/480-v15-catalog-delta` cut from `main`. Memory-grep done (reference_erpnext_v16_desk_ui,
project_v16_migration_triage_criterion, beaverdam-mcp-first-sequencing, end-state memory).

### Method — read the live v15 source, not archaeology
dev15_01 reached over WireGuard (`erpadm@10.10.0.18`, key hasan_mighty; not yet in ssh_config).
All catalog classifications are **mechanism-level, read from live frappe/erpnext 15.110.0 source** on
the box. The baseline is generic (no prod data), so data-level *reproduction* of each defect is
deferred to the migration-with-data step; which **step** each defect lives on was settled by source.

### v15 defect-catalog delta (posted on #480)
| Row | v15 source finding | Step | vs. prior |
|---|---|---|---|
| **R1** Homepage salvage | `erpnext/portal/doctype/homepage` **alive** on v15 (issingle) | **V15→V16** | 🔄 FLIP (was V13→V15) |
| **#626** server_script_enabled | v15 `is_safe_exec_enabled()` reads `get_common_site_config()` **only** — same as v16 | **V13→V15** | 🔄 REFUTES "per-site on v15" |
| **#618** atajos masking | v15 sidebar does `pages.extend(private_pages)` — private workspaces **surfaced** | **V15→V16** | ✅ confirms |
| **leaderboard** | Page **present** on v15 (`frappe/desk/page/leaderboard` + `erpnext/startup/leaderboard.py`) | **V15→V16** | ✅ confirms |
| **#617** Naming Series | `Naming Series` DocType **gone** on v15 → `Document Naming Settings`/`Rule` (v14+ rename already in v15) | **V13→V15** (probe both) | ✅ confirms |
| **R3** IRS-1099 | tenant-data orphan, version-agnostic fix | **V13→V15** | clarified |
| **R5/R6** nginx | ESACP-template, version-independent | provision-time | clarified |
| **R2** /tasks | stock v14+, accepted won't-fix | n/a | unchanged |

Two prior assumptions overturned by source: **R1 is a v16 defect (Homepage alive on v15)**, and
**#626's common-only gate is identical on v15 (fix still needed)**. Incidental: `v16_post_migrate_fixups.py`
already contains both R1 and R3 (#486's "R1 pending" comment is stale).

### #480 umbrella re-targeted
Retitled "V13→**V16**" ⇒ "**V13→V15 baseline + V15→V16 tracked**". Delta posted as a comment.
Step-assignments posted on children #617 (V13→V15) / #626 (V13→V15) / #618 (V15→V16). Tier-B
#456/#457 untouched; R2 won't-fix unchanged. Used comments, not new label machinery (operator
didn't request a label scheme).

### Mid-session decision — OS-per-major (ESACP#643, NEW)
Operator: each major inhabits its era-matched Ubuntu LTS with latest-valid deps — **dev13→22.04 /
3.10** (v13 deps genuinely pinned), **dev15→24.04 / 3.12**, **dev16→26.04 / 3.12+**. Source-verified
clean for v15: frappe v15.110 `requires-python = ">=3.10,<3.15"` → 24.04's Python 3.12 fully
supported; the Python-3.12+ wall is v16-only (PEP-695). Consequence: the current dev15_01 (22.04) is
a **demonstrator** on the wrong OS; the OS-correct v15 baseline rebuilds when `template_v15`@24.04
lands (the Packer build is already frappe-major-parameterized — adds an OS build-arg). Operator: **no
dev15_01 rebuild yet**; finish the planned catalog work. Filed #643 (deferred, own 1:1:1); updated
plan §4 + the end-state memory (the "v15 runs on 22.04/3.10" framing was floor-not-ceiling).

## Outcomes
- **#480** re-targeted V13→V15 + V15→V16; v15 catalog delta written on the umbrella. (Stays OPEN —
  the dual-script build is the deferred next increment.)
- **#643 OPEN (NEW)** — OS-per-major template matrix; deferred to its own 1:1:1.
- **#617 / #626 / #618** step-classified on v15 (V13→V15 / V13→V15 / V15→V16).
- Catalog delta is OS-independent → stands against the future 24.04 v15.
- Plan §4 + end-state memory updated to OS-per-major.

## esacp-qa ledger
(to be appended at pre-commit/pre-merge below)
