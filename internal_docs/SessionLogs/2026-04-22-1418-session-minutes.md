# Session Minutes — Phase 3A Wizard Bundle (#181, #271, #284)

**Date:** 2026-04-22 ~11:10–14:20 EDT
**Branch:** `fix/181-271-wizard-bundle` (merged to `main` via `73303a9`)
**Issues closed:** #181 (objective), #271 (approved piggyback)
**Issues opened:** #284 (mid-session bug — piggybacked), #285 (deferred Run 06 regen)
**PR:** #286 — merged 2026-04-22T18:18:07Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ fde05ff`

## Objective

Phase 3A of the open-issues purge plan — **Wizard bundle**. Parameterise the Pseudo-Co Playwright wizard recording (#181) and sweep the destroy-branch provisioned guard across the UI-transport acceptance specs (#271 piggyback). Regenerate B03 via Run 03 and B06 via Run 06 as the acceptance proof.

## Scope decisions taken at session start

1. **Option C for #181** — close against bullets 1–2 (config object, default config works). Alt-config proof (bullets 3–4) deferred as follow-up issue. Plan-file Phase 3A scope is narrower than #181's full acceptance, and `feedback_not_perfection_project.md` pushes against pre-emptive scope inflation.
2. **Delete `target5-20260415_113221.spec.js`** — first raw recording, superseded, no live callers (only historical minutes referenced it).
3. **#271 sweep narrowed by audit** — issue body suggested 5 specs. Code audit revealed the bug only lives in UI-transport specs (05, 06, 07) — CLI specs 02/03/04 use `execSync` destroy which handles pre-registered-only state cleanly. Issue body also missed spec 07. Final sweep: 3 UI specs.
4. **Branch name** `fix/181-271-wizard-bundle`.

## Pre-work — B03/B06 archival + gitignore

- `platforms/kvm/golden_backups/archive/` created; old B03 (`20260420_142102-...`) and old B06 (`20260421_114520-...`) copied in (`cp -p`, not moved — canonical copies stayed put until regen).
- `.gitignore` gained explicit directory rule for `platforms/kvm/golden_backups/archive/` on top of the existing `*.tgz` rule. Archive is local-only, git-untracked.

## #181 implementation

`prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js`:

- `DEFAULT_CONFIG` object holds the Pseudo-Co defaults (admin, country, industries, company name/abbr/description/currency/accounting_standard).
- `WIZARD_CONFIG_JSON` env var override replaces the entire config when set. Full-config replacement rather than deep-merge — the object is small and fully explicit.
- Four wizard-screen sections added as comment markers (Welcome+Country / User / Industry / Company 4a+4b).
- Industries iterated over a list — single-industry Pseudo-Co case unchanged, multi-industry alt-configs now possible without spec changes.
- `#256` setup_complete-response guard and `#267` welcome-modal DOM-mutation checkbox guard preserved verbatim.
- Canary fetch now uses `CONFIG.company.name` so alt-config company names get canary-checked correctly.

`prototypes/cytoscape/recordings/replay_wizard.js`:

- New `--config <json-file>` flag.
- Validates JSON at the parent before spawning child (bad JSON fails loudly at the operator, not inside the replay process).
- Forwards validated JSON as `WIZARD_CONFIG_JSON` in the child env.

`prototypes/cytoscape/recordings/wizard/target5-20260415_113221.spec.js` — deleted. Only live references were in historical session minutes — left as-is (archival, don't rewrite history).

## #271 implementation

`prototypes/cytoscape/tests/accept-05/06/07-*.spec.js` — identical fix pattern in each:

```js
if (existing && existing.provisioned) {
  // UI Destroy (existing behaviour)
} else if (existing) {
  // #271: pre-registered-only — CLI destroy fallback unregisters cleanly,
  // identical post-condition to the UI branch.
  execSync(`echo y | ./tools/esacp.py destroy ${params.target_vm}`, ...)
  // ...post-condition check + Cytoscape reload
} else {
  // absent — nothing to do
}
```

CLI-transport specs (`accept-02/03/04`) left untouched — they already take the `execSync` destroy path via `if (existing)` and don't exhibit the bug.

## Run 03 — passed, B03 regenerated

- `npx playwright test tests/accept-03-cli-pseudo-wizard.spec.js` — **10.7 min, green**.
- New B03: `platforms/kvm/golden_backups/20260422_112724-dev01_iridium_blue.tgz` (1.36 MB).
- Canary: `zgrep -c 'Pseudo-Co' <B03>-database.sql.gz` → **14** (parity with archived prior B03 and archived prior B06, both also 14).

## Run 06 — three failures, regen deferred to #285

Three consecutive attempts failed at **progressively earlier** points in the wizard replay:

| Attempt | Failure site | Action taken |
|---|---|---|
| 1 | Industry→Company screen-4a textbox timeout (30 s) | Filed #284; added freeze-backdrop guard before screen 4a entry. |
| 2 | Industry→Next click intercepted by welcome modal (58 click retries) | Extended #284; added Escape-dismiss of `.modal-backdrop.show` before the Next click. |
| 3 | Welcome→Next timeout (line 60, first wizard click) | Halted. New failure site, not a site addressed by #284's code. |

The code fixes for #284 sites A and B shipped in the PR, but could not be end-to-end-validated because the third failure mode blocked the flow before reaching them.

Failure pattern read: **sustained host load** (≈3 full VM destroy/rebuild cycles in 40 min, plus wizard drive) is more plausible than three genuinely independent race bugs in a single session. Decision per `feedback_not_perfection_project.md`: land the #181/#271/#284 code changes + the regenerated B03 now; defer the B06 regen + #284 revalidation to a cold-system session via #285.

#284 stays open — the code fix landed but end-to-end validation pending. Closing only after #285 passes.

## Files changed (in-repo)

| File | Change |
|---|---|
| `.gitignore` | `+5` — `platforms/kvm/golden_backups/archive/` directory rule. |
| `ansible/group_vars/all.yml` | `wg_pubkey_dev01` update from post-rebuild state. |
| `config/wireguard/keys.sops.yml` | SOPS-re-encrypted after dev01 keypair regen. |
| `internal_docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml` | `backup_source` → new B03 filename; comment annotated with archival reference. |
| `platforms/kvm/golden_backups/20260422_112724-dev01_iridium_blue.tgz` | **NEW** — regenerated B03, force-added over `*.tgz` ignore. |
| `platforms/kvm/golden_backups/20260420_142102-dev01_iridium_blue.tgz` | Deleted — old B03 (archive copy preserved locally). |
| `prototypes/cytoscape/recordings/replay_wizard.js` | `--config <json-file>` flag + env forwarding. |
| `prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js` | Full rewrite — parameterised config + #284 guards; #256/#267 preserved. |
| `prototypes/cytoscape/recordings/wizard/target5-20260415_113221.spec.js` | Deleted — superseded. |
| `prototypes/cytoscape/tests/accept-05/06/07-*.spec.js` | #271 destroy guard + CLI fallback. |

## Acceptance verification

- ✅ `node --check` clean on all edited JS.
- ✅ Run 03 passed first try (10.7 min); new B03 canary = 14 Pseudo-Co hits, parity confirmed.
- ✅ `sync_check` green at session start (46 ✅ / 11 ⚠ / 0 ❌).
- ⚠ Run 06 regen deferred to #285 (cold-system session).
- ✅ PR #286 merged, mergeCommit `73303a9`, mergedAt `2026-04-22T18:18:07Z`.
- ✅ #181 auto-closed at `2026-04-22T18:18:08Z` via `fixes`.
- ✅ #271 auto-closed at `2026-04-22T18:18:09Z` via `fixes`.
- ✅ GPG-signed commit `203aaac`, RSA key 9C6BCEA891C518AF1711B05FA232D66FDA9704E8.

## State handed to next session

- `main @ 73303a9` (+ this minutes commit).
- Open issues: **19** — unchanged net count (closed #181 + #271, opened #284 + #285). List: #48, #65, #138, #153, #156, #157, #187, #202, #219, #220, #223, #225, #235, #240, #241, #278, #280, #284, #285.
- #284 open — code fix landed, E2E pending #285.
- #285 open — tracks cold-system Run 06 regen + alt-config proof.
- Plan next hop: **Phase 3B — Saconsole bundle (#220, #225)**. If host is cold, #285 is a candidate to interleave first (tiny run, mostly waiting on hardware).

## Reminders to user (unresolved concerns)

1. **#285 entry conditions** — toshiba + saconsole + dev01 should be idle ~30 min before attempting Run 06 regen. If the stochastic "welcome modal on load" race recurs on a cold system, that means it is a real bug rather than load-related flake, and we file another #284-class issue rather than retrying.
2. **params/07-ui-pseudo-restore.yml still points at old B06** (`20260421_114520-...`). Correct and intentional — B06 wasn't regenerated in this session. Must update in the same commit that lands the new B06 (#285's acceptance step 5).
3. **Run 04 and Run 07 have not been re-exercised** with the parameterised wizard recording or the new #271 guard. They are not matrix-touched in Phase 3A per the plan, but next time they're invoked (e.g. during a matrix re-run), they will be the first real validation of the #271 sweep on those specs.
4. **#284 closure discipline** — when #285 passes, close #284 via a PR body reference rather than manual close, so the merge-commit hash is preserved in the close annotation.

## File trail

- Commit: `203aaac` on `fix/181-271-wizard-bundle`
- Merge commit: `73303a9`
- PR: <https://github.com/martinhbramwell/ESACP/pull/286>
- Closed: <https://github.com/martinhbramwell/ESACP/issues/181>, <https://github.com/martinhbramwell/ESACP/issues/271>
- Opened: <https://github.com/martinhbramwell/ESACP/issues/284>, <https://github.com/martinhbramwell/ESACP/issues/285>
- Plan file: `~/.claude/plans/open-issues-purge.md` (Phase 3A complete; next hop Phase 3B)
- This minutes: `internal_docs/SessionLogs/2026-04-22-1418-session-minutes.md`
- Prior session minutes: `internal_docs/SessionLogs/2026-04-22-1040-session-minutes.md` (#276 cf-mcp-refresh heredoc refactor)
