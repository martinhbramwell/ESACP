# Pointers — where to find ESACP's existing technical surface

This is your map into the repo. It tells you what exists, what each
file is for, and — crucially — which parts of the repo are **universal**
(safe to inherit on this zero-knowledge branch) vs. **tenant-specific**
(institutional history of the current operating tenant; not your
onboarding-author concern).

You do not need to read everything before starting. You need to know
where to look.

## Root-level orientation

| File | What it is | Universal or tenant-specific |
|---|---|---|
| `CLAUDE.md` (root) | Project context for any Claude Code session on ESACP. Has the Session Protocol, commit conventions, banned patterns, architecture rules, QA verdict contract, and global conduct rules. | **Mixed** — see section table below |
| `internal_docs/RUNBOOK.md` | Operator runbook for hypervisor + target VM operations. | Mostly universal; some examples use real hostnames |
| `internal_docs/qa-contract.md` | The QA verdict layer contract (T1–T5 triggers, verdict shape, fail-safe). Required reading for any Claude that commits, merges, pushes, performs destructive ops, or closes issues. | Universal |
| `.claude/agents/esacp-qa.md` | The QA agent definition that implements the contract. | Universal |
| `internal_docs/qa-log.md` | Running log of every QA verdict the project has produced. Read as historical context, not as a rulebook. | Tenant-specific (institutional memory) |
| `internal_docs/DiagramDesign.md`, `FailoverDesign.md` | Architecture references for the Cytoscape control plane and failover posture. | Universal |
| `hosts_map.yml` | The authoritative host directory for the current fleet. | **Tenant-specific contents, universal format** — the *file's role* is universal; its current entries are tenant-side |

### Root `CLAUDE.md` — section-by-section

| Section | Universal? | Why |
|---|---|---|
| Mission (top line) | Universal | Describes the project's purpose in tenant-agnostic terms |
| Session Protocol | **Universal — required reading** | One objective per session, 1:1:1 discipline, housekeeping bundles, umbrella branches, bug workflow |
| Three-Bucket Architecture & Bespoke App Repos | Tenant-specific | Institutional history of the current tenant's repo layout; not your concern as an onboarding author |
| Current State (stage table) | Tenant-specific | Stage progress for the current tenant's fleet |
| Architecture (controller/hypervisor table) | Tenant-specific | Specific to the current operator's hardware history |
| Key Files | **Universal — required reading** | The actual file map of the project |
| Commit Conventions | **Universal — required reading** | Conventional Commits + GPG signing + co-author trailer |
| Banned Patterns | **Universal — required reading** | No `sed`, no heredocs-as-code, no `python tools/x.py` |
| Invoke scripts as executables | **Universal — required reading** | `./tools/x.py` not `python tools/x.py` |
| Function and script size limits | **Universal — required reading** | ≤50 lines preferred, 101+ is a reject |
| Architecture Rules — Anti-Spiral Enforcement | **Universal — required reading** | Where business logic lives, dispatcher rules, no subprocess in dispatchers, dead-code deletion |
| QA Verdict Contract | **Universal — required reading** | Refers to `internal_docs/qa-contract.md` |
| Global Conduct Rules | **Universal — required reading** | Already inlined into `on_boarding/AI_GUARDRAILS.md` so you can read it without leaving the kit |

## Subdirectory `CLAUDE.md` files

Each of these adds domain-specific gotchas. Read the one that matches
the surface you are touching:

| Path | Domain |
|---|---|
| `platforms/kvm/CLAUDE.md` | KVM/libvirt hypervisor, bootstrap, ERPNext differentiation, WireGuard/iptables/SSH |
| `ansible/CLAUDE.md` | Ansible plays/roles, MCP server configurations, MariaDB/nginx/Grafana gotchas |
| `docker/observability/CLAUDE.md` | Prometheus/Grafana/Loki/Alertmanager stack ports and gotchas |
| `prototypes/cytoscape/CLAUDE.md` | Cytoscape.js control plane: zone frames, viewport, selectors, Inspect/Refresh/Destroy |
| `tools/CLAUDE.md` | `api.py` endpoints, `esacp.py` CLI, `generate_inventory.py` |

All of these contain real hostnames in examples; the *patterns and
rules* are universal, the *example data* is tenant-side.

## The pipeline — where business logic lives

`tools/pipeline/` is the only place infrastructure operations are
allowed to live. Specifically:

- `tools/pipeline/stages/sNN_<name>/` — Stage-N unit functions
  (`(Config, Emit) -> TaskResult`)
- `tools/pipeline/stages/stage_N_*/__init__.py` — stage orchestrators
- `tools/pipeline/macro/` — multi-stage macros
- `tools/pipeline/orchestration/` — non-stage operations (host
  registration, VM build, destroy)

Dispatchers (`tools/esacp.py`, `tools/api.py`, `tools/job_worker.py`,
`tools/cli/*.py`) only parse input, call one pipeline primitive, and
format output. They are NOT allowed to contain business logic.

If your onboarding material needs to invoke an infrastructure
operation, invoke a primitive. Do not write new logic in a dispatcher.
If the primitive does not exist, that is an upstream platform gap —
file an issue, do not patch around it from the branch.

## Tools you will use

| Tool | What it does |
|---|---|
| `./tools/esacp.py` | The unified lab CLI. Always invoked as the executable, not via `python`. |
| `./tools/host_identity.py` | Python constants resolved from `hosts_map.yml`. |
| `./tools/generate_inventory.py` | Derives Ansible inventory from `hosts_map.yml`. |
| `./tools/secrets.py` | Build secrets from env or SOPS-encrypted file. |
| `gh` (GitHub CLI) | Issue filing, PR creation, PR status checks. Auth is operator-side. |
| `sops` + `age` | Secret encryption. Operator must have an age key. |
| `gpg` | Required for commit signing (see `CLAUDE.md` Commit Conventions). |

## Things that look like documentation but are not

These exist on the repo and you will encounter them — they are **not**
orientation for you, and you should not let your onboarding material
depend on them:

- `internal_docs/SessionLogs/` — agendas + minutes from the current
  tenant's operating sessions. Historical record. Tenant-specific.
- `internal_docs/AuditReports/` — audit outputs from the current
  tenant's operating sessions. Tenant-specific.
- `memory/` (under `~/.claude/projects/.../memory/` on the current
  operator's controller) — Claude's private memory dir. Symlinked
  from a private repo. **NOT** available to you, **NOT** available
  to end-users, **MUST NOT** be referenced as a dependency by any
  onboarding material you produce.

## What's available to you, what isn't

| Available | Not available |
|---|---|
| Anything checked into the repo on the `on_boarding` branch | The current operator's `memory/` directory |
| `CLAUDE.md` (universal sections), subdirectory `CLAUDE.md` files | Private tenant repositories (memory, business-logic, validation suites) |
| `internal_docs/qa-contract.md`, `.claude/agents/esacp-qa.md` | Tenant-specific issue trackers beyond `martinhbramwell/ESACP` |
| `internal_docs/RUNBOOK.md`, design docs | The current operator's `~/.claude/CLAUDE.md` |
| `tools/pipeline/`, `tools/cli/`, `tools/api.py` source | Production ERPNext (read-only at most; not for onboarding examples) |
| Public ERPNext / Frappe documentation | Anything outside this branch on someone else's authority |

When in doubt, ask the operator. Do not invent.
