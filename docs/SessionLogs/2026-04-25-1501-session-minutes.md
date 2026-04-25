# Session Minutes — 2026-04-25 1501

## Declared objective (from prior next-agenda)

Fix **#298** (screen-4a Company-name textbox-render race) on `fix/wizard-screen-4a-render-wait` sub-branch off `umbrella/ladder-fixture @ 22997aa`. Acceptance: 3-of-3 consecutive `replay_wizard.js` runs against fresh `"ERPNext V13 before Wizard"` snapshot.

## Outcome

**Objective abandoned mid-session by operator decision.** v13 setup wizard determined fundamentally too flaky for reliable Playwright automation; defer to ERPNext v14. Session pivoted to producing a **certified v13 + Pseudo-Co restored substrate** on dev02 as the starting line for v13→v14 upgrade work.

## What happened

### Phase 1 — #298 attempt and shelve (declared objective)

1. Sync_check at start: 49 ✅ / 8 ⚠️ / 0 ❌ (warnings all expected: dormant VMs, sops cosmetic, Chrome manual-verify).
2. Cut `fix/wizard-screen-4a-render-wait` off `umbrella/ladder-fixture @ 22997aa`.
3. Reverted dev02 to `"ERPNext V13 before Wizard"` snapshot.
4. Applied **minimum-diff fix at screen 4a**: one line — `await page.waitForURL('**/setup-wizard/4*', { timeout: 30_000 })` between Industry-Next click and screen-4a fill (`prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js:158`).
5. **3-of-3 acceptance: 2 PASS + 1 FAIL**. Failure mode shifted from `getByRole('textbox').first()` timing out at the fill, to `waitForURL` itself timing out — surfacing that the Industry-Next click sometimes fires no navigation at all (modal-intercept hypothesis).
6. Operator experimented with a cleaner Playwright-idiomatic pattern: replaced the DOM-mutation checkbox loop (`#267` fix) with `.locator('input[type="checkbox"][data-unit="${industry}"]').check()`; removed the welcome-modal backdrop fallback (`#284 + #293` fix); added `'Distribution'` to industries.
7. Reviewed those changes — flagged removal of the modal-handler block as risky because the welcome-modal race those guards were engineered to dodge is real and load-dependent, not eliminated by selector specificity.
8. Operator authorised a **5× empirical characterisation** run against the experimental version. Result: **3 PASS / 2 FAIL = 40% failure rate**. Both failures showed `<div ... class="modal fade show">…</div> intercepts pointer events` during `.check()`'s actionability retry loop — exact failure mode the deleted DOM-mutation block existed to dodge (per #267 commit message).
9. **Operator decision: shelve all wizard hardening at v13, revisit when v14 lands** — under the reasoning that the v13 wizard requires defensive (not idiomatic) Playwright code to clear consistently, and even with that defensive code residual flake remains.

### Phase 2 — wizard-work cleanup

10. Discarded sub-4 working tree (`git checkout -- ...` on the two modified files; removed three leaked `pw-replay-*.cjs` temp files).
11. Switched to `main`, deleted `fix/wizard-screen-4a-render-wait` (never pushed).
12. Closed **#298** with `state_reason: not_planned` and a detailed comment summarising attempted fix, 5×-run evidence, and v14 deferral rationale (`#issuecomment-4319992545`).
13. Held PR #299 (sub-3, `fix(wizard-replay): extract welcome-modal handler, extend to #296 + #297 sites`) and the entire `umbrella/ladder-fixture` parked unchanged. Both verified `mergedAt = null`, `state = OPEN`.

### Phase 3 — pivot: produce v13 Pseudo-Co substrate on dev02

14. Cut `feat/v13-to-v14-upgrade-experiment` off `main` (no commits yet, reserved for the upgrade attack).
15. **Initial command-name confusion**: tried `./tools/esacp.py destroyVM dev02` — that's the legacy local-libvirt subcommand, can't see remote (toshiba) VMs. Pivoted to `./tools/esacp.py destroy dev02` (full macro: WG peer + VM + hosts_map + group_vars + inventory + Ansible WG + SOPS keys + cloud-init).
16. **`destroy` requires interactive confirmation** — no `--yes` flag exists. Piped `echo "y"`. 8/8 steps green.
17. **Second snag**: `provisionGeneric dev02` exited 1 with `Unknown VM 'dev02'. Valid: saconsole, dev03, target5, dev01` — because `destroy` had cleared the registration, but `provisionGeneric` requires the host to be present in `hosts_map.yml`. The matrix Run 04 procedure used the legacy `destroyVM` (which keeps registration), explaining why their flow worked direct.
18. Re-registered via `./tools/esacp.py addHost dev02 --zone development --wg-ip 10.10.0.17 --virbr0-ip 192.168.122.27 --hypervisor toshiba --backend kvm --nickname dev0` (same IPs as the prior registration, now free).
19. Ran `./tools/esacp.py provisionGeneric dev02 --wizard-mode existing --wizard-arg 20260422_112724-dev01_iridium_blue.tgz` (B03 from matrix Phase 3A regen). All 9 stages green; wizard-completion phase short-circuited to `handleRestore.sh` (B03 restored in 2m 8s); pipeline exit 0; total ~9 min.
20. Cleared stale known_hosts entries for `10.10.0.17` and `192.168.122.27` (new VM host key after rebuild) — re-added with `accept-new` on next SSH.
21. **Substrate verification**:
    - HTTPS `/login` → 200
    - `bench --site dev02.iridium.blue version` → `frappe 13.58.22`, `erpnext 13.55.2`
    - `bench --site dev02.iridium.blue list-apps` → **frappe + erpnext only** (no `ce_sri` / `route_planner` / `returnable` — `#289`'s Stage 6 gate working as intended on the umbrella tip)
    - Pseudo-Co Company canary: `[{"name": "Pseudo-Co", "abbr": "PSC", "country": "Canada", "default_currency": "CAD"}]`
22. Snapshot captured on toshy: `v13-Pseudo-Co-restored` — "Matrix Run 04 exit state — post-B03 restore, ERPNext 13.55.2 / Frappe 13.58.22, bench-clean (frappe + erpnext only, post-#289)".
23. Comment posted on **#289** confirming bench-clean substrate produced (`#issuecomment-4320342748`). Issue remains open (umbrella tip not yet merged to main).

## Branch state at session close

```
main @ <this commit>
  └─ feat/v13-to-v14-upgrade-experiment (no commits) ← reserved for upgrade attempt
  └─ umbrella/ladder-fixture @ 22997aa (parked, indefinitely)
       ├─ feat/playwright-wizard-generic-fixture (sub-2) @ 8dc2e71 (parked)
       └─ feat/wizard-complete-setup-fix (sub-3) @ cbf8f17 + PR #299 OPEN/HELD (parked)
```

dev02 on toshy: running, snapshot `v13-Pseudo-Co-restored` captured for revert.

## Issues touched

- **#298** — closed `not planned` with v14-deferral comment.
- **#289** — confirmation comment posted; remains open (closure tracks umbrella → main merge).
- **#296, #297** — no change; tied to PR #299, both parked.

## PRs touched

None opened. **#299** verified unchanged (`mergedAt: null`, `state: OPEN`).

## What did NOT happen this session

- No PR opened, no commits to `main` (other than this minutes commit).
- v13→v14 upgrade attack itself — deferred to next session (substrate is now ready).
- No decision yet on `umbrella/ladder-fixture` long-term retention.
- No archival of the four `20260424_*-dev02_iridium_blue.tgz` polluted backups — still in `platforms/kvm/golden_backups/`. Originally deferred behind "until clean B03 produced"; B03' was not produced this session because wizard work shelved.

## Erratum on prior session's agenda assumption

The `2026-04-25-0758-next-agenda.md` queued ladder-style sub-4 work assuming wizard fixes would continue. That premise is now invalidated. The umbrella's purpose — produce a clean Playwright-driven generic-mode B03' artefact — remains unfulfilled, and the bespoke fixes within it (#296/#297 modal helpers) are blocked behind v13-wizard reliability gates we have now formally given up on. Re-evaluate the umbrella's reason-to-exist when v14 work begins.
