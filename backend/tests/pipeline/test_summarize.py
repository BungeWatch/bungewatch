from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
import pytest

from app.pipeline.summarize import run_summarization_for_bill
from app.utils.exceptions import BillTooLongError, AIModelError, ResourceNotFoundError
from app.schemas.ai_summary import SummaryOutput

pytestmark = pytest.mark.asyncio  # applies to every test in this file


def _fake_summary_output():
    return SummaryOutput(
        summary_full="This bill does X.",
        pros=[{"point": "Improves Y", "section_reference": "Section 3(1)"}],
        cons=[{"point": "May increase Z", "section_reference": "Section 7"}],
        sectors_affected=["agriculture"],
        notes=None,
    )


@patch("app.pipeline.summarize.create_draft_summary", new_callable=AsyncMock)
@patch("app.pipeline.summarize.asummarize_bill", new_callable=AsyncMock)
@patch("app.pipeline.summarize.needs_chunking")
@patch("app.pipeline.summarize.find_bill_by_id", new_callable=AsyncMock)
async def test_run_summarization_creates_draft_on_success(
    mock_find_bill, mock_needs_chunking, mock_asummarize, mock_create
):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Test Bill", reviewed_text=MagicMock(text="bill text here"))
    mock_find_bill.return_value = bill
    mock_needs_chunking.return_value = False
    mock_asummarize.return_value = _fake_summary_output()
    mock_create.return_value = MagicMock(id=uuid4(), version=1)

    result = await run_summarization_for_bill(db, bill.id)

    mock_asummarize.assert_awaited_once_with("Test Bill", "bill text here")
    mock_create.assert_awaited_once()
    assert result is not None


@patch("app.pipeline.summarize.find_bill_by_id", new_callable=AsyncMock)
async def test_run_summarization_skips_bill_with_no_reviewed_text(mock_find_bill):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), reviewed_text=None)
    mock_find_bill.return_value = bill

    result = await run_summarization_for_bill(db, bill.id)

    assert result is None


@patch("app.pipeline.summarize.summarize_long_bill", new_callable=AsyncMock)
@patch("app.pipeline.summarize.needs_chunking")
@patch("app.pipeline.summarize.find_bill_by_id", new_callable=AsyncMock)
async def test_run_summarization_routes_long_bill_to_chunking(
    mock_find_bill, mock_needs_chunking, mock_summarize_long
):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Huge Bill", reviewed_text=MagicMock(text="massive text"))
    mock_find_bill.return_value = bill
    mock_needs_chunking.return_value = True
    mock_summarize_long.side_effect = BillTooLongError(token_count=999999, limit=150000)

    with pytest.raises(BillTooLongError):
        await run_summarization_for_bill(db, bill.id)

    mock_summarize_long.assert_awaited_once()


@patch("app.pipeline.summarize.asummarize_bill", new_callable=AsyncMock)
@patch("app.pipeline.summarize.needs_chunking")
@patch("app.pipeline.summarize.find_bill_by_id", new_callable=AsyncMock)
async def test_run_summarization_reraises_ai_model_error(
    mock_find_bill, mock_needs_chunking, mock_asummarize
):
    db = MagicMock()
    bill = MagicMock(id=uuid4(), title="Test Bill", reviewed_text=MagicMock(text="bill text"))
    mock_find_bill.return_value = bill
    mock_needs_chunking.return_value = False
    mock_asummarize.side_effect = AIModelError("Claude", "validation failed after retries")

    with pytest.raises(AIModelError):
        await run_summarization_for_bill(db, bill.id)


@patch("app.pipeline.summarize.find_bill_by_id", new_callable=AsyncMock)
async def test_run_summarization_propagates_not_found(mock_find_bill):
    db = MagicMock()
    mock_find_bill.side_effect = ResourceNotFoundError("Bill", uuid4())

    with pytest.raises(ResourceNotFoundError):
        await run_summarization_for_bill(db, uuid4())