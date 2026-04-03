# Minutes — 2026-04-03 19:00 — Eliminate sed from differentiate pipeline

## Objective
Remove all `sed` usage from the differentiate pipeline, replacing with Python scripts.

## Outcomes

### Completed
- **H4e sed eliminated**: Created `tools/vm_scripts/h4e_patch_parms.py` — injects fresh API key into `ce_sri_parms.json`, then `UPDATE_SRI_SERVICE_PARAMETERS.py` generates all `.env` variants + `setTESTMODE.sh` / `setPRODUCTIONMODE.sh` on the target VM. One script + one parameters file — no SCP of pre-built .env files from controller.
- **G-pre sed eliminated**: Created `tools/vm_scripts/gpre_strip_definer.py` — streams line-by-line to avoid OOM on low-RAM VMs (first attempt loaded entire dump into memory, killed by OOM on dev02).
- **Step 10 parms enriched**: `api_protocol=https` and `api_port=443` now set in `ce_sri_parms.json` during generation, so all ERP connection values are complete before the file reaches the VM.
- **h4a_apikeys.py committed**: Was created in prior session but never tracked.
- **#93 closed**: dev02 deployed end-to-end with sed-free pipeline, all services green.
- **CLAUDE.md updated**: "Existing violations" section now reads "None — all migrated".

### Verified on dev02
- `.env_20260403_TEST_IVA15` + `.env_20260403_PROD_IVA15` + `setTESTMODE.sh` + `setPRODUCTIONMODE.sh` all generated on VM
- ERP_HOST=dev02.iridium.blue, AMBIENTE=1, api_port=443, real API key — all correct
- Health: web/app/db all green

## Commits
| Hash | Description |
|------|-------------|
| `ad69aee` | refactor(kvm): eliminate all sed from differentiate pipeline |
| `dfa81d3` | chore(kvm): track h4a_apikeys.py in tools/vm_scripts |
| `4f735ff` | fix(kvm): stream DEFINER strip to avoid OOM on low-RAM VMs |
| `579d617` | docs(session): minutes + next agenda |

## Issues
| Issue | Status | Notes |
|---|---|---|
| #93 | Closed (4f735ff) | dev02 end-to-end verified |
| #94 | Open | H4a wipes admin password set by H3 — `DELETE FROM __Auth` destroys password row |

## Root cause — admin login failure
H3 runs `bench set-admin-password sasa` → writes password to `__Auth`. Then H4a runs `DELETE FROM __Auth` (blanket wipe) and only regenerates `api_key`/`api_secret`. Password row is destroyed. Fix: move H3 after H4a, or have H4a preserve `fieldname='password'` rows.

## Observations
- dev02 Commission section missing custom fields vs dev01 — ce_sri fixture bugs #83/#84 still affecting fresh deploys (fixed manually on dev01, not committed to ce_sri repo)
