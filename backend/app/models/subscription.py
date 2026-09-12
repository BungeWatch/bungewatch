import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubscriptionChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    website = "website"
    ussd = "ussd"


class Subscription(Base):
    """
    A user can subscribe to:
      - a specific bill (bill_id set, sector null)
      - an entire sector (sector set, bill_id null)
      - everything (both null)
    This replaces any notion of a 'bills subscribed to' field on the user table —
    that shape can't be queried efficiently ("who is subscribed to bill X?").
    """
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    bill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bills.id", ondelete="CASCADE"), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)

    channel: Mapped[SubscriptionChannel] = mapped_column(Enum(SubscriptionChannel))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="subscriptions")
