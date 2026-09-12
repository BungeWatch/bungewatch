import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PreferredChannel(str, enum.Enum):
    website = "website"
    whatsapp = "whatsapp"
    ussd = "ussd"


class Language(str, enum.Enum):
    english = "english"
    swahili = "swahili"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Primary identifier across all channels — phone-based since WhatsApp/USSD are phone-native.
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    name: Mapped[str | None] = mapped_column(String(200), nullable=True)  # optional — USSD users may never give one
    email: Mapped[str | None] = mapped_column(String(300), nullable=True)

    preferred_language: Mapped[Language] = mapped_column(Enum(Language), default=Language.english)
    preferred_channel: Mapped[PreferredChannel | None] = mapped_column(Enum(PreferredChannel), nullable=True)

    # WhatsApp opt-in is tracked separately and explicitly — required for template message compliance.
    whatsapp_optin: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_optin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
