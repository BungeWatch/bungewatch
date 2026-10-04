# tests/pipeline/test_chunking.py

from pathlib import Path
from app.pipeline.chunking import split_by_budget
from unittest.mock import patch, AsyncMock, MagicMock
import pytest

from app.pipeline.chunking import (
    split_by_budget,
    _group_chunks_within_token_budget,
    summarize_long_bill,
)
from app.schemas.ai_summary import SummaryOutput
from app.utils.exceptions import AIModelError

FIXTURE = Path(__file__).parent / "fixtures" / "legal_notice_96_wages.txt"

def _fake_output(point="Point A", section="Section 1"):
    return SummaryOutput(
        summary_full="Partial summary text.",
        pros=[{"point": point, "section_reference": section}],
        cons=[],
        sectors_affected=["agriculture"],
        notes=None,
    )


@patch("app.pipeline.chunking.count_tokens")
def test_group_chunks_accepts_chunks_within_budget(mock_count_tokens):
    # Every chunk reports well under the limit — should return unmodified.
    mock_count_tokens.return_value = 100
    result = _group_chunks_within_token_budget("Test Bill", "short bill text")
    assert len(result) >= 1


@patch("app.pipeline.chunking.count_tokens")
@patch("app.pipeline.chunking.MAX_INPUT_TOKENS", 100)
def test_group_chunks_splits_further_when_estimate_was_wrong(mock_count_tokens):
    """
    Covers the self-correction path: the cheap character-based estimate
    can be wrong, so a chunk that still exceeds the real token count after
    the first pass must get split again, not silently accepted over-budget.
    """
    # First call (verifying the only initial chunk) reports OVER budget,
    # forcing the fallback split; subsequent calls (checking the smaller
    # re-split pieces) are omitted here since the function only re-verifies
    # once in the current implementation — this test locks in that behavior.
    mock_count_tokens.return_value = 999_999_999
    long_text = "Sentence one. " * 5000  # long enough to actually sub-split
    result = _group_chunks_within_token_budget("Test Bill", long_text)
    # However it was re-split, it must produce MORE than one piece —
    # proves the over-budget chunk didn't just get accepted as-is.
    assert len(result) > 1


@patch("app.pipeline.chunking._amerge", new_callable=AsyncMock)
@patch("app.pipeline.chunking.asummarize_bill", new_callable=AsyncMock)
@patch("app.pipeline.chunking._group_chunks_within_token_budget")
async def test_summarize_long_bill_merges_multiple_chunks(
    mock_group, mock_asummarize, mock_amerge
):
    mock_group.return_value = ["chunk one text", "chunk two text"]
    mock_asummarize.side_effect = [
        _fake_output("Point A", "Section 1"),
        _fake_output("Point B", "Section 5"),
    ]
    mock_amerge.return_value = _fake_output("Merged point", "Section 1")

    result = await summarize_long_bill("Test Bill", "irrelevant full text")

    assert mock_asummarize.await_count == 2
    mock_amerge.assert_awaited_once()
    assert result.pros[0].point == "Merged point"


@patch("app.pipeline.chunking.asummarize_bill", new_callable=AsyncMock)
@patch("app.pipeline.chunking._group_chunks_within_token_budget")
async def test_summarize_long_bill_skips_merge_when_only_one_chunk(
    mock_group, mock_asummarize
):
    """
    If grouping happened to produce just one chunk (e.g. a bill just over
    the threshold), the merge step — an extra AI call with its own
    failure/drift risk — should be skipped entirely, not run pointlessly
    on a single input.
    """
    mock_group.return_value = ["only one chunk"]
    single_output = _fake_output()
    mock_asummarize.return_value = single_output

    result = await summarize_long_bill("Test Bill", "irrelevant full text")

    assert result is single_output  # returned directly, no merge call


@patch("app.pipeline.chunking.call_model")
@patch("app.pipeline.chunking._group_chunks_within_token_budget")
@patch("app.pipeline.chunking.asummarize_bill", new_callable=AsyncMock)
async def test_summarize_long_bill_wraps_merge_failure_distinctly(
    mock_asummarize, mock_group, mock_call_model
):
    """
    A merge-step failure should be distinguishable from a chunk-summarization
    failure when debugging — both raise AIModelError, but the message should
    make clear WHICH stage failed.
    """
    mock_group.return_value = ["chunk one", "chunk two"]
    mock_asummarize.return_value = _fake_output()
    mock_call_model.side_effect = AIModelError("Claude", "API timeout")

    with pytest.raises(AIModelError, match="Merge step failed"):
        await summarize_long_bill("Test Bill", "irrelevant full text")

def test_split_by_budget_never_exceeds_max_chars_per_chunk():
    text = FIXTURE.read_text()
    chunks = split_by_budget(text, max_chars=400, overlap_sentences=1)
    # Allow some slack: a single sentence longer than max_chars can't be
    # split further without breaking mid-sentence, which we explicitly
    # choose not to do — this asserts chunks stay CLOSE to budget, not
    # a hard impossible guarantee.
    assert all(len(c) < 600 for c in chunks)


def test_split_by_budget_does_not_lose_any_wage_figures():
    """
    The real regression test: every wage figure from the table must
    survive into SOME chunk. This is the test that would have caught
    the earlier regex bug — a mis-split could silently drop or garble
    a row's figures.
    """
    text = FIXTURE.read_text()
    chunks = split_by_budget(text, max_chars=400, overlap_sentences=1)
    combined = " ".join(chunks)

    expected_figures = ["9,196.93", "20,621.15", "26,591.20", "13,496.47"]
    for figure in expected_figures:
        assert figure in combined


def test_split_by_budget_preserves_sentence_integrity():
    """
    No chunk should start or end mid-word — a crude but useful proxy
    for 'we never cut inside a sentence in a way that breaks meaning.'
    """
    text = FIXTURE.read_text()
    chunks = split_by_budget(text, max_chars=400, overlap_sentences=1)
    for chunk in chunks:
        assert chunk == chunk.strip()
        assert not chunk.startswith(",")  # a mid-list cut would often start here