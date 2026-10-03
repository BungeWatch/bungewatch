from unittest.mock import patch, MagicMock
import pytest

from app.services.ai_summarizer import summarize_bill, validate_summary_output
from app.utils.exceptions import AIModelError, BillTooLongError

VALID_RAW_OUTPUT = {
    "summary_full": "This bill does X.",
    "pros": [{"point": "Improves Y", "section_reference": "Section 3(1)"}],
    "cons": [{"point": "May increase Z", "section_reference": "Section 7"}],
    "sectors_affected": ["agriculture"],
    "notes": None,
}


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