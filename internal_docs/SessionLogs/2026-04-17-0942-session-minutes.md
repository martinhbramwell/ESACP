# Session Minutes — 2026-04-17 09:42 EDT

**Objective**: Resolve #210 (hub WG peer drift) — Phase 9 preliminary blocker
**Result**: ✅ Complete. PR #214 merged 2026-04-17T13:40:47Z, merge commit `fdf73a9`. #210 auto-closed.

---

## Unfinished Business (carried from prior session)

| Item | Status |
|---|---|
| #210 — destroy strips hub WG peer; re-applying play doesn't restore | ✅ CLOSED — PR #214 merged, `fdf73a9` |
| Phase 9 (#197) — decompose `tools/install_specific.py` | ⏸ NEXT SESSION — agenda drafted |

---

## New Business

### ✅ CLOSED

1. **#210 root cause identified** — `ansible/roles/wireguard/tasks/main.yml` detected change via file-content in the `template` task. When a destroy (or any direct `wg set … peer remove`) mutated live `wg0` without touching inventory/sops, the rendered `wg0.conf` was byte-identical to on-disk → `restart wg0` handler silent → drift persisted across reruns. Confirmed by static analysis of role/handler/template **and** by a deliberate drift regression test.

2. **Fix implemented and validated** — one task added to `ansible/roles/wireguard/tasks/main.yml` after `Enable and start wg-quick@wg0`:
   ```yaml
   - name: Reconcile wg0 runtime state with wg0.conf (hub only)
     shell: "wg syncconf wg0 <(wg-quick strip wg0)"
     args:
       executable: /bin/bash
     changed_when: false
     when: wg_role == 'hub'
   ```
   `wg syncconf` is the native WireGuard reconciler — applies the delta to the kernel without interrupting traffic or tearing down handshakes. Rejected alternatives: hand-rolled `wg show`/`wg set` diff (reinvents syncconf), `notify + flush_handlers` (still needs textual change), `wg-quick down/up` (needless outage).

3. **Evidence recorded** — posted as a comment on #210:
   - Real drift found on session start: hub 4 peers, file 5 peers, missing `dev01` (`LUOR6yrc7…` @ 10.10.0.13/32) from post-Phase-8 teardown.
   - First play run with fix: `sync_check` 9b → green, peer restored.
   - Deliberate regression test: `wg set wg0 peer <dev01> remove` → 4 peers → play → `Deploy wg0.conf: ok` (unchanged, handler silent as predicted) → `Reconcile … : ok` → 5 peers.

4. **#213 filed during session** — `session_close_audit` hook uses a relative path (`.claude/hooks/session_close_audit.sh`) in `.claude/settings.json` and fails with `/bin/sh: not found` on every `UserPromptSubmit`. Non-blocking (hook errors silently, session continues). Introduced by `c248b9d`. Trivial fix: `${CLAUDE_PROJECT_DIR}/.claude/hooks/…`. Filed **before** returning to #210 per one-objective discipline.

### ⏸ PARKED / DEFERRED

- **Phase 9 (#197)** — full scope per `~/.claude/plans/synthetic-mapping-pretzel.md`. Agenda drafted at `2026-04-17-0942-next-agenda.md`. Fresh branch `fix/197-install-specific-decompose` from `main`. Mesh is now self-reconciling — Phase 9 e2e can run cleanly.

---

## Discoveries

- **Handler-based change detection is fundamentally insufficient for stateful kernel resources**. The `template → notify` pattern is correct when the file *is* the source of truth and the service reads the file on restart. For kernel-backed runtime state (WireGuard, netfilter, routing), a post-write reconcile step against live state is structurally required. Pattern to reuse: `native-tool --syncconf`-style reconciliation over hand-rolled diffs.
- **Session start found real drift** (not reproduced — discovered). The post-Phase-8 environment was already in the broken state, so the fix was validated against a genuine regression, not only a synthetic one. The deliberate `wg set … peer remove` test was then run for definitive evidence that the play (with old behaviour) silently no-ops and (with new behaviour) restores state.

---

## Process notes

- **One-objective discipline held** — #213 surfaced mid-session (hook noise in transcript). Filed immediately, not fixed. Returned to #210.
- **Confirm-before-acting held** — proposed fix + evidence before implementing, then again before opening PR, then again before merging.
- **1:1:1 discipline held** — one issue (#210), one branch (`fix/210-wg-hub-peer-reconcile`), one session. Next objective (#197) moves to its own session.
- **Guardrail observation** — agenda said "if preliminary balloons past ~2 hours, stop and move Phase 9". Preliminary took well under 2 hours end-to-end.

---

## State at session close

- Branch: `main` (pulled to `fdf73a9`); working tree clean
- Open issues: #48, #50, #65, #138, #153, #156, #157, #181, #187, #188, **#197**, #202, #206, #211, **#213**
- Open PRs: none
- sync_check: 41 ✅ / 12 ⚠️ / 4 ❌ (4 ❌ are expected VM-not-running pings; section 9b now green)
- Mesh: hub has 5 peers as expected; wg0 healthy
- MEMORY.md updated — #210 removed from open list, #213 added with note, closure recorded inline

---

## Next session

See `2026-04-17-0942-next-agenda.md`. Objective: Phase 9 — decompose `tools/install_specific.py` (#197).
