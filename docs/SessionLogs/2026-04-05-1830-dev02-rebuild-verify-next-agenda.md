# Agenda — dev02 Full Rebuild + Supplier Field Verification

**Objective:** End-to-end verification that the `insert_after: tax_id` fixture fix (ce_sri `a5c776e`) survives a clean pipeline rebuild. Purge dev02 via topology UI, rebuild from scratch, confirm Purchase Taxes and Charges Template renders correctly on the Supplier form.

**Pre-requisite:** ce_sri `wip/2026-03-25` branch has commit `a5c776e` (fixture fix) pushed to GitHub.

---

## Steps

1. **Open topology UI** — `http://localhost:5173`
2. **Destroy dev02** — right-click → Destroy (or drag to trash). Wait for job completion.
3. **Verify purge on hypervisor** — dev02 VM removed from `virsh list --all`, disk image deleted, WireGuard peer removed from saconsole hub.
4. **Deploy dev02** — drag from palette to Dev zone (or right-click → Deploy). Wait for full pipeline (~15 min): provision → cloud-init → differentiate (sections A through L).
5. **Verify ERPNext is live** — `https://dev02.iridium.blue` returns HTTP 200.
6. **Verify Supplier field** — open any Supplier record, confirm "Purchase Taxes and Charges Template" appears between Tax ID and Tax Category.
7. **Verify all 13 Custom Fields** — spot-check Sales Invoice commission fields and other externalized fields.
8. **Run sync_check** — `bash platforms/kvm/sync_check.sh` — all sections green.

## Success criteria

- dev02 fully destroyed and rebuilt without manual intervention
- Purchase Taxes and Charges Template field renders in correct position on Supplier form
- All topology UI operations (Destroy + Deploy) — no CLI fallback

## Notes

- All operations via topology UI — CLI only for sync_check and verification queries
- If Deploy is not available in the UI for dev02, document what's missing and open an issue
