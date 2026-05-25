# 2026-05-25 0858 — Session 79 minutes

## Session number

79 (S79). Operator-driven re-verification + methodology reset after S78
critique; ended with R5 weeks-of-debugging socketio defect solved.

## Objective — stated

Operator pushback on S78 verdicts surfaced fundamental methodology
issue: API-level + schema-level checks were not user-facing parity
verification. Plan: stand up a V13 lab alongside V16 dev02, do real
A/B comparison, distinguish V16 regressions vs always-broken vs
false alarms, and propose scripted fixes for the umbrella.

## Objective — actual outcome

Achieved with substantial unexpected wins. Five-bucket findings:

1. **2 confirmed V16 regressions**: R1 (Homepage upstream-deleted),
   R2 (/tasks 404 — was confirmed S78, parity check confirmed again)
2. **2 pre-existing defects worth fixing**: R3 (IRS 1099 always-broken),
   R5 (nginx /socket.io missing 2 headers)
3. **1 V16-only surface artifact** layered on pre-existing: R5 URI
   site-name appending (V16 client builds different URI)
4. **1 false alarm dropped**: R4 (frappe correctly rejecting query
   for non-existent Email Template field; my S78 query was wrong)
5. **~28 confirmed-parity rows** (schema/data match V13↔V16; user
   workflow parity still requires Phase D operator-watched batches)

Plus end-to-end fixes implemented for R1, R3, R5 (the operator's
"weeks of debugging" socketio defect — solved + ESACP template change
merged).

## Pre-flight

- Controller on `main`, clean
- sync_check (S78 carry): 45/10/2 expected
- Open ESACP at start: 65 (per S78 close-count)
- Open LSKB at start: 11 (per S78 close-count)
- dev02 V16 confirmed: frappe 16.18.3 / erpnext 16.19.1
- Topology recon for V13 standup:
  - dev01 had `v13-plus-edits` snapshot ready (V13 production-data + customizations)
  - dev03 not even a defined libvirt domain
  - toshy WG: confirmed saconsole is the WG hub (no toshy-level WG); shutting saconsole would break controller→dev02
  - toshy RAM: 15 GiB total, ~348 MiB free pre-resize
- Resize saconsole 4G → 2G live (`virsh setmem`, balloon working
  per dommemstat); freed ~2.5 GiB for dev01 boot
- Reverted dev01 to `v13-plus-edits` snapshot (memory state included;
  auto-started)
- dev02 went shut-off unexpectedly during dev01 revert (libvirt
  resource shuffle); restarted dev02
- dev01 V13 versions verified: frappe 13.58.22 / erpnext 13.55.2
- Both Chrome tabs ready: V13 `1456393545→1456393547` (operator
  relogin), V16 `1456393537`

## What happened

### Phase A — V13 lab standup

Steps 1-5 of the parity plan: saconsole shrink + dev01 V13 revert +
both Chrome tabs to login screens. Operator-typed Administrator logins
on both.

### Phase B — Bulk schema diff (Claude-alone)

One large JS round-trip per tab queried all 53 Agenda 00 customizations
via `frappe.db.get_value`. Resulting diff revealed surprising scale of
S77 enumeration drift:

- **6 of 19 CFs DON'T EXIST on V13** — they're V14+ stock Frappe
  additions (Communication-company, Custom DocPerm/DocPerm/DocShare-
  impersonate, Email Account-company, UTM Campaign-crm_campaign).
  Should leave Agenda 00 entirely.
- **10 of 15 PFs missing from V13** — V14+ materializes stock-with-
  UI-edits PFs as DB records; V13 stored them differently. Should
  leave Agenda 00.
- **Notification "for new fiscal year" subject** changed V13→V16
  (stock upstream change)
- **Web Form `request-to-delete-data` route+title** renamed V13→V16
  (stock upstream change, GDPR-clarity)

### Phase B+ — Critical regression vs always-broken probes

Hit V13 endpoints for each S78-flagged "V16 regression":
- `/` V13 → **HTTP 200** (Logichem branded homepage), V16 → 404
  → R1 confirmed regression
- `/tasks` V13 → **HTTP 200**, V16 → 404 → R2 confirmed regression
- `ejm` report V13 → **same 500** as V16 → R3 demoted to always-
  broken (operator decision: drop / fix)
- 3 bespoke PFs (FdI: Cotización, Factura ejemplo, OdV 2): all
  empty/null Jinja body on V13 too → always-broken on both

### Data parity sampled

- `Delivery Note-saldo_del_cliente`: 5 most-recent submitted DNs on
  each VM — **identical values** (0.01, 0.066, 0.121, 0.01, 0.029)
- `Sales Partner-supplier`: 5 partners on each — identical supplier
  links

### Operator critique on "demoted" framing

Operator pointed out that "V13 errors that migrate to V16 are still
errors in need of correction" — distinction is attribution, not action.
Re-framed into three buckets:
1. V16-introduced regression
2. Pre-existing defect, broken on V13 too (still warrants fix)
3. Not a defect (correct behavior)

Re-classification under this framing:
- R3 = bucket 2 (worth fixing — delete or fix the orphan template)
- R4 = bucket 3 (frappe correctly rejected my over-broad query)
- R5 = uncertain at first, then localized to bucket 2 (V14+ surface
  layer on pre-existing nginx config gap)

### R1 fix — Homepage Web Page recreation

Salvaged Homepage singleton values from V16 `tabSingles`
(company="Logichem Solutions S. A.", tag_line="Molecular Tensegrity",
description). Created `Web Page` with `route='home'` populated from
those values. `GET /` returns 200 with Logichem branding (was 404).

### R3 fix — IRS 1099 Form disabled

`frappe.client.set_value` to set `disabled=1` on the orphan Print
Format. Reversible. Prevents future accidental invocation of the
always-failing template.

### R5 root cause + fix (the weeks-of-debugging defect)

Investigation traced through:
- V13 client `get_host()` returns clean host; V16 appends `/sitename`
  as Socket.IO namespace (V14+ multi-tenant pattern)
- V16 client uses ESM `import { io }` so `io` not in global scope
- Both V13 + V16 server middlewares have IDENTICAL `host == origin`
  hostname-comparison check
- V13 dev01 socket.io ALSO disconnected — both VMs broken
- nginx config FILE (bench's `frappe-bench/config/nginx.conf`) HAS
  the correct `proxy_set_header Origin` + `X-Frappe-Site-Name`
  directives
- nginx ACTIVE config (`/etc/nginx/sites-available/dev0X.iridium.blue`,
  templated by ESACP ansible) was MISSING those two headers
- tcpdump on dev02 lo:9000 confirmed: upstream sees NO Origin header
- ESACP source: `platforms/kvm/templates/nginx_vhost.conf.j2:50-59`
  lacked the directives

Why this took the operator weeks to diagnose on the forums:
1. Bench's self-generated nginx.conf shows the correct directives —
   looking there shows everything OK
2. Forum advice conflates with CORS; "Invalid origin" sounds like
   CORS but isn't — it's frappe's internal host==origin equality check
3. Upgrading V13→V16 didn't fix it because the bug is in ESACP
   template, not in frappe code; the template was missing the
   directives on both VMs
4. The deployed config diverged from the source-of-truth (bench's
   file); only `sudo nginx -T` reveals the active loaded content

Fixes applied:
- Manual patch to both `/etc/nginx/sites-available/*.iridium.blue`
  files + `nginx -s reload` on dev01 + dev02
- ESACP template (`platforms/kvm/templates/nginx_vhost.conf.j2`)
  updated with the two missing directives + explanatory comment
  citing the frappe source location
- Filed ESACP#481 (the template fix), opened PR#482, T1+T3 +
  T2 verdicts both `approve`, squash-merged via `4784d88`
- ESACP#481 auto-closed via `fixes #481`

Verification:
- V16 dev02 socket.io after fix: `connected: true`, valid id
- V13 dev01 socket.io after fix: `connected: true`, valid id

### Umbrella issue filed: ESACP#480

"V13→V16 re-migration: defect catalog + scripted fixes + clean-run
acceptance (umbrella)" — supersedes ESACP#463 framing for the
structured-fixes phase. Catalog of R1-R5 findings, fix-script
specifications, acceptance criteria.

## Decisions

- **A/B parity testing** is the right methodology; was missing from
  S78. Operator-watched + Claude-alone tiers per checklist.
- **Three-bucket classification** (regression / pre-existing / not-a-
  defect) — operator framing improves on "demoted" euphemism.
- **R5 manual patch on both lab VMs** is OK because per
  `feedback_dev_vms_are_disposable.md` dev VMs are disposable. The
  template change is the durable fix.
- **R1 fix on dev02** is a JS-level Web Page creation; for production
  cutover the fix-script will live in the umbrella's pipeline integration.
- **Saconsole shrink** to 2 GiB is reversible (`virsh setmem
  saconsole 4194304 --live`); resized back at session close.
- **Leave dev01 V13 running** (4 GiB) for potential S80+ continued
  parity work; operator can shut down when no longer needed.
- **R5 fix as separate PR#482** rather than bundled with session-close
  doc commit (per 1:1:1 — substantive code change deserves own
  issue/branch/PR).

## Outputs

| Artifact | Repo | Status |
|---|---|---|
| Issue #480 (V13→V16 re-migration umbrella) | ESACP | open (deliberate; tracks remaining work) |
| Issue #481 (nginx socketio headers) | ESACP | closed via PR#482 |
| PR #482 / squash-commit `4784d88` | ESACP | merged 2026-05-25T12:57:42Z |
| Branch `feat/481-nginx-socketio-headers` | ESACP | merged, persists |
| Manual nginx patches on dev01 + dev02 active configs | (lab state) | applied + nginx reloaded |
| Plan file `v13-v16-parity-checklist.md` | `~/.claude/plans/` | seed for future parity walkthroughs |
| Plan file `v13-v16-schema-diff-report.md` | `~/.claude/plans/` | comprehensive findings |
| dev01 V13 reverted + running (4 GiB) | toshy | preserved post-session |
| Saconsole resized 4G→2G→4G (live, reversible) | toshy | restored |
| R3 fix on dev02 (IRS 1099 Form disabled=1) | (lab state) | applied |
| R1 fix on dev02 (Web Page route=home created) | (lab state) | applied |

## QA verdicts

- **T1+T3 combined on ESACP `86cd115`** (R5 template fix): `approve`,
  `hard_block: true`. No conditions.
- **T2 on PR#482** under v2.1 §2.2 carve-out: `approve`. All three
  conditions independently verified.
- **T5 (pre-issue-close) on #481**: auto via `fixes #481` in commit body.
- **Session-close T1+T3 on ESACP main**: _to be invoked next._

## Carry-forward (new from S79)

- **ESACP#480 umbrella** open — drives the V13→V16 re-migration
  fix-script catalog. Next sessions (Phase D walkthroughs, fix-script
  pipeline integration, dev01 ansible re-run) feed it.
- **dev01 V13 lab still running** — disposable; shut down when no
  longer needed. Snapshot `v13-plus-edits` persists for re-revert.
- **R2 fix not yet implemented** — `/tasks` 404 V16 regression; needs
  operator decision (rewrite tenant docs / nginx rewrite / accept).
- **Methodology lessons captured** (deferred memory file write for
  next session): API-level checks ≠ user-parity; console errors are
  tracking-time-asymmetric; opaque frappe.db errors mask real exception;
  self-induced vs organic conflation; deployed-config vs source-of-truth
  divergence pattern.
- **Phase D walkthrough batches** still pending — 28 confirmed-parity
  rows need operator-watched visual + domain confirmation.

## Carry-forward (unchanged from S78)

- S71 minutes backfill decision (still pending)
- ESACP#426 / #427 — pending operator pickup
- on_boarding branch — Junior owns
- LogiSoluMemory cross-repo cleanup (~28 stale `docs/` refs)
- ESACP#401 saconsole + dev02 intermittents
- LSKB#11 / #16 / #18 / #21 — Phase 2/3 follow-on
- LSKB#24 — Agenda 04 SPC doc gap
- LSKB#28 (3 bespoke PFs) — re-frame per S79 (always-broken, not regression)
- LSKB#30 — Agenda 00 LSV-spec backfill
- ESACP#440 — `snapShotVM` CLI bug (3rd encounter S78); ripe for S80
- ESACP#456 — V16 / 404; S79 confirmed regression + root cause; awaiting fix-script decision
- ESACP#472 — /tasks 404; S79 confirmed regression
- ESACP#473 — `ejm` report 500; S79 re-classified as always-broken-with-default-filters
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry
- `sync_check.sh:2 Mighty` (S58 TRIVIAL_FIXES)
- `tools/secrets.py +x` (S47 TRIVIAL_FIXES)
- MariaDB-10.6 default PS=OFF (S55 carry)
- Tablet WG sidebar (#383)
- ESACP#383 / #361

## Memory changes

None this session in `memory/` proper. Methodology lessons enumerated
in carry-forward; to be filed as a feedback memory in S80 (would
require its own session-close cycle if filed now without bundling).

## Counts

- ESACP open issues: **65 → 66** (+1 net: #480 + #481 filed, #481
  closed via merge; net = +1 from #480)
- LSKB open issues: **11 → 11** (unchanged this session)
- Sibling-tracker counts unchanged: ce_sri 6 / ce_sri_svc 2 /
  LogiSoluValidations 2 / BaRe 2
- dev02 state: V16 substrate now has 2 lab fixes applied (R1 Web
  Page, R3 PF disabled, R5 nginx). All reversible; pre-S78 snapshot
  retained.
- dev01 state: V13 lab live from `v13-plus-edits` snapshot + R5
  nginx patch applied (manual; will be lost on re-revert)
- Snapshots: dev02 unchanged (10 prior); dev01 reverted to existing
  snapshot, no new snapshots taken
- TRIVIAL_FIXES.md: unchanged (3 entries)

## Files committed (ESACP this session)

- PR#482 (squash-commit `4784d88`): `platforms/kvm/templates/nginx_vhost.conf.j2`
  +5 lines
- This session-close commit: S79 minutes + S80 next-agenda + qa-log
  S79 close-batch row

## Session classification

**1:1:1 discipline + substantive multi-defect investigation session**.
Substantive code change (R5 nginx template) went through proper
1:1:1 (issue #481 → branch → commit → PR → merge). Lab-state fixes
(R1 Web Page, R3 disabled PF) are dev02-disposable substrate changes
that will become scripted fixes in pipeline integration (#480 umbrella).

Not housekeeping-bundle. Not introspection-sidebar (no MEMORY.md
edits this session; carry-forward additive). Not umbrella-branch
(R5 fit single 1:1:1; #480 umbrella issue ≠ branch-topology umbrella
per CLAUDE.md).

Diff-based introspection-sidebar trigger: MEMORY.md untouched;
S80 carry-forward additive only (no attrition). Trigger NEGATIVE.
