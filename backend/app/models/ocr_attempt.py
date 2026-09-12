import enum
import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, Enum, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OcrEngine(str, enum.Enum):
    tesseract = "tesseract"
    aws_textract = "aws_textract"
    google_doc_ai = "google_doc_ai"


class OcrAttempt(Base):
    """
    Raw output from a single OCR engine run on a single bill.
    Kept even after human review — this is the audit trail that lets you
    later distinguish 'OCR got it wrong' from 'AI misinterpreted correct text.'
    Never shown to end users directly.
    """
    __tablename__ = "ocr_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"))

    engine: Mapped[OcrEngine] = mapped_column(Enum(OcrEngine))
    raw_text: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bill: Mapped["Bill"] = relationship(back_populates="ocr_attempts")
