# ERPNext Lab Restore — A→Z Runbook

Full procedure for restoring a production ERPNext backup into the lab (target1),
starting from the "ERPNext v13 Installed" snapshot and ending with a fully operational
ERPNext instance carrying production data and all bespoke apps.

---

## Snapshots on target1

| Snapshot | Contents | When to use |
|---|---|---|
| `ERPNext Lab Fresh Install` | Ubuntu 22.04, bench prereqs | Redo full ERPNext install |
| `ERPNext v13 Installed` | frappe + erpnext installed, no apps, no data | **Start of A→Z restore** |
| `ERPNext v13 Bespoke Apps` | + ce_sri, returnable, route_planner pip-installed | Skip Phase 5 if apps unchanged |
| `ERPNext v13 Production DB Restored` | + production data, bench migrate, SLK cleared | Gold reference |

---

## Prerequisites

All of the following must be in place on the controller machine before starting:

| Item | Location | Notes |
|---|---|---|
| Bespoke app: ce_sri | `~/projects/Logichem/ce_sri_prod/ce_sri/` | Production checkout |
| Bespoke app: returnable | `~/projects/Logichem/returnable_prod/returnable/` | Production checkout |
| Bespoke app: route_planner | `~/projects/Logichem/route_planner_prod/route_planner/` | Production checkout |
| BaRe scripts | `~/projects/Logichem/BaRe/` | handleRestore.sh, installApps.sh |
| Backup archive | `~/projects/Logichem/ce_sri/BKP/<date>-erp_logichem_solutions.tgz` | Copied from production |
| Backup name holder | `~/projects/Logichem/ce_sri/BKP/BACKUP.txt` | Contains archive filename |
| envars.sh | `~/projects/Logichem/envars.sh` | Lab site config + restore flags |
| WireGuard mesh | `you@10.10.0.3` reachable | `ping 10.10.0.3` to verify |

### envars.sh restore flags

```bash
export RESTORE_SITE_CONFIG="no"    # keep lab site_config.json (lab encryption_key)
export KEEP_SITE_PASSWORD="yes"    # retain lab DB password if RESTORE_SITE_CONFIG=yes
```

Set `RESTORE_SITE_CONFIG="yes"` only if you want to replace the lab's site_config.json
with the one from the backup (needed to test encryption-dependent features like SRI certs).

---

## One-command run (with snapshot revert)

```bash
cd ~/projects/Logichem/ESACP
bash platforms/kvm/provision_erpnext_restore.sh --fresh
```

`--fresh` reverts target1 to "ERPNext v13 Installed" before starting.
Omit `--fresh` if you already reverted manually.

---

## Step-by-step (if running manually)

### Step 1 — Revert target1 snapshot (from controller)

```bash
ssh hasan@toshy "virsh --connect qemu:///system snapshot-revert target1 \
    'ERPNext v13 Installed' --running"
# Wait ~60s for WireGuard to come up, then:
ssh you@10.10.0.3 true   # should succeed without error
```

### Step 2 — Rsync bespoke apps (from controller)

```bash
LOGICHEM=~/projects/Logichem
BENCH="you@10.10.0.3:/home/adm/frappe-bench-T1LAB"
RSYNC="rsync -a --delete --rsync-path=sudo rsync"

$RSYNC ${LOGICHEM}/ce_sri_prod/ce_sri/        ${BENCH}/apps/ce_sri/
$RSYNC ${LOGICHEM}/returnable_prod/returnable/ ${BENCH}/apps/returnable/
$RSYNC ${LOGICHEM}/route_planner_prod/route_planner/ ${BENCH}/apps/route_planner/
rsync -a --rsync-path="sudo rsync" ${LOGICHEM}/BaRe/ ${BENCH}/BaRe/
rsync -a --rsync-path="sudo rsync" ${LOGICHEM}/ce_sri/BKP/ ${BENCH}/BKP/
```

### Step 3 — Push envars.sh (from controller)

```bash
scp ~/projects/Logichem/envars.sh you@10.10.0.3:/tmp/envars_lab.sh
ssh you@10.10.0.3 "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A cp /tmp/envars_lab.sh /opt/ce_sri/envars.sh"
```

### Step 4 — Install apps (on target1 as adm)

```bash
ssh you@10.10.0.3 "sudo -u adm bash -c 'cd ~/frappe-bench-T1LAB && bash BaRe/installApps.sh'"
```

This does:
- `pip install -e apps/{ce_sri,returnable,route_planner}`
- Adds apps to `sites/apps.txt`
- `bench migrate` to create DocTables for the new apps (pre-restore)
- Copies `apps/ce_sri/example_srvr_files/views.ddl` → `sites/lab.target1.local/private/files/ddlViews.sql`

### Step 5 — Restore database (on target1 as adm)

```bash
ssh you@10.10.0.3 "sudo -u adm bash -c 'cd ~/frappe-bench-T1LAB && bash BaRe/handleRestore.sh'"
```

handleRestore.sh does:
1. Reads `BKP/BACKUP.txt` to find the backup archive
2. Detects site name mismatch (production `erp_logichem_solutions` ≠ lab `lab_target1_local`)
3. Repackages the archive with the lab site name substituted throughout
4. Decompresses to `/dev/shm/BKP` (requires 8 GB RAM on target1 — set in hypervisor)
5. `bench --site lab.target1.local --force restore ...`
6. `bench migrate --skip-failing` — applies schema patches for version gap (13.39.2 → 13.55.2)
7. Deletes `tabSocial Login Key` rows — clears encryption-key mismatch on login page
   (only when `RESTORE_SITE_CONFIG="no"`)
8. Applies `ddlViews.sql` with production DB hash substituted for the lab DB hash
9. Calls `restoreSocialLoginConfig()` (requires `apikey.sh` — see below)

### Step 5a — API key for restoreSocialLoginConfig

`restoreSocialLoginConfig()` sources `sites/lab.target1.local/private/files/apikey.sh`.
This file must exist with a valid Administrator API key **after the restore** (the restore
replaces the database, invalidating any pre-restore key).

For the lab, Google OAuth does not work (self-signed cert). Two options:
- **Skip it:** comment out `restoreSocialLoginConfig` in the main block (set `1 == 0`)
  — Social Login Keys are already deleted in step 6 above, so the login page is clean.
- **Restore it:** after the restore, generate a new API key, write apikey.sh, then
  re-run `restoreSocialLoginConfig` manually.

To generate apikey.sh after restore:
```bash
ssh you@10.10.0.3 "sudo -u adm bash -c '
    cd ~/frappe-bench-T1LAB
    result=\$(bench --site lab.target1.local execute \
        frappe.core.doctype.user.user.generate_keys --args \"['"'"'Administrator'"'"']\")
    secret=\$(echo \"\$result\" | python3 -c \"import sys,json; print(json.load(sys.stdin)['"'"'api_secret'"'"'])\")
    key=\$(bench --site lab.target1.local execute frappe.client.get_value \
        --args \"['"'"'User'"'"', '"'"'Administrator'"'"', '"'"'api_key'"'"']\")
    key=\$(echo \"\$key\" | tr -d '"'"'\"'"'"')
    echo \"export KEYS=\\\"\${key}:\${secret}\\\"\" \
        > sites/lab.target1.local/private/files/apikey.sh
'"
```

### Step 6 — Verify (from controller browser via WireGuard)

Open `https://lab.target1.local` in a browser.
Accept the self-signed certificate warning.
Log in as `Administrator` with password `sasa`.

Expected:
- Production company name visible in top-right
- ERPNext home page loads without errors
- `bench version` shows: frappe 13.x, erpnext 13.55.x, ce_sri 0.0.1, returnable 0.0.1, route_planner 0.0.1

---

## Known issues and workarounds

### Schema version gap (13.39.2 → 13.55.2)

Production backup is from ERPNext 13.39.2. Lab bench is 13.55.2. Several DocType fields
added in between cause `InvalidColumnName` errors if `bench migrate` is not run after restore.
`handleRestore.sh` runs `bench migrate --skip-failing` automatically.

The `frappe.patches.v12_0.delete_duplicate_indexes` patch fails on MariaDB 10.5+ (queries
a removed `information_schema.global_status` view). `--skip-failing` skips it harmlessly.

### Social Login Key encryption mismatch

The production backup contains Social Login Key rows encrypted with the production
`encryption_key`. The lab's `site_config.json` has a different `encryption_key`.
ERPNext throws `Encryption key is invalid` on the login page when it tries to load these.

Fix: delete all rows from `tabSocial Login Key`. `handleRestore.sh` does this automatically
when `RESTORE_SITE_CONFIG="no"`.

### ddlViews.sql production DB hash

The `views.ddl` file contains `CustomerPayments` view with a hardcoded reference to the
production database hash (`_091b776d72ba8e16`). The lab database hash is `_490d9b08b0a13ea9`.
`handleRestore.sh` substitutes any 17-character `_[hex]` pattern with `${ACTIVE_DATABASE}`
before applying the SQL.

### Redis/supervisord restart after snapshot revert

After reverting a snapshot, the Redis processes from the previous session may still be
alive (snapshot captured a running state). If `supervisorctl start` fails with
"Address already in use" for Redis, wait 30–60 seconds for the orphaned processes to exit,
then start the services manually:
```bash
sudo supervisorctl start \
    "frappe-bench-T1LAB-redis:frappe-bench-T1LAB-redis-cache" \
    "frappe-bench-T1LAB-redis:frappe-bench-T1LAB-redis-queue"
```

---

## Pending: SRI electronic voucher connection test

SRI = Servicio de Rentas Internas (Ecuadorian tax authority).
ce_sri sends signed electronic vouchers (facturas, retenciones, etc.) to SRI servers.
This requires:
- A valid `.p12` digital signature certificate (Ecuadorian SRI-issued)
- `ce_sri_parms.json` at `~/.ssh/secrets/ce_sri_parms.json` on target1
- Correct SRI environment (test vs production URLs in ce_sri settings)

**Not yet tested in the lab.** Test by submitting a document that triggers an electronic
voucher and checking the SRI response in the `Comprobantes Electrónicos` DocType.
