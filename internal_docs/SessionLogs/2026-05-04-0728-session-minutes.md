# 2026-05-04 0728 — Session 6 minutes (#343 diagnosis)

## Session shape

- **Started**: 2026-05-03 evening, ran across midnight into 2026-05-04 ~07:28 EDT
- **Branch**: `main` throughout (diagnosis-only; no substantive code changes landed)
- **Working tree at session-end**: this minutes/agenda commit only
- **Stated objective at session start**: none — operator surfaced #343 mid-session as the de-facto objective
- **Actual objective**: diagnose the dev01 → SRI Pruebas ECONNRESET that #343 was opened to track, narrow to a confirmable root cause

## What happened

### Pre-flight (start of session)

- `sync_check.sh` — 45 ✅ / 9 ⚠ / 2 ❌, both ❌ are dev02 dormant carve-outs (expected). No new failures.
- Open issues: 29.
- Branch clean at `ec4010c`, post-#341 verdict-layer landing.

### #343 opened, then immediately corrected

Operator presented two captured logs (`$BESPOKE_ROOT/tmp/{erp.<company>,dev01.iridium.blue}/SRI_submit_log.txt`) — production succeeded with `RECIBIDA`, dev01 failed with `AxiosError: read ECONNRESET`, both within ~43 minutes of each other on 2026-05-03. Side-by-side falsified the long-held assumption (carried in closed issue #146) that the SRI Pruebas server was at fault.

Issue **#343** opened: `bug(network): dev01 lab egress to SRI Pruebas fails with ECONNRESET while production succeeds at same time`. Five candidate root causes listed.

Operator caught a fabricated reproduction command in the issue body (`bench execute ce_sri.api.submit_test_invoice`). Verified against the codebase: no such method exists; the real entry point is the whitelisted `comprobante_electronico` method called from the Sales Invoice form button (`ce_sri/comprobante_electronico/doctype/comprobante_electronico/comprobante_electronico.py:10`). #343 body edited in place with the corrected reproduction paths; edit-note comment posted; new feedback memory written: `feedback_no_invented_commands.md`. Index entry added under Critical Rules in `MEMORY.md`.

### Falsifying the original five hypotheses

Authorised diagnostic phase. Phase-1 probes (read-only, from controller via SSH to dev01-erp and toshy):

- dev01 routes SRI traffic via **`enp1s0` libvirt NAT, not `wg0`** — WG mtu 1420 is irrelevant to SRI traffic. Hypothesis A (WG MTU blackhole) dead at this point.
- TLS handshakes from dev01 to celcer.sri.gob.ec succeed; cert chain verifies; PMTU 1492 (PPPoE on home router); GET to `?wsdl` returns 200/4118 B cleanly.

Phase-2 probes (curl POSTs of varying body sizes from dev01 and from toshy):

- 4-byte POST → `500 SOAP fault "Error reading XMLStreamReader"` from both sides. Network path good.
- **18 668-byte random body POST → same SOAP fault, same ~0.7 s latency**. Larger than the 14 468-byte payload that fails. No RST.

Implication: hypotheses A, B, C, D, E from #343 all falsified. The defect is content-tied — random bytes get a clean SOAP response, signed envelope hard-RSTs.

### Operator's reframe — long-term, devXX-only, prod-clean

Operator clarified: the ECONNRESET has been a hard fault on every devXX submission attempt for weeks. Production succeeds reliably. So not a transient. Question reframed as *"why does SRI reject submissions from dev01.iridium.blue but not from erp.\<company-domain\>?"*

Two interpretations of "identical response" were possible (SOAP fault vs ECONNRESET). Operator confirmed interpretation B: ECONNRESET on every dev01 attempt.

### Operator's investigation — `console.dir(bundle)` artefact

Operator had already enabled diagnostic logging in `sendInvoice.js` (lines 55-60, mirrored on prod and dev01). Captured production log shared, showing the **complete** SOAP envelope — full base64 envelope including X509Certificate and signature value, not truncated. dev01's log showed truncation at exactly 10 000 chars (`'... 4468 more characters`).

Same code, different output → **different Node runtime defaults for `util.inspect.maxStringLength`**. That's a runtime fingerprint. Diagnosis pivoted to runtime-version mismatch.

### G1 confirmed via `node --version`

| Side | Node | OpenSSL | llhttp | Notes |
|---|---|---|---|---|
| erpls (✅) | **14.21.3** | **1.1.1t** | 2.1.6 | EOL'd April 2023; SRI submissions reliable |
| dev01 (❌) | **18.20.8** | **3.0.16** | 6.1.1 | Fresh-ish; SHA-1 deprecated in OpenSSL 3.0 default |

Four Node majors apart. OpenSSL 1.1.1 → 3.0. `http`/`https` → `undici`. Likely proximate cause: OpenSSL 3.0's stricter signature-scheme handling for SHA-1 (the XAdES envelope signs with `xmldsig#rsa-sha1`), or `undici`'s body framing differing in a way SRI's edge RSTs.

Curl from dev01 worked because curl uses the system OpenSSL, not Node's bundled OpenSSL — that explains why our Phase-2 probes didn't reproduce the failure.

### Mission framing recognised

V14's bench/build chain almost certainly requires Node ≥ 16. So lab is currently broken on Node 18; production is OK on Node 14; **V14 cutover would re-surface the identical break on production**. The strategic fix is modernising `ce_sri_svc` for Node 18+/OpenSSL 3.0. The short-term lab fix is pinning dev01 to Node 14.21.3 to match prod.

### Plan written, implementation deferred

Plan at `~/.claude/plans/issue-343-sri-econnreset.md`. Key shape:

- New probe `ce_sri_svc/diagnostics/sri_probe.js` — standalone Node script, POSTs a SOAP envelope file to SRI, prints one-line outcome (RECIBIDA / DEVUELTA / SOAP_FAULT / ECONNRESET / OTHER), exit-codes accordingly.
- Test fixture: a previously-submitted production envelope (extracted from operator's shared log, secuencial 289). Stored at `ce_sri_svc/diagnostics/fixtures/`, **gitignored** (operator call: keep local-only).
- Replicate prod runtime on dev01 via `nvm install 14.21.3` (alongside Node 18, reversible).
- Run probe under both versions; predicted result is Node-14 returns `DEVUELTA` (duplicate, accepted at app layer), Node-18 returns `ECONNRESET`.
- On confirmation: PR the probe to `ce_sri_svc`, file sibling issue for the V14-prep modernisation.

Operator approved plan; deferred implementation to a fresh session for cleanliness.

## Substantive findings recorded

- **#343 body** corrected with real reproduction paths (UI / direct ce_sri_svc / network probes).
- **#343 comment** posted with G1 diagnosis update + plan-file pointer.
- **`feedback_no_invented_commands.md`** written; indexed in MEMORY.md.
- **`~/.claude/plans/issue-343-sri-econnreset.md`** written.
- Falsified earlier hypothesis (closed issue #146's "SRI server dropped the connection") — superseded by today's evidence.

## Verdict-layer activity (#341)

This was a diagnosis-only session. Triggers actually fired:

- `gh issue create` (opened #343) — not a verdict trigger per `internal_docs/qa-contract.md` §5.
- `gh issue edit` (corrected #343 body) — not a trigger.
- `gh issue comment` ×2 (edit-note on #343, G1 diagnosis on #343) — not triggers.
- `Write` to `~/.claude/plans/`, `~/.claude/projects/.../memory/`, `MEMORY.md` — outside repo, not commit-bound.
- This minutes + agenda commit at session-end — **commit trigger fires**, advisory verdict.

No merge / push / destructive op / `gh issue close` triggers fired this session. qa-log entry deferred to the post-implementation-session batch (the next session will produce more substantial verdict activity worth row-batching).

## Files at session-end

- `internal_docs/SessionLogs/2026-05-04-0728-session-minutes.md` — this file
- `internal_docs/SessionLogs/2026-05-04-0728-next-agenda.md` — next-session agenda
- `~/.claude/projects/.../memory/feedback_no_invented_commands.md` — already written mid-session
- `~/.claude/projects/.../memory/MEMORY.md` — already updated mid-session with one new line
- `~/.claude/plans/issue-343-sri-econnreset.md` — already written mid-session

## Open issues delta

- **Opened**: #343 (this session).
- **Closed**: none.
- **Updated**: #343 (twice — body correction + G1 diagnosis comment).
- **Total open**: 30 (was 29 at session start).

## Session-end audit (retrospective)

After the initial close commit (`77a6534`), a session-end audit pass against the SESSION-CLOSE AUDIT hook surfaced one durable-home gap:

- **#146 had no backlink comment to #343.** The earlier attribution in #146 ("remote SRI test server dropped the TLS connection") had been documented as superseded inside the #343 body and inside these minutes, but #146 itself was not annotated. Posted a supersession comment on #146 ([`#146 comment-4370733431`](https://github.com/martinhbramwell/ESACP/issues/146#issuecomment-4370733431)) cross-linking to #343 so future searches landing on #146 reach the active diagnosis.

Other forward-tense items in the session resolved without further action: all conditional next-session work captured in `~/.claude/plans/issue-343-sri-econnreset.md` and the next-session agenda; all in-session promises executed (issue body edit, edit-note comment, G1 diagnosis comment, plan written, memory `feedback_no_invented_commands.md` written and indexed, runtime probes run on dev01 and toshy, plan + minutes + agenda committed).

No PRs were opened this session.

Issues referenced and their durable-home status after audit:

| Issue | Findings posted to issue itself? |
|---|---|
| #343 | ✅ Body corrected + 2 comments (edit-note, G1 diagnosis) |
| #146 | ✅ Supersession backlink comment posted post-audit |
| #341, #163, #311, #312, #330, #331, #306, #307, #213, #238, #243, #188 | n/a — referenced as backlog only, no new findings |
