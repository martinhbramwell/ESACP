# Agenda — Next session — Validate ERPNext customizations on clean rebuild

## Primary Objective

### Validate ce_sri Custom Fields and Property Setters on dev01/dev02 against production

Both VMs are at a clean, verified baseline (2026-04-04 rebuild). All known pipeline blockers
(#83, #84, #94) are fixed. This is the right time to confirm that the 39 Custom Fields and
194 Property Setters in `ce_sri/fixtures/` are correctly applied.

## Pre-flight
1. Run `sync_check.sh`
2. Verify both VMs healthy (health endpoint green, HTTPS 200)
3. Confirm admin login works on both

## Steps

1. **Audit Custom Fields on dev01** — compare `ce_sri/fixtures/custom_field.json` (39 entries)
   against what is actually in `tabCustom Field` on dev01. Identify any missing or mismatched.

2. **Audit Property Setters on dev01** — compare `ce_sri/fixtures/property_setter.json` (194 entries)
   against `tabProperty Setter`. Identify any missing or mismatched.

3. **Spot-check critical fields** — verify presence + correct doctype:
   - `Sales Invoice-forma_de_pago_especificada` (SRI invoicing — blocks e-invoicing if missing)
   - `Sales Invoice-commission_paid`, `Sales Invoice-sales_partner_supplier`
   - `Customer-forma_de_pago_preferida`
   - `Delivery Note-saldo_del_cliente`, `Sales Order-saldo_del_cliente`

4. **Compare dev01 vs production** (read-only Chrome on erp.logichem.solutions) — screenshot
   key doctypes (Sales Invoice, Customer) and compare field layouts.

5. **Fix any gaps** — if fields are missing, determine whether it's a fixture issue or a
   `bench migrate` issue, fix in ce_sri repo, and Refresh.

## Open Issues (15)

### Pipeline / Infrastructure
| # | Title | Priority |
|---|-------|----------|
| 87 | Refresh doesn't re-SCP secrets — .env and parms missing | High |
| 68 | Refresh runs full DB restore — should skip G/H for fast path | Medium |
| 37 | api.py jobs run as uvicorn tasks — restart kills jobs | Medium |
| 50 | cf-mcp-refresh not in repo or setup docs | Low |
| 9 | tech-debt: hardcoded usernames/machine names | Low |

### Topology UI (Cytoscape)
| # | Title | Priority |
|---|-------|----------|
| 90 | Node shows "Unprovisioned" during active provisioning | Medium |
| 91 | Clicking provisioning node should show live job logs | Medium |
| 65 | Auth architecture for Grafana-embedded control plane | Decision |

### ERPNext / App
| # | Title | Priority |
|---|-------|----------|
| 79 | ce_sri_svc startup banner should show API target | Low |

### Legacy gotchas (serpht era — deprioritized)
| # | Title |
|---|-------|
| 19 | bootstrap should inject controller pubkey into cloud-init |
| 20 | Prod app repos can't push from controller — SSH aliases missing |
| 21 | serpht: you@target2 SSH fails after bootstrap |
| 23 | stg.erpnext.host DNS interception needed |
| 24 | serpht scripts not auto-deployed to saconsole |
| 48 | Registrar credentials: secure backup + family access |

## Deferred
- SRI PRUEBAS retry (2026-04-07)
- h4e_patch_parms.py backslash collapse in f-string template (cosmetic)
