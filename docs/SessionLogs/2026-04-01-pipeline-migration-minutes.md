# Session Minutes — 2026-04-01 Pipeline Migration (GitHub Clone)

**Objective**: Complete pipeline migration — replace controller rsync with on-VM git clone from GitHub.

## Completed

### 1. Pipeline migration — commit cf68e62

- **api.py Step 10**: SCP deploy keys + passphrase to VM; rsync BKP only (apps no longer rsynced)
- **differentiate.sh A2c**: Install SSH config aliases (`ce_sri.gh`, `ce_sri_svc.gh`, `route_planner.gh`) + SSH_ASKPASS for non-interactive passphrase
- **differentiate.sh A2d**: Idempotent git clone/pull for all 5 app repos (ce_sri, route_planner, BtlMng, ce_sri_svc, BaRe)
- **Section B ownership**: Reduced to BKP only (apps now cloned as ERP_USER — correct ownership by construction)
- **Refresh endpoint**: Removed rsync block — differentiate.sh A2d handles `git pull` on re-run
- **Constants removed**: `CE_SRI_SRC`, `RETURNABLE_SRC`, `ROUTE_PLANNER_SRC`, `BARE_SRC` no longer needed

### 2. Full rebuild test on dev01 — verified

- Destroy + provision from template: all 9 supervisor services RUNNING
- All 5 repos cloned with correct GitHub remotes and branches
- Health check: web/app/db all green

### 3. GH #80 — setTESTMODE.sh fails after git clone

Opened and closed during session. The git clone flow does not bring untracked files like `.env_20260122_TEST_IVA15` — only tracked files are present. Initial fix used `.env.sample` as source — **wrong approach, corrected later in session**.

### 4. Real .env files deployed to dev01

User created new dated variants (`.env_20260401_TEST_IVA15`, `.env_20260401_PROD_IVA15`) and updated `setTESTMODE.sh` / `setPRODUCTIONMODE.sh`. Deployed manually to dev01 with ERP connection parametrised:
- `ERP_HOST=dev01.iridium.blue`, `ERP_PTCL=https`, `ERP_PORT=443`
- `setTESTMODE.sh` activated → AMBIENTE=1, BIND_PORT=5000, real company data
- ce_sri_svc running with real values (IVA 15%, real cert, real address)

### 5. chkMode.sh + spvstr alias

Created `chkMode.sh` in bench dir — waits 3s then greps ce_sri_svc log for Revenue Service Operational Mode. `spvstr` alias updated to call it after `supervisorctl start all`.

### 6. modules.txt accent fix — `Comprobantes Electrónicos` → `Comprobante Electronico`

`bench migrate` was failing with `ModuleNotFoundError: No module named 'ce_sri.comprobantes_electrónicos'` because `modules.txt` had an accented `ó` but the actual directory is `comprobante_electronico` (ASCII). Fixed on dev01:
- Updated `modules.txt` to `Comprobante Electronico`
- Updated `tabModule Def` record in DB
- **Must be committed to ce_sri repo** — not yet done

### 7. Fixture import — 12 of 40 Custom Fields were missing

`bench migrate` only imported 28 of 40 ce_sri Custom Fields. Root cause: `Supplier-purchase_taxes_and_charges_template` in the fixture JSON conflicts with a standard ERPNext field → Frappe's `import_doc` aborts on first error, skipping all subsequent fields. Fixed by running a script that inserts missing fields individually, skipping conflicts. 10 inserted, 2 skipped (already exist).

**`forma_de_pago_especificada`** and all commission fields now visible on Sales Invoice.

## Correction — ce_sri_svc .env approach was wrong

### What happened

Section B2 was modified to generate `.env` by copying `.env.sample` and patching AMBIENTE + ERP_HOST. This produced a service running with **placeholder garbage** in every field except the 2-3 patched ones — no real company data, no certificate, no IVA rate, no email config.

### Why it was wrong

`.env.sample` is a documentation template for humans. The original ce_sri scripts use a **family of real `.env` files** with all actual values:

| File | Purpose |
|---|---|
| `.env_YYYYMMDD_TEST_IVA15` | All real values, AMBIENTE=1, test email recipients |
| `.env_YYYYMMDD_PROD_IVA15` | All real values, AMBIENTE=2, production email recipients |
| `setTESTMODE.sh` | `cp .env_YYYYMMDD_TEST_IVA15 .env` |
| `setPRODUCTIONMODE.sh` | `cp .env_YYYYMMDD_PROD_IVA15 .env` |

The only difference between TEST and PROD variants is:
1. `AMBIENTE` (1 vs 2)
2. Which email block is active (test recipients vs production recipients)

Everything else is identical — real company data, real certs, real IVA rate, real API credentials.

### What must happen instead

1. The 4 files (two `.env_*` variants + two `set*MODE.sh` scripts) are secrets that live on the controller, outside git
2. They get SCP'd to the VM during provisioning (Step 10, alongside deploy keys)
3. Section B2 must parametrise the ERP connection block in **both** `.env_*` files:
   - `ERP_HOST` → the VM's site URL (e.g. `dev01.iridium.blue`)
   - `ERP_PTCL` → `https` (dev/staging VMs serve through nginx with TLS)
   - `ERP_PORT` → appropriate for the VM (dev/staging: 443)
   - `ERP_API_TKN` → the API key:secret valid for the restored database on that VM
4. Then run `setTESTMODE.sh` to activate the TEST variant as `.env`
5. `setPRODUCTIONMODE.sh` is deployed but never called on dev/staging — it exists for future promotion

## Issues

| Issue | Status | Notes |
|---|---|---|
| #80 | Closed (cf68e62) | setTESTMODE.sh fix — Section B2 still needs rewrite for real .env files |
| #81 | Open | BIND_PORT — moot once real .env files are in pipeline |

## Bugs found — not yet filed

- **ce_sri modules.txt accent** — `Comprobantes Electrónicos` must become `Comprobante Electronico` (ASCII). Blocks `bench migrate` on fresh clones. Needs commit to ce_sri repo.
- **Fixture import aborts on first conflict** — `Supplier-purchase_taxes_and_charges_template` conflicts with standard ERPNext field. Frappe's `import_doc` stops entirely. The fixture JSON either needs this entry removed, or the pipeline needs a post-migrate script that inserts missing fields individually.
