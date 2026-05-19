# Frappe `tabPatch Log` pre-seeding (substrate-apply technique)

When a Frappe upgrade target carries a patch with a date-suffix in
`patches.txt` (`# YYYY-MM-DD` re-run-trigger), and an older tag has already
run that patch in un-suffixed form on the data being restored, `bench migrate`
will re-run the patch — because `frappe.modules.patch_handler.executed()`
does an exact string match against the `patch` column of `tabPatch Log`.

If the patch is purely structural (no-op against already-migrated data) but
trips a runtime error against the current MariaDB substrate (e.g. cross-schema
`information_schema.tables` queries that pick up `performance_schema`
compatibility tables), pre-seeding `tabPatch Log` with the suffixed patch
name is a truthful resolution: the data work the patch would do has already
been done, so marking it executed reflects the actual state.

## Procedure

1. Identify the exact suffixed patch string in the target version's
   `apps/frappe/frappe/patches.txt`:
   ```bash
   ssh <dev-vm> "grep -n '<patch-base-name>' \
     /home/<erp-user>/frappe-bench/apps/frappe/frappe/patches.txt"
   ```
   Copy the line verbatim, including the two-space gap before `#` and the
   date.

2. Confirm the un-suffixed equivalent is already in `tabPatch Log` (i.e. the
   patch ran at the older tag on the source data):
   ```sql
   SELECT name, patch FROM `tabPatch Log`
     WHERE patch LIKE '<patch-base-name>%';
   ```
   At least one row with the un-suffixed name should exist.

3. Mark the suffixed version as executed using the frappe-native helper:
   ```bash
   bench --site <site> execute \
     frappe.modules.patch_handler.update_patch_log \
     --args '["<exact suffixed patch string from step 1>"]'
   ```
   The helper does
   `frappe.get_doc({"doctype": "Patch Log", "patch": ...}).insert(...)` —
   it handles auto-naming, timestamps, and Administrator owner.

4. Retry `bench migrate`. The pre-seeded row makes `executed()` return
   truthy and the patch is skipped.

## When NOT to use

- The patch makes data changes that would not have been captured by the
  older un-suffixed run. Re-running is required; the bug is elsewhere
  (likely in the patch's compatibility with the current MariaDB version).
- The patch's date-suffix marks a deliberate re-run because the patch
  logic itself changed. Skipping risks data corruption.
- You haven't verified the un-suffixed equivalent ran cleanly on the
  source data (`tabPatch Log` doesn't show a pre-existing row).

In all three cases, pre-seeding masks a real problem.

## Historical context

This technique was developed for [ESACP#398](https://github.com/martinhbramwell/ESACP/issues/398)
during Plan-C pinned-tag substrate-apply (frappe `v13.58.22` / erpnext
`v13.55.2`) where `frappe.patches.v12_0.delete_duplicate_indexes`
re-triggered on `# 2022-12-15` and hit MariaDB-10.6-internal
`performance_schema` compatibility tables that
`frappe.db.get_tables()` returns without `table_schema` filtering. The
substrate-config approach (disabling `performance_schema`) was attempted
and reverted: those compatibility tables remain visible in
`information_schema.tables` regardless of `performance_schema = OFF`.
