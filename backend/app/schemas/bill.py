import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.bill import BillHouse, BillStatus


class BillListItem(BaseModel):
    """
    Slim shape for GET /bills — a list view shouldn't ship full text/OCR data.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bill_number: str
    title: str
    house: BillHouse
    status: BillStatus
    current_stage: str | None
    date_introduced: datetime | None


class BillDetail(BillListItem):
    """
    Full shape for GET /bills/{id} — includes sponsor and source doc link.
    Deliberately does NOT include raw_extracted_text or OCR data — that's
    internal pipeline data, not something the public API should expose.
    """
    sponsor: str | None
    pdf_url: str
    public_participation_deadline: datetime | None
