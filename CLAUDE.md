# ESACP — Claude Code Project Context

**Mission**: Self-repairing, AI-assisted platform so a family-owned business can maintain and enhance their heavily customised ERPNext system without depending on any single developer. See `memory/mission_vision.md` for full context.

---

## Session Protocol

At the start of every session, before doing anything else:

1. **Identify the platform** — which controller machine are you on?
2. **Run the sync check**: `bash platforms/kvm/sync_check.sh`
3. **Fix any failures**, commit and push repairs.
4. **State one objective** for the session. Do not pursue other issues — note them and handle in a dedicated session.

**One objective per session.** Hard rule.

**1:1:1 discipline (substantive changes)** — 1 issue = 1 branch = 1 session, for substantive project software: pipeline code, dispatchers, SUT scripts, Ansible plays/roles, SOPS-backed config with runtime effect, pipeline unit tests. Branch from main, PR to merge, clean working tree always. No accumulating uncommitted changes on main.

**Housekeeping bundles (exception)** — a single branch/session MAY close multiple issues when all are housekeeping: documentation scrubs (CLAUDE.md, RUNBOOK, agendas, minutes), wording/terminology fixes, external Claude Code config (`~/.claude/*`), `.gitignore`/pre-commit hygiene, issue grooming. Guardrails: each issue still filed individually; PR titled as a sweep (`chore(housekeeping): …` or `docs(sweep): …`); PR body lists `fixes #A, #B, #C`; no mixing (any substantive code change pulls the bundle back to 1:1:1); per-file size-check ratchet still applies.

**Umbrella branches (multi-session refactors / broad-context work)** — for efforts where unit-level PRs can each pass their own narrow acceptance while still leaving a broad-context integration bug on `main`, use a long-lived umbrella branch off main. Each 1:1:1 unit is a sub-branch of the umbrella; sub-branches merge into the umbrella, not main. The umbrella merges to main only in a deliberate **certification session** (all scoped issues resolved, broad-context acceptance green, `sync_check` green against umbrella tip, explicit user sign-off).

- **When to use** — any of: >3 sub-branches expected; cross-cutting files touched by multiple issues; a broad-context acceptance exists that cannot run per-sub-branch (matrix runs, full-pipeline e2e); or explicit user call at planning time. Otherwise direct-to-main per 1:1:1 or housekeeping rules. Single-issue hotfixes and doc-only PRs always direct to main.
- **Naming** — `umbrella/<short-topic>` (e.g. `umbrella/v16-upgrade`, `umbrella/matrix-run-08`). Single prefix so `git branch --list 'umbrella/*'` enumerates live umbrellas.
- **Rebase cadence** — on demand, not scheduled: before cutting a new sub-branch off umbrella; when a direct-to-main PR touches files also touched on umbrella; before the certification session. No fixed cron.
- **"Merged" semantics** — per `feedback_pr_merge_before_session_close.md`, "merged" means merged-to-target-branch. A sub-branch's target is its umbrella; the umbrella's target is main. Both must reach non-null `mergedAt` before the respective "done" claims.
- **Retroactive application** — none. Rule applies only to multi-session work **started after** this policy lands. Prior matrix/Gen 3 work stays as-landed.
- **CI / sync_check** — no branch-topology awareness in `sync_check` for this phase; revisit only if merges are later gated on umbrella-tip state.

**Bug workflow** — whenever a bug is found:
1. Open a GitHub issue immediately (`gh issue create --repo martinhbramwell/ESACP`)
2. Fix the code, committing with `fixes #N`
3. Close the issue with the commit hash

Do this at the moment of discovery — not at session end.

**Issues review** — at the start of bug-fixing/infrastructure sessions: `gh issue list --repo martinhbramwell/ESACP --state open` and close any already-resolved issues.

---

## Current State

| Stage | Status | Description |
|---|---|---|
| Stage 1 / 1.5 | ✅ Complete | VBox/WSL — **permanently retired**, hardware failure 2026-03-17 |
| Stage 2.1 | ✅ Complete | KVM path, WireGuard mesh, observability 27/27 validated |
| Stage 2.2 | ✅ Complete | toshiba hypervisor: saconsole + targets, all MCP servers live |
| Stage 2.2 rebuild | ⚠️ Partial | Hub rebuild proven; Phase 3 (targets) misaligned with pipeline (#185) |
| Stage 2.3 | 🔧 In progress | Cytoscape 4-quadrant control plane + FastAPI backend |
| Stage 2.x | 🔜 Next | CloudStack backend, chaos on KVM, version watchdog |

---

## Architecture

| # | Controller OS | Hypervisor / VPS | Status |
|---|---|---|---|
| 1 | Windows 11 + WSL2 | Hyper-V (replaces VBox) | ⏸ On hold — no hardware |
| 2 | Xubuntu (Mighty) | KVM/libvirt — remote (toshiba) | 🔧 Active |
| 3 | Ubuntu Server | External VPS (iwStack/CloudStack) | 🔜 Planned |
| 4 | macOS | External VPS (iwStack/CloudStack) | 🔜 Planned |

Controllers are bootstrap-only. saconsole manages all sibling VMs after handoff.

**VBox is permanently retired** — do not add VBox-specific code. Scripts in `platforms/vbox/` are reference only.

---

## Key Files

```
hosts_map.yml              # Authoritative host directory — single source of truth
tools/host_identity.py     # Python constants resolved from hosts_map.yml (HUB_KEY, ZONE_DOMAINS, DEFAULT_HYPERVISOR, etc.)
tools/secrets.py           # Build secrets from env vars or config/build_secrets.sops.yml
tools/generate_inventory.py # Derives ansible/inventory/kvm.yml
config/wireguard/          # SOPS/age-encrypted WireGuard keys
config/build_secrets.sops.yml # SOPS-encrypted build passwords (erp_user_pwd, db_root_pwd)
platforms/kvm/             # Bootstrap + differentiation scripts + cloud-init templates
ansible/                   # site-kvm.yml (5 plays), roles, group_vars
docker/observability/      # Compose stack: Prometheus, Grafana, Loki, Alertmanager, etc.
prototypes/cytoscape/      # Cytoscape.js + Vite control plane prototype
tools/api.py               # FastAPI backend (port 8088)
tools/esacp.py             # Unified lab CLI
docs/                      # DiagramDesign.md, FailoverDesign.md, RUNBOOK.md
```

**Domain-specific detail in subdirectory CLAUDE.md files:**
- `platforms/kvm/CLAUDE.md` — toshiba, bootstrap, ERPNext differentiation, WireGuard/iptables/SSH
- `ansible/CLAUDE.md` — plays, roles, MCP configs, MariaDB/nginx_ui/mcp_grafana gotchas
- `docker/observability/CLAUDE.md` — stack ports, Prometheus template, Grafana/Promtail/cAdvisor gotchas
- `prototypes/cytoscape/CLAUDE.md` — zone frames, viewport, selectors, Inspect/Refresh/Destroy
- `tools/CLAUDE.md` — api.py endpoints, esacp.py CLI, generate_inventory.py

---

## Commit Conventions

All commits must:
1. **Conventional Commits** format: `<type>[optional scope]: <description>`
2. **GPG-signed** (`git commit -S`)
3. **Co-author trailer**: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`
4. **Update relevant CLAUDE.md** if the commit changes architecture, key files, stage status, or gotchas

| Type | When |
|---|---|
| `feat` | New capability |
| `fix` | Bug or misconfiguration fix |
| `docs` | CLAUDE.md, RUNBOOK.md, SETUP_GUIDE.md |
| `refactor` | Code restructure, no behaviour change |
| `chore` | Deps, generated files, housekeeping |
| `ci` | Ansible playbook changes, provisioner scripts |

Common scopes: `kvm`, `vbox`, `observability`, `wireguard`, `ansible`, `claude`, `chaos`

---

## Banned Patterns — `sed` and heredocs-as-code

**No `sed`** in any script generated or maintained by this project. Every text transformation must be a Python function (`str.replace()`, `re.sub()`, or a proper parser). `sed` introduces escaping fragility that compounds across SSH, f-string, and heredoc layers.

**No heredocs feeding code** to interpreters (`bench console`, `python`, `mysql`, etc.) through shell layers. Instead:
- Write a standalone `.py` (or `.sql`) file
- Deploy it to the target (SCP, Jinja2 render, or embed in the repo)
- Run it directly: `sudo -u $ERP_USER $BENCH_DIR/env/bin/python /tmp/script.py`

**Why**: Heredocs carrying code through `bash -c "..."` inside Python f-strings create three interacting escaping layers (Python string → shell double-quotes → heredoc body). This is the root cause of #93 and has burned multiple sessions. A standalone file has zero escaping layers.

**Heredocs feeding short data** (a password, a filename) to stdin are acceptable when no code is involved.

**Existing violations**: None — G-pre, H4e, and H4a have all been migrated to standalone Python scripts in `tools/vm_scripts/`.

## Invoke scripts as executables

Every script under `tools/` has `#!/usr/bin/env python3` and is `chmod +x`.
Run them directly:

- ✓ `./tools/esacp.py confirmPrerequisites`
- ✗ `python tools/esacp.py …` (no `python` on PATH)
- ✗ `python3 tools/esacp.py …` (bypasses the shebang contract)

Covers `esacp.py`, `generate_inventory.py`, `host_identity.py`, pipeline
scripts, and every other shebanged Python file. Rationale + recurrence
history: `feedback_invoke_as_executable.md` in project memory (#188).

## Function and script size limits

Any function or standalone script over **50 lines** needs decomposition. This is a gradient, not a cliff:

| Lines | Signal |
|---|---|
| ≤ 50 | Fine |
| 51–70 | Look for a split point |
| 71–100 | Must split before committing |
| 101+ | Reject — decompose into focused units |

`differentiate.sh` (297 lines) is a known violation — it is a pipeline of labelled sections (A, B, C…) that should each be an independent script called from a thin orchestrator. Refactor as sections are next touched.

---

## Architecture Rules — Anti-Spiral Enforcement

These rules prevent the recurring death spiral: fix → patch monolith → monolith grows → refactor → repeat. They are mechanically enforceable. See issues #189–#198 for the Gen 3 pipeline completion plan.

### Where business logic lives

**Business logic lives ONLY in `tools/pipeline/`.** All infrastructure operations (SSH, virsh, subprocess, config mutation, multi-step workflows) must live under `tools/pipeline/`. Specifically:
- Unit functions: `tools/pipeline/stages/*/` — IoC: takes `(Config, Emit) -> TaskResult`
- Stage orchestrators: `tools/pipeline/stages/stage_N_*/` — `__init__.py` composes units
- Macros: `tools/pipeline/macro/` — composes stages
- Orchestration helpers: `tools/pipeline/orchestration/` — non-stage operations (host registration, VM build, destroy)

**Forbidden locations for business logic**: `tools/esacp.py`, `tools/api.py`, `tools/job_worker.py`, `tools/cli/*.py`. These are dispatchers only.

### Dispatcher rules

A dispatcher may ONLY:
1. Parse input (argparse, Pydantic, JSON)
2. Call ONE pipeline primitive or macro
3. Format output for its transport (Rich console, JSON response, log line)
4. Handle transport-specific concerns (HTTP status codes, exit codes, job spawning)

If a dispatcher needs an `if` about VM state, WireGuard config, or any infrastructure concept, that logic belongs in a primitive.

### New operations

1. Write the primitive in `tools/pipeline/` first, with IoC signature
2. Write a colocated test for it
3. Add the thin dispatcher entry that calls the primitive
4. Never write logic in a dispatcher "temporarily"

### No duplication across transports

CLI + API + job_worker calling the same operation MUST call the SAME primitive. They differ only in input parsing, output formatting, and error handling.

### `emit` is the only output mechanism

Pipeline primitives use `emit: Emit` exclusively. Never import Rich, FastAPI, or print in pipeline code.

### Dispatcher file size hard limits

| File | Max lines | Action if exceeded |
|---|---|---|
| `tools/esacp.py` | 150 | Split into `tools/cli/` per-command files |
| `tools/api.py` | 300 | Extract endpoint groups into route modules |
| `tools/job_worker.py` | 100 | Logic has leaked — extract to macro |
| Any `tools/cli/*.py` | 80 | Logic has leaked — extract to primitive |
| Any `tools/pipeline/**/*.py` | 80 | Decompose into smaller units |

A pre-commit hook enforces these limits mechanically (see #198).

### No subprocess calls in dispatchers

Any code calling `subprocess.run` with SSH, virsh, ansible-playbook, sops, or any infrastructure tool MUST live in `tools/pipeline/`. The only exception: `api.py` spawning `job_worker.py`.

### Dead code deletion is mandatory

When a primitive is extracted from a monolith, the monolith code it replaces MUST be deleted in the same PR. No commented-out code. No flags. The primitive is the single source of truth.

### Known violations (being resolved by #189–#197)

| File | Current lines | Target | Tracking issue |
|---|---|---|---|
| `tools/esacp.py` | 1677 | ≤150 | #189, #191, #192, #194, #195 |
| `tools/api.py` | 999 | ≤300 | #190, #193, #195 |
| `tools/job_worker.py` | 400 | ≤100 | #192, #193 |
| `tools/install_specific.py` | 721 | ≤50 | #197 |

### QA Verdict Contract (#341)

Pre-commit / pre-merge / pre-push / pre-destroy / pre-issue-close verdict layer. The parent agent must invoke `Agent(subagent_type: "esacp-qa", …)` before any trigger op and act on the verdict. Full contract: [`docs/qa-contract.md`](docs/qa-contract.md). Agent definition: [`.claude/agents/esacp-qa.md`](.claude/agents/esacp-qa.md). Verdict log: [`docs/qa-log.md`](docs/qa-log.md).

---

## Global Conduct Rules (enforced — see `~/.claude/CLAUDE.md`)

Confirm before acting · Root cause over symptoms · GitHub Issues as institutional memory · No real names in docs · No masking of errors · No modification of third-party code
