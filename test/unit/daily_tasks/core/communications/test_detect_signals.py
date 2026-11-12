"""Responsibility: Prove signal phrases are detected on word boundaries, casefolded and negation-aware.
Public interface:
+-- test_detect_signals_partial_word_or_negation_returns_nothing(text)
+-- test_detect_signals_quote_is_the_sentence_containing_the_phrase()
+-- test_detect_signals_repeated_phrase_is_reported_once()
`-- test_detect_signals_status_phrase_returns_kind_and_phrase(text, expected)

Signal word classification over short email and chat snippets.
"""

import pytest

from daily_tasks.core.communications import detect_signals


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Done! PR merged.", (("completion", "done"), ("completion", "merged"))),
        ("Verification COMPLETED this morning", (("completion", "completed"),)),
        ("Legal says we are unblocked", (("completion", "unblocked"),)),
        ("Ticket resolved upstream", (("completion", "resolved"),)),
        ("Still blocked on the vendor", (("blocked", "blocked"),)),
        ("I'm stuck, waiting  on legal", (("blocked", "stuck"), ("blocked", "waiting on"))),
        ("@jordan Can you review the PR?", (("request", "can you"),)),
    ],
)
def test_detect_signals_status_phrase_returns_kind_and_phrase(text: str, expected: tuple[tuple[str, str], ...]) -> None:
    assert tuple((signal.kind, signal.phrase) for signal in detect_signals(text)) == expected


@pytest.mark.parametrize(
    "text",
    ["The abandoned branch", "Undone work", "pre-merged draft", "It is not done yet", "We aren't blocked", ""],
)
def test_detect_signals_partial_word_or_negation_returns_nothing(text: str) -> None:
    assert detect_signals(text) == ()


def test_detect_signals_quote_is_the_sentence_containing_the_phrase() -> None:
    signals = detect_signals("Hi Jordan,\nThe Slack connector PR is merged. Thanks!")

    assert [signal.quote for signal in signals] == ["The Slack connector PR is merged"]


def test_detect_signals_repeated_phrase_is_reported_once() -> None:
    assert len(detect_signals("done. done. DONE.")) == 1
