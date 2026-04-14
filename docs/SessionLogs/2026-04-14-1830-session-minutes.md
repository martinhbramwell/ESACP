# Session Minutes — 2026-04-14 1830 UTC

**Objective:** Plan #171 — eliminate hardcoded "saconsole" VM name

## Key discovery

The string `saconsole` is not one identifier — it conflates **at least 9 distinct identity types** (virsh domain, OS hostname, hosts_map key, Ansible host, SSH target, WireGuard peer, Cytoscape node ID, display label, file/directory name). These happen to share one string today, which is a latent collision.

**New design principle adopted:** VM name, OS hostname, and network identity must never be the same string.

## Inventory results

- **648 occurrences** across **110 files** (nearly double the ~320 estimate in the issue)
- ~377 occurrences in ~57 active code files need migration
- ~271 occurrences in ~47 files are docs/session-logs/retired VBox — left as-is

### Breakdown by category

| Category | Files | Occurrences | Action |
|---|---|---|---|
| Docs / Session logs | 36 | ~166 | Leave as-is |
| Retired VBox | 10 | ~100 | Leave as-is |
| hosts_map.yml | 1 | 5 | Source of truth — add fields |
| Platforms/KVM | 13 | ~142 | Migrate |
| Ansible | 17 | ~95 | Migrate |
| Tools (Python) | 10 | ~59 | Migrate |
| Cytoscape (JS) | 4 | ~28 | Migrate |
| Orchestration | 3 | ~22 | Migrate |
| Docker/Observability | 3 | ~3 | Migrate |
| Config (WireGuard) | 3 | ~13 | Partial |
| Packer / root scripts | 3 | ~10 | Migrate |

## Decisions made

1. **Schema change to `hosts_map.yml`** — add `vm_name` and `display_name` as explicit fields for every host, so each identity is independently addressable.

2. **Single branch, single PR** — no phased PRs. A half-migrated codebase is harder to test than a clean sweep. The acceptance test (`rebuild_lab.sh`) is all-or-nothing anyway.

3. **Decompose `bootstrap_saconsole.sh`** during this refactor — it's 297 lines (known >50-line violation). Rename to `bootstrap_hub.sh` with ≤50-line extracted functions.

4. **Migration rule per identity type** — each occurrence is replaced with the correct field for its context (vm_name for virsh, hostname for OS identity, hosts_map_key for lookups, display_name for UI, etc.).

## Artefacts

- Full implementation plan posted as comment on #171:
  https://github.com/martinhbramwell/ESACP/issues/171#issuecomment-4246177913
- Covers: identity taxonomy, schema change, migration rules, scope, 6-step implementation sequence, acceptance criteria, risks

## Issues touched

- #171 — implementation plan posted (planning complete, implementation next session)

## No code changes this session (planning only, per constraints)
