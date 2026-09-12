import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class NotificationChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    website = "website"  # e.g. in-app notification badge, not a push


class NotificationLog(Base):
    __tablename__ = "notifications_sent"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"))

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    template_used: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus))

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
