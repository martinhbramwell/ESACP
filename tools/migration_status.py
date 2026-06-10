#!/usr/bin/env python3
"""Migration status probe (S0, internal_docs/MIGRATION_PLAN.md).

The mechanical "where are we" for the V13->V15->V16 push.  Prints:

  1. the recorded structural-vs-functional split (decided S10 — DO NOT re-ask);
  2. catalogue coverage — the structural/behavioural bar, counted live from
     LogiSoluValidations' customizations_catalogue.yml;
  3. every DONE step's proof command, re-executed — a regressed proof reopens
     the step (proof method, MIGRATION_PLAN.md);
  4. (opt-in, --bench HOST) the live structural A/B audit against a bench.

Without --bench it is offline and fast — safe to run as a SessionStart hook.
The audit (which SSHes to a bench) is opt-in so session start never blocks on it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.bespoke_root import BESPOKE_ROOT  # noqa: E402

CATALOGUE = (
    BESPOKE_ROOT / "LogiSoluValidations" / "audit" / "customizations_catalogue.yml"
)
PROOFS = REPO / "internal_docs" / "migration_proofs"

SPLIT = """\
Recorded structural-vs-functional split (decided S10 — DO NOT re-ask):
  structural  → property setters, custom fields/docperms, translations,
                in-place core edits, print formats — runnable per-leg bar,
                checked by tools/customisation_audit/ A/B vs the catalogue.
  behavioural → staffer workflow sections A-H — operator-paced, a hard gate
                before the real cutover, checked by LogiSoluValidations specs."""


# ── pure cores (offline-testable) ───────────────────────────────────────────


def catalogue_coverage(cat: dict) -> dict:
    """Count the catalogue's coverage bar: entries, operator sign-off, sections."""
    entries = cat.get("entries", []) or []
    sections: dict[str, int] = {}
    for e in entries:
        sections[e.get("suite_section", "?")] = (
            sections.get(e.get("suite_section", "?"), 0) + 1
        )
    return {
        "total": len(entries),
        "confirmed": sum(1 for e in entries if e.get("operator_confirmed") is True),
        "tbd": sum(
            1 for e in entries if e.get("business_relevance") in (None, "TBD")
        ),
        "sections": dict(sorted(sections.items())),
    }


def parse_proof_log(text: str) -> dict:
    """Extract {step, command, verdict} from a migration_proofs/<id>.log file."""

    def field(label: str) -> str:
        m = re.search(rf"^{label}:\s*(.+)$", text, re.M)
        return m.group(1).strip() if m else ""

    return {
        "step": field("STEP"),
        "command": field("PROOF COMMAND"),
        "verdict": "PASS" if re.search(r"^PASS\b", text, re.M) else "FAIL",
    }


# ── thin I/O shell ──────────────────────────────────────────────────────────


def _load_catalogue() -> dict | None:
    if not CATALOGUE.exists():
        return None
    return yaml.safe_load(CATALOGUE.read_text())


def _proof_logs() -> list[Path]:
    return sorted(p for p in PROOFS.glob("*.log"))


def _rerun(cmd: str) -> tuple[bool, str]:
    r = subprocess.run(
        cmd, shell=True, cwd=REPO, capture_output=True, text=True, timeout=120
    )
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _print_coverage() -> None:
    cat = _load_catalogue()
    if cat is None:
        print(f"  catalogue: NOT FOUND at {CATALOGUE} (is BESPOKE_ROOT set?)")
        return
    cov = catalogue_coverage(cat)
    print(
        f"  catalogue: {cov['total']} entries — "
        f"{cov['confirmed']} operator_confirmed, {cov['tbd']} business_relevance=TBD"
    )
    print(f"  sections: {cov['sections']}")


def _print_proofs() -> None:
    logs = _proof_logs()
    if not logs:
        print("  no DONE steps yet — ledger is empty.")
        return
    for log in logs:
        rec = parse_proof_log(log.read_text())
        if not rec["command"]:
            print(f"  {log.name}: no PROOF COMMAND line — cannot re-verify")
            continue
        ok, _ = _rerun(rec["command"])
        glyph = "✅" if ok else "❌ REGRESSED — reopen"
        print(f"  {glyph}  {rec['step'] or log.name}  ($ {rec['command']})")


def _run_audit(bench: str) -> int:
    from tools.customisation_audit.runner import run_audit

    report = run_audit(bench, str(REPO))
    drifts = report.get("drifts", report)
    print(f"  audit on {bench}: {len(drifts) if hasattr(drifts, '__len__') else '?'} drifts")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="V13->V15->V16 migration status probe")
    ap.add_argument("--bench", help="run the live structural A/B audit on this host")
    args = ap.parse_args()

    print("══ Migration status — V13 → V15 → V16 ══")
    print(SPLIT)
    print("── catalogue coverage ──")
    _print_coverage()
    print("── DONE-step proofs (re-verified) ──")
    _print_proofs()
    if args.bench:
        print("── live structural A/B audit ──")
        return _run_audit(args.bench)
    return 0


if __name__ == "__main__":
    sys.exit(main())
