# Session Minutes — 2026-04-19 13:38

**Objective (entering):** Execute Matrix Run 02 proper end-to-end via the CLI path — `addHost dev01` → `provision dev01` with full restore from the golden production backup, driven by a Playwright spec that also asserts Cytoscape topology convergence.

**Status:** **SHELVED.** Matrix Run 02 does not start. Session pivoted after a conduct-rule violation surfaced: the real client name is embedded in **124 occurrences across 51 files**. Scope and nuance too large for tail-end execution. Issue **#239** filed. Matrix Run 02 and downstream runs 03–07 wait on #239 closure.

Branch `fix/conduct-scrub-client-name` holds all scrub-related work (this minutes file, the next agenda, and all future scrub commits).

---

## Pre-flight (completed before halt)

### Precondition gates — all passed per the prior agenda
- `sync_check.sh` — 43 ✅ / 8 ⚠️ / 3 ❌; the 3 failures are the expected dev02/dev03/target5 ping rows (those VMs unprovisioned).
- `main` HEAD `a370851` — post-`eff7078` (PR #237 merged).
- `saconsole` running on toshiba; no `dev01` entry.
- Cytoscape API 200, Vite 200.
- Golden production backup present at its canonical path. User confirmed the current pointer (third `.tgz` dated 2026-04-19 07:28 in `BACKUP.txt`).
- `./tools/esacp.py --help` shows `addHost`.
- No in-flight PRs on `accept/02-cli-full-*`; no in-flight jobs.

### D1 / D2 decisions
- **D1 = (a)** — param file drives the Playwright harness (spec reads YAML, passes fields to CLI), not a new `--params` flag on `provision`. Keeps dispatcher dumb.
- **D2 = (a)** — the run calls `addHost` itself as step 2 (fresh state, full CLI lifecycle), rather than pre-registering dev01.

### Provision-CLI discovery
- `./tools/esacp.py provision <vm>` takes only positional `<vm>` — no mode flag. `Config.provision_mode` defaults to `"restored"` (`tools/pipeline/stages/common/config.py:50`).
- Stage 3 (`tools/pipeline/stages/stage_3_connectivity/backup.py:10`) hardcodes the backup source directory; stage 7 restores from whatever `BACKUP.txt` names on-VM.
- Net: `./tools/esacp.py provision dev01` is exactly the full-restore path needed for Run 02. No CLI changes required.
- `addHost --vm-role` accepts any string (no canonical-set validation). The planned `dev:full_<real>` value would have been accepted but is a new form.

---

## Conduct-rule violation — discovered mid-authoring

Sanity check before writing the Playwright spec filename surfaced the issue: the spec and param filenames themselves would embed the real client name. Verified against global rule (`~/.claude/CLAUDE.md` — *"No real names in docs or conversation"*).

### Scope
`grep -ri '<real-name>'` → **124 occurrences across 51 files**.

| Category | Files | Notes |
|---|---|---|
| Live SUT code | 14 | `hosts_map.yml`, cytoscape `{main,api}.js`, `topology-ops.spec.js`, `tools/pipeline/{macro,stages/stage_3_connectivity}/*.py`, `platforms/kvm/{prepare_hypervisor.sh,session_start.py,fallback/*.sh}`, two CLAUDE.md files |
| Going-forward docs | 8 | `internal_docs/SessionLogs/acceptance-matrix/{02,03,05,06,07}-*.md` (02 & 05 also have it in the filename), `internal_docs/ERPNextRestoreRunbook.md`, `internal_docs/PrepareHypervisor.md`, this agenda's parent (`2026-04-19-1242-next-agenda.md`) |
| Historical session logs | ~30 | Pre-2026-04-19 minutes/agendas. User ruled (iii): separate commit, name-replacement only, zero semantic changes |
| Memory | N/A | Outside repo. Scrubbed in parallel during execute session |

### Issue filed
**#239** — `fix(conduct): scrub real client name from repo — 124 occurrences across 51 files`. Three-commit plan on branch `fix/conduct-scrub-client-name`:
1. Live SUT code scrub
2. Going-forward docs scrub + filename renames (`git mv`)
3. Historical log scrub (labelled as such)

Replacement term: `company_specific` (snake_case, code/data) / `company-specific` (kebab-case, filenames/markdown).

### Feedback memory captured
`feedback_no_real_client_names.md` saved outside the repo. MEMORY.md `## Critical Rules` now includes a pointer referencing #239.

---

## SUT-scrub decomposition — P1 through P5

Enumerating the 20 SUT occurrences revealed they split into five non-uniform categories. Blind replacement is unsafe; the categories need per-category design decisions before a single `Edit` runs. **This is why the session halts and plans next.**

### P1 — production domain value (`<real>.solutions`) — 4 occurrences
- `hosts_map.yml:18` (authoritative)
- `prototypes/cytoscape/src/main.js:1653` — `ZONE_DOMAINS` duplicates hosts_map (hardcoded-values-audit-class)
- `prototypes/cytoscape/src/api.js:50` (comment)
- `platforms/kvm/CLAUDE.md:45` (documentation)

**Constraint:** real running DNS zone. Blind replacement breaks production routing. Options sketched:
- (P1a) `hosts_map.yml.template` + gitignored local overlay.
- (P1b) Placeholder + ship-broken-by-default; require local reconfiguration.
- (P1c) Extract only the `production:` value to SOPS / gitignored.

### P2 — filesystem paths (`~/projects/<real>/...`) — 8 occurrences
- `platforms/kvm/prepare_hypervisor.sh:210`
- `platforms/kvm/session_start.py:17` (CC session dir path — filesystem-derived from the out-of-repo dir)
- `platforms/kvm/session_start.py:18`
- `platforms/kvm/fallback/toshy-fallback-install.sh:9,71,76`
- `tools/pipeline/stages/stage_3_connectivity/backup.py:10`
- `tools/pipeline/stages/stage_3_connectivity/cesri_secrets.py:16,19`
- `tools/pipeline/stages/stage_3_connectivity/ddl_views.py:11`

**Constraint:** paths point outside the repo. Options sketched:
- (P2a) Introduce `ESACP_WORKSPACE_ROOT` env var + user filesystem rename.
- (P2b) Env var with default still pointing at real directory; rename deferred.
- (P2c) Defer entirely; carry-forward documented in #239.

### P3 — virsh snapshot label — 1 occurrence
- `tools/pipeline/macro/provision.py:74` — `snap_name = "ERPNext v13 <real> DB Restored"`

**Constraint:** existing VMs carry baseline snapshots with the old label in libvirt metadata. Any code that string-matches this label (idempotency gates?) needs auditing before the change.

### P4 — labels / comments / docstrings — 5 occurrences (safe)
- `tools/pipeline/macro/provision_generic.py:33` (docstring)
- `prototypes/cytoscape/src/main.js:91` (UI template tile label)
- `prototypes/cytoscape/src/main.js:1853` (comment)
- `prototypes/cytoscape/tests/topology-ops.spec.js:48` (test error message)
- `prototypes/cytoscape/CLAUDE.md:104` (doc)
- `platforms/kvm/CLAUDE.md:45` (doc — partial, shared with P1)

**Constraint:** none runtime-critical. Pure `Edit` operations.

### P5 — logo filename — 1 occurrence (+ tracked binary file)
- `tools/pipeline/stages/stage_3_connectivity/cesri_secrets.py:18` — `CE_SRI_LOGO = ... "<real>Logo.png"`
- `config/branding/<real>Logo.png` — tracked binary. Confirmed present.

**Constraint:** `git mv` the asset + update the code. Must audit any other references to the filename (ansible? VM-side scripts? external tooling?).

---

## Artefacts created in this session

| Artefact | Location | Notes |
|---|---|---|
| Branch `fix/conduct-scrub-client-name` | local, off `a370851` | Zero code commits yet. Carries these minutes + the next agenda. All future scrub work lands here. |
| Issue #239 | github.com/martinhbramwell/ESACP/issues/239 | OPEN. Three-commit plan + P1–P5 breakdown. |
| `feedback_no_real_client_names.md` | memory (outside repo) | Rule + why + how-to-apply. Placeholder syntax only. |
| MEMORY.md update | memory | Added pointer under `## Critical Rules`. |
| This minutes file | `internal_docs/SessionLogs/2026-04-19-1338-session-minutes.md` | Placeholder syntax. On scrub branch only. |
| Next agenda | `internal_docs/SessionLogs/2026-04-19-1338-next-agenda.md` | Planning session for #239. On scrub branch only. |

---

## Matrix Run 02 — knowledge to carry forward

When the scrub is done and the matrix resumes, resume Run 02 with:

### Decisions already made
- D1 = (a); D2 = (a).
- Backup path: `~/projects/<real>/ce_sri/BKP/` (pipeline-hardcoded in stage 3 — note that this IS the P2 scope).
- CLI is single-mode: `./tools/esacp.py provision <vm>` defaults to `provision_mode="restored"`. No CLI flag change needed.
- `addHost --vm-role` accepts any string; the `vm_role` value is metadata only, not a pipeline-gate.

### Open questions (re-raise when Run 02 resumes)
- `wait_budget_seconds` — Run 02 agenda-template says 1800. My read: 3600 more realistic for a full ERPNext restore. No empirical timing yet.
- Canary record assertion (for Run 05 UI parity) — specific doctype+name not chosen. Needs to be a record present in the golden backup and stable across restores.

### Filename implications
After #239 closes, these files will have been renamed:
- `internal_docs/SessionLogs/acceptance-matrix/02-cli-vm-full-<real>-from-backup.md` → `02-cli-vm-full-company-specific-from-backup.md`
- `internal_docs/SessionLogs/acceptance-matrix/05-ui-vm-full-<real>-from-backup.md` → `05-ui-vm-full-company-specific-from-backup.md`
- The future param file and Playwright spec for Run 02 will use the `company-specific` form from the outset.

### Task-list hygiene
Tasks #8–#14 from this session are moot now. Execution session will re-author its own task list against the plan that comes out of the next planning session.

---

## Session close

Next session: **plan** #239 P1–P5 end-to-end, no code edits. See `2026-04-19-1338-next-agenda.md`.

Session after: execute the plan.

User note: **`git checkout fix/conduct-scrub-client-name` before starting the next session** — the agenda and plan-output live on this branch, not on `main`, per the user's "all scrub work on a fresh branch" ruling.
