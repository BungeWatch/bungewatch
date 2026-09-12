import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReviewedText(Base):
    """
    The canonical, human-verified text for a bill — one per bill.
    This is the ONLY thing that should ever be fed to the AI summarizer.
    Never summarize raw_extracted_text or a raw OcrAttempt directly.
    """
    __tablename__ = "reviewed_text"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"), unique=True)

    text: Mapped[str] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # FK to a future admin/reviewer table
    diff_flags_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bill: Mapped["Bill"] = relationship(back_populates="reviewed_text")
