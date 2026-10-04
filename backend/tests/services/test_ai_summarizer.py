from unittest.mock import patch, MagicMock
import pytest
import asyncio
import time

from app.services.ai_summarizer import summarize_bill, validate_summary_output, asummarize_bill
from app.utils.exceptions import AIModelError, BillTooLongError
from app.schemas.ai_summary import SummaryOutput

pytestmark_async = pytest.mark.asyncio
 
VALID_RAW_OUTPUT = {
    "summary_full": "This bill does X.",
    "pros": [{"point": "Improves Y", "section_reference": "Section 3(1)"}],
    "cons": [{"point": "May increase Z", "section_reference": "Section 7"}],
    "sectors_affected": ["agriculture"],
    "notes": None,
}


def _fake_summary_output():
    return SummaryOutput(
        summary_full="Fake summary.",
        pros=[{"point": "X", "section_reference": "Section 1"}],
        cons=[],
        sectors_affected=["agriculture"],
        notes=None,
    )

def _mock_tool_use_response(input_dict: dict):
    """Builds a fake Anthropic response shaped like a real tool_use reply."""
    block = MagicMock()
    block.type = "tool_use"
    block.input = input_dict
    response = MagicMock()
    response.content = [block]
    return response


@patch("app.services.ai_summarizer.client")
def test_summarize_bill_returns_valid_output_on_first_try(mock_client):
    mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)
    mock_client.messages.create.return_value = _mock_tool_use_response(VALID_RAW_OUTPUT)

    result = summarize_bill("Test Bill", "some bill text")

    assert result.summary_full == "This bill does X."
    mock_client.messages.create.assert_called_once()


@patch("app.services.ai_summarizer.client")
def test_summarize_bill_retries_on_invalid_output_then_succeeds(mock_client):
    mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)
    bad_output = {**VALID_RAW_OUTPUT, "sectors_affected": ["not_a_real_sector"]}
    mock_client.messages.create.side_effect = [
        _mock_tool_use_response(bad_output),   # first attempt fails validation
        _mock_tool_use_response(VALID_RAW_OUTPUT),  # second attempt succeeds
    ]

    result = summarize_bill("Test Bill", "some bill text", max_retries=1)

    assert result.summary_full == "This bill does X."
    assert mock_client.messages.create.call_count == 2


@patch("app.services.ai_summarizer.client")
def test_summarize_bill_raises_after_exhausting_retries(mock_client):
    mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)
    bad_output = {**VALID_RAW_OUTPUT, "sectors_affected": ["not_a_real_sector"]}
    mock_client.messages.create.return_value = _mock_tool_use_response(bad_output)

    with pytest.raises(AIModelError):
        summarize_bill("Test Bill", "some bill text", max_retries=2)

    assert mock_client.messages.create.call_count == 3  # 1 initial + 2 retries


@patch("app.services.ai_summarizer.client")
def test_summarize_bill_raises_bill_too_long_before_calling_create(mock_client):
    mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=999_999)

    with pytest.raises(BillTooLongError):
        summarize_bill("Huge Bill", "massive text" * 100000)

    mock_client.messages.create.assert_not_called()  # should never reach the actual call

@pytest.mark.asyncio
@patch("app.services.ai_summarizer.summarize_bill")
async def test_asummarize_bill_does_not_block_event_loop(mock_summarize):
    """
    Proves the specific property asyncio.to_thread exists for: two
    concurrent calls should run ALONGSIDE each other (interleaved on
    separate threads), not block the event loop and serialize. If someone
    later 'simplifies' asummarize_bill back to a direct synchronous call,
    this test should fail.
    """
    def slow_summarize(title, text, max_retries=2):
        time.sleep(0.2)  # simulates a blocking call
        return _fake_summary_output()

    mock_summarize.side_effect = slow_summarize

    start = time.monotonic()
    await asyncio.gather(
        asummarize_bill("Bill A", "text a"),
        asummarize_bill("Bill B", "text b"),
    )
    elapsed = time.monotonic() - start

    # If truly concurrent (threaded), ~0.2s total, not ~0.4s serialized.
    # Generous threshold to avoid CI flakiness, but tight enough to catch
    # a regression back to blocking behavior.
    assert elapsed < 0.35