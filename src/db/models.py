"""
SQLAlchemy 2.0 ORM models (async-compatible).

Uses the modern ``Mapped`` / ``mapped_column`` typing API introduced in 2.0.
"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class User(Base):
    """Tracks every unique visitor who runs /start.

    This table is used as a lightweight analytics store: each row
    represents one Telegram user who has interacted with the bot at
    least once.  The ``first_seen`` timestamp lets you slice the
    audience by date (e.g., "how many HR managers visited this week?").

    Columns:
        id:          Auto-increment primary key.
        telegram_id: Telegram user ID — unique, used as the upsert key.
        username:    @username (may be NULL — not all users set one).
        first_name:  Telegram first name at the time of first visit.
        first_seen:  UTC timestamp set automatically on first INSERT.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    first_seen: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<User id={self.id} telegram_id={self.telegram_id} "
            f"username={self.username!r} first_seen={self.first_seen}>"
        )
