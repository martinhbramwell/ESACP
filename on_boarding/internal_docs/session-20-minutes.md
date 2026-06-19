# Session 20 minutes — 2026-06-18

**Branch:** `on_boarding` (Junior). **Started as:** S20 agenda ([#712](https://github.com/martinhbramwell/ESACP/issues/712)) — validate the goal-staged router (`first_visit_002.md`). **Became:** an operator-driven redesign of how the welcome is *rendered* and how the router *frames itself*, ending with a transparent, inline-Visualizer entry page.

## The arc
Operator raised two defects against `first_visit_002.md`: (1) the departing-visitor continuity synopsis was dropped; (2) welcome formatting (juxtaposition lines, a centred "free/free/not" diamond, non-question asks). Chasing the diamond surfaced a chain of discoveries that reshaped the page three times (`002→003→004→005`).

## ESSENTIAL KNOWLEDGE — carry forward
1. **claude.ai has two render paths** (memory `project_claudeai_artifacts_render_html`): the **chat window** renders only basic Markdown — raw HTML / centring is **stripped**. A **Visualizer** renders HTML/SVG **inline in the conversation** (what the welcome wants). An **Artifact** is the **side panel** / downloadable file — what the word "artifact" produces, and the wrong tool here.
2. **Visualizer trigger that works:** *"Render this HTML inline using the Visualizer; do not create an artifact or open a side panel — show it directly in the chat."* Verified live (chat `af88108c`).
3. **The Mode-A router must be TRANSPARENT** (memory `project_mode_a_router_transparent`): covert classification + impersonation + silent-fetch framing makes a well-aligned model **refuse the whole role-play** (chat `ab19d47d`). It was **intermittent** (Test010 complied on identical framing), so the covert design was fragile. Fix: Claude openly acting as Nick; open questions; ordinary tool-use dispatch.
4. **Inside a render** (Visualizer or artifact-preview): centring works, `Georgia` serif works, **external images are BLOCKED** (`<img src=…>` → broken-image), **inline `<svg>` works**. Brand colours: green `#059669`, gold `#D97706` — legible on white **and** black; leave body `color` unset so text adapts to theme.
5. **Inline SVG logo was dropped** — render speed was unacceptable. Welcome currently has no logo.
6. **Egress-cache filename bump on every republish** (`project_claudeai_free_fetch_constraints`): `002→003→004→005` this session.
7. **Promoted S20 (#724):** the landing snippet now points at `first_visit_005.md` (transparent, inline-Visualizer) — on **one** clean acceptance run. `first_dialog.md` (v4) is dereferenced/obsolete. Robustness confirmation continues S21 (#723) and now gates a possible **rollback**, not a promotion.

## FAILED EXPERIMENTS / DEAD ENDS — do not repeat
1. **"Render as an artifact"** → a side-panel downloadable "Code · HTML" file (Test010), not the inline visual. Use a **Visualizer**.
2. **Logo via external URL** → blocked by the sandbox CSP (broken-image + alt text). Inline the SVG, or drop it.
3. **Inline SVG logo** → renders, but astonishingly slow → dropped for now.
4. **Covert-classification router** (`003`/`004`, "you are Nick / never tell them you're classifying / silently fetch") → intermittent model refusal as third-party prompt-injection. Redesigned transparent (`005`, #719).
5. **"Render the HTML as part of your response"** in the chat text → impossible; chat strips HTML. The visual must live in a Visualizer/artifact container.
6. **Don't `--no-gpg-sign`; don't re-roll fresh chats until one complies** — the latter games a safety behaviour and leaves the intermittency for real visitors.

## Process notes
- Four substantive 1:1:1 cycles, each its own issue→branch→PR→T2-QA→merge: [#715](https://github.com/martinhbramwell/ESACP/issues/715)→PR [#716](https://github.com/martinhbramwell/ESACP/pull/716) (artifact card), [#717](https://github.com/martinhbramwell/ESACP/issues/717)→PR [#718](https://github.com/martinhbramwell/ESACP/pull/718) (Visualizer), [#719](https://github.com/martinhbramwell/ESACP/issues/719)→PR [#720](https://github.com/martinhbramwell/ESACP/pull/720) (transparent), [#724](https://github.com/martinhbramwell/ESACP/issues/724)→PR [#725](https://github.com/martinhbramwell/ESACP/pull/725) (promote landing entry → `005` + bold "What this does:"). All live-verified (curl + Jekyll deploys green). T2 advisory per `project_on_boarding_trunk_vs_default`; #724 closed T5.
- esacp-qa caught a **missing Co-Authored-By trailer** on the #716 commit (amended before merge); other two clean. GPG pinentry cancelled once → operator tty-unlock (`feedback_gh_signing_pinentry_timeout`).
- **A wrong-turn worth recording:** Junior initially dismissed claude.ai's description of its own Visualizer feature as a probable hallucination — it is real. Operator corrected with a claude.ai transcript. Don't conflate "verify before trusting model self-report" with "dismiss a real feature."
- Browser-MCP drive note: the first `type` after a fresh `claude.ai/new` navigation lands empty (focus not yet in the box) — click the input by coordinate and retype.

## State at close
| | |
|---|---|
| **LIVE entry (promoted S20, #724)** | landing snippet → `first_visit_005.md` (transparent, inline-Visualizer; acceptance ×1) |
| **`first_dialog.md`** | dereferenced/obsolete — cleanup pending (S21; still cross-referenced by `install_planner.md`) |
| **Open — acceptance robustness pending** | #715, #717, #719 (one clean run; need 2+ confirmatory cold runs before T5 close) |
| **Open — carry-forward** | [#721](https://github.com/martinhbramwell/ESACP/issues/721) continuity synopsis (defect #1), [#710](https://github.com/martinhbramwell/ESACP/issues/710) staging cleanup, [#511](https://github.com/martinhbramwell/ESACP/issues/511)/[#448](https://github.com/martinhbramwell/ESACP/issues/448) deferred |
| **Likely gap (S21 #2)** | Type pages `visitor/{curious,owner_general,owner_specific}.md` may still carry covert framing — audit + transparent pass |
| **Next agenda** | [#723](https://github.com/martinhbramwell/ESACP/issues/723) (Session 21) |

Design detail: [`mode-a-router-design.md`](mode-a-router-design.md).
