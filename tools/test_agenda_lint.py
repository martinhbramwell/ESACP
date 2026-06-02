"""Colocated test for agenda_lint bare-CLOSED-ref detection (#560)."""

from tools.agenda_lint import bare_closed_refs

STATES = {483: "CLOSED", 541: "CLOSED", 456: "OPEN", 560: "OPEN"}


def test_bare_closed_ref_is_flagged():
    text = "- remaining R6 family under #483 — walkthrough first"
    flagged = bare_closed_refs(text, STATES)
    assert len(flagged) == 1
    assert flagged[0][1] == 483


def test_stamped_closed_ref_is_not_flagged():
    text = "- R6 (#483) DONE — deployed+probed S81"
    assert bare_closed_refs(text, STATES) == []


def test_strikethrough_stamp_suppresses_flag():
    text = "- ~~#483 R6 nginx parity~~ resolved"
    assert bare_closed_refs(text, STATES) == []


def test_open_ref_is_never_flagged():
    text = "- #456 faithful homepage rebuild; scope undecided"
    assert bare_closed_refs(text, STATES) == []


def test_cross_repo_ref_is_skipped():
    # LSKB#483 must not be checked against ESACP state even though 483 is CLOSED.
    text = "- LSKB#483 Phase-2 follow-on still open upstream"
    assert bare_closed_refs(text, STATES) == []


def test_multiple_refs_one_line_mixed_states():
    # Bare line: closed #483 flagged, open #456 not; no stamp present.
    text = "- carry #483 and #456 forward"
    flagged = bare_closed_refs(text, STATES)
    assert [f[1] for f in flagged] == [483]


def test_lineno_is_reported():
    text = "header\n\n- bare #541 rebrand underway"
    flagged = bare_closed_refs(text, STATES)
    assert flagged[0][0] == 3
