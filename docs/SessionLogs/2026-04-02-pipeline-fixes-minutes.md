# Session Minutes — 2026-04-02 Pipeline Fixes

## Objective
Fix ce_sri repo bugs (#2, #3 from agenda) and pipeline secrets (#4, #5), then end-to-end test dev02 provision (#6).

## Completed

- ✅ **SSH config fixed**: dev01/dev02 entries with `ProxyJump toshy` + `dev01-erp`/`dev02-erp` aliases for erpadm
- ✅ **erpadm authorized_keys**: deployed `hasan_mighty.pub` on both dev01 and dev02
- ✅ **#83 — modules.txt accent fix**: `Comprobantes Electrónicos` → `Comprobante Electronico` in ce_sri repo (`c4fb7d3`)
- ✅ **#84 — fixture conflict**: removed `Supplier-purchase_taxes_and_charges_template` (standard ERPNext DocField, not custom) from ce_sri `custom_field.json` + `hooks.py` (`3c287ed`)
- ✅ **Item 4 — SOPS ce_sri_parms.json**: populated with real values (user did manually)
- ✅ **Item 5 — Secret rotation**: skipped by decision — risk too low vs effort
- ✅ **#85 — f-string `{count}` bug**: unescaped in api.py differentiate.sh template, crashed Step 12 (`b577c18`)
- ✅ **#86 — `_CESRI_SVC` unbound**: variable definition removed with Section B2, but B2b still referenced it (`1027a52`)
- ✅ **Timestamps added**: all 5 job runners in api.py now log `[HH:MM:SS]` UTC (`a2bf568`)
- ✅ **Playwright deploy test fixed**: drag-to-deploy replaces stale right-click context menu (`d6c6219`)
- ✅ **bash_aliases moved to Section A1**: earliest possible in differentiate.sh (`0df5766`)
- ✅ **Feedback memory saved**: remote SSH script pattern (write script, SCP, run — don't inline)

## Discovered / Deferred

- 🔄 **#87 — Refresh doesn't re-SCP secrets**: ce_sri_parms.json, P12 cert, logo not re-sent on Refresh. .env and ce_sri_svc broken after Refresh.
- 🔄 **`bench list-apps` empty on dev02**: apps are git-cloned but not `bench install-app`'d. `installApps.sh` (Section F) may not be handling this correctly. 0 Custom Fields as a result.
- 🔄 **dev01-differentiate.sh not patched**: older format, didn't get _CESRI_SVC or bash_aliases fixes. Needs regeneration on next provision.
- 🔄 **SRI PRUEBAS retry**: moved to 2026-04-07 agenda (Easter downtime).

## Key Decisions

- `Supplier-purchase_taxes_and_charges_template` confirmed as standard ERPNext DocField (in `tabDocField`, added by runtime patch). Safe to remove from fixture — not a business customisation.
- Secret rotation (cert pwd, SMTP pwd, API tokens) deferred — conversation-only exposure, not public.
- bash_aliases installed early (Section A1) as safety net against `bench start` confusion.
- Remote SSH commands: always write temp script + SCP + run. Never inline complex commands.

## Commits (ESACP main)

| Hash | Description |
|---|---|
| `b577c18` | fix(api): escape `{count}` in f-string — fixes #85 |
| `a2bf568` | feat(api): add UTC timestamps to all job log lines |
| `d6c6219` | fix(cytoscape): update Deploy test to drag-to-deploy |
| `1027a52` | fix(api): define `_CESRI_SVC` before B2b — fixes #86 |
| `49fce8c` | fix(kvm): patch saved dev02-differentiate.sh |
| `0df5766` | refactor(api): move bash_aliases to Section A1 |

## Commits (ce_sri wip/2026-03-25)

| Hash | Description |
|---|---|
| `c4fb7d3` | fix: correct modules.txt — fixes #83 |
| `3c287ed` | fix: remove standard field from fixture — fixes #84 |
