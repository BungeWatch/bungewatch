import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.bill import Bill, BillStatus
from app.schemas.bill import BillListItem, BillDetail

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("", response_model=list[BillListItem])
async def list_bills(
    status: BillStatus | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List bills, optionally filtered by status. This is what the website,
    WhatsApp, and USSD channels should ALL call — no channel should query
    the DB directly.
    """
    stmt = select(Bill).order_by(Bill.date_introduced.desc()).offset(offset).limit(limit)
    if status is not None:
        stmt = stmt.where(Bill.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{bill_id}", response_model=BillDetail)
async def get_bill(bill_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill
