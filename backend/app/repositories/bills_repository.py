from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.bill import Bill
from app.utils.exceptions import ResourceNotFoundError

async def find_bill_by_id(db: AsyncSession, bill_id: UUID):
    """
    Returns a bill by its ID.
    """
    result = await db.execute(select(Bill).where(Bill.id == bill_id))
    bill = result.scalar_one_or_none()
    if bill is None:
        raise ResourceNotFoundError("Bill", bill_id)
    return bill