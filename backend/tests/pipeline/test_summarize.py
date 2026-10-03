from unittest.mock import patch, MagicMock
from uuid import uuid4
import pytest

from app.pipeline.summarize import run_summarization_for_bill
from app.utils.exceptions import BillTooLongError, AIModelError, NotFoundError
from app.schemas.ai_summary import SummaryOutput


def _fake_summary_output():
    return SummaryOutput(
        summary_full="This bill does X.",
        pros=[{"point": "Improves Y", "section_reference": "Section 3(1)"}],
        cons=[{"point": "May increase Z", "section_reference": "Section 7"}],
        sectors_affected=["agriculture"],
        notes=None,
    )


@patch("app.pipeline.summarize.insert_draft_summary")
@patch("app.pipeline.summarize.summarize_bill")
@patch("app.pipeline.summarize.find_bill_by_id")
def test_run_summarization_creates_draft_on_success(mock_find_bill, mock_summarize, mock_insert):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Test Bill", reviewed_text=MagicMock(text="bill text here"))
    mock_find_bill.return_value = bill
    mock_summarize.return_value = _fake_summary_output()
    mock_insert.return_value = MagicMock(id=uuid4(), version=1)

    result = run_summarization_for_bill(db, bill.id)

    mock_summarize.assert_called_once_with("Test Bill", "bill text here")
    mock_insert.assert_called_once()
    assert result is not None


@patch("app.pipeline.summarize.find_bill_by_id")
def test_run_summarization_skips_bill_with_no_reviewed_text(mock_find_bill):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), reviewed_text=None)
    mock_find_bill.return_value = bill

    result = run_summarization_for_bill(db, bill.id)

    assert result is None  # explicit no-op, not an error


@patch("app.pipeline.summarize.summarize_bill")
@patch("app.pipeline.summarize.find_bill_by_id")
def test_run_summarization_reraises_bill_too_long(mock_find_bill, mock_summarize):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Huge Bill", reviewed_text=MagicMock(text="massive text"))
    mock_find_bill.return_value = bill
    mock_summarize.side_effect = BillTooLongError(token_count=999999, limit=150000)

    with pytest.raises(BillTooLongError):
        run_summarization_for_bill(db, bill.id)


@patch("app.pipeline.summarize.summarize_bill")
@patch("app.pipeline.summarize.find_bill_by_id")
def test_run_summarization_reraises_ai_model_error(mock_find_bill, mock_summarize):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Test Bill", reviewed_text=MagicMock(text="bill text"))
    mock_find_bill.return_value = bill
    mock_summarize.side_effect = AIModelError("Claude", "validation failed after retries")

    with pytest.raises(AIModelError):
        run_summarization_for_bill(db, bill.id)


@patch("app.pipeline.summarize.find_bill_by_id")
def test_run_summarization_propagates_not_found(mock_find_bill):
    db = MagicMock()
    mock_find_bill.side_effect = NotFoundError("Bill", uuid4())

    with pytest.raises(NotFoundError):
        run_summarization_for_bill(db, uuid4())