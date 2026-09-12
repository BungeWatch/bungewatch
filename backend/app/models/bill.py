import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BillHouse(str, enum.Enum):
    national_assembly = "national_assembly"
    senate = "senate"


class BillStatus(str, enum.Enum):
    """
    Fixed enum from scraped status strings
    (which vary in wording between sources) get mapped to one of these during
    ingestion. The raw scraped string is kept separately in `raw_status_text`
    for debugging when the mapping is unclear.
    """
    introduced = "introduced"
    first_reading = "first_reading"
    committee_stage = "committee_stage"
    public_participation = "public_participation"
    second_reading = "second_reading"
    third_reading = "third_reading"
    assented = "assented"
    withdrawn = "withdrawn"
    unknown = "unknown"


class ExtractionMethod(str, enum.Enum):
    native = "native"   # PDF had a usable text layer — extracted directly
    ocr = "ocr"          # PDF was scanned — required OCR


class SourceSite(str, enum.Enum):
    kenya_law = "kenya_law"
    parliament = "parliament"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Official reference — used for dedup, since titles can vary slightly across scrapes
    bill_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))

    house: Mapped[BillHouse] = mapped_column(Enum(BillHouse))
    sponsor: Mapped[str | None] = mapped_column(String(300), nullable=True)

    status: Mapped[BillStatus] = mapped_column(Enum(BillStatus), default=BillStatus.unknown)
    raw_status_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(300), nullable=True)

    date_introduced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_participation_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_site: Mapped[SourceSite] = mapped_column(Enum(SourceSite))
    pdf_url: Mapped[str] = mapped_column(Text)
    extraction_method: Mapped[ExtractionMethod | None] = mapped_column(Enum(ExtractionMethod), nullable=True)

    # Raw extracted text (native or best-OCR-pass) — NOT the human-reviewed canonical version.
    # See ReviewedText for the source-of-truth text used by the AI summarizer.
    raw_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    date_scraped: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ocr_attempts: Mapped[list["OcrAttempt"]] = relationship(back_populates="bill", cascade="all, delete-orphan")
    reviewed_text: Mapped["ReviewedText | None"] = relationship(back_populates="bill", uselist=False)
    summaries: Mapped[list["Summary"]] = relationship(back_populates="bill", cascade="all, delete-orphan")
