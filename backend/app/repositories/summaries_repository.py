"""
Contains AI Summarization database operations.
Handles creation and finding operations.
"""

from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summary import Summary, SummaryStatus
from app.schemas.ai_summary import SummaryOutput
from app.utils.exceptions import ResourceNotFoundError


async def create_draft_summary(db: AsyncSession, bill_id: UUID, output: SummaryOutput, ai_model_used: str) -> Summary:
    """
    Creates the Summary record
    """
    result = await db.execute(
        select(func.count(Summary.id)).filter(Summary.bill_id == bill_id))
    existing_count = result.scalar_one()
    
    summary = Summary(
        bill_id=bill_id,
        version=existing_count + 1,
        summary_full=output.summary_full,
        summary_short_ussd=output.summary_full[:450],
        pros=[p.model_dump() for p in output.pros],
        cons=[c.model_dump() for c in output.cons],
        sectors_affected=[s.value for s in output.sectors_affected],
        ai_model_used=ai_model_used,
        status=SummaryStatus.draft,
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return summary

async def find_latest_summary_for_bill(db: AsyncSession, bill_id: UUID) -> Summary | None:
    """
    Finds latest Bill Summary.
    Returns None if no summary exists for the bill.
    """
    result = await db.execute(
        select(Summary)
        .where(Summary.bill_id == bill_id)
        .order_by(Summary.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def find_summary_by_id(db: AsyncSession, summary_id: UUID) -> Summary:
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if summary is None:
        raise ResourceNotFoundError("Summary", summary_id)
    return summary