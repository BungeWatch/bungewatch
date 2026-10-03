import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.bills_repository import find_bill_by_id
from app.repositories.summaries_repository import create_draft_summary
from app.services.ai_summarizer import asummarize_bill, MODEL_NAME
from app.utils.exceptions import BillTooLongError, AIModelError, NotFoundError
from app.pipeline.chunking import needs_chunking, summarize_long_bill

logger = logging.getLogger("bungewatch.pipeline")


async def run_summarization_for_bill(db: AsyncSession, bill_id: UUID) -> UUID | None:
    """
    Fetches a bill by id, runs it through the summarizer then stores the draft summary in the database.
    """
    bill = await find_bill_by_id(db, bill_id)

    if bill.reviewed_text is None:
        logger.info(f"Bill {bill_id} has no reviewed_text yet — skipping summarization.")
        return None

    try:
        if needs_chunking(bill.title, bill.reviewed_text.text):
            output = await summarize_long_bill(bill.title, bill.reviewed_text.text)
        else:
            output = await asummarize_bill(bill.title, bill.reviewed_text.text)
   
    except BillTooLongError as e:
        logger.warning(f"Bill {bill_id} exceeds single-pass token limit: {e.message}")
        raise
    except AIModelError as e:
        logger.error(f"Summarization failed for bill {bill_id} after retries: {e.message}")
        raise

    summary = await create_draft_summary(db, bill_id, output, ai_model_used=MODEL_NAME)
    logger.info(f"Created draft summary {summary.id} (v{summary.version}) for bill {bill_id}.")
    return summary.id