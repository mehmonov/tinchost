from datetime import datetime
from sqlalchemy import (
    DateTime
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
    Session
)
from zoneinfo import ZoneInfo
from config import config

from utils.db_utils import get_db

def get_current_datetime():
    return datetime.now(ZoneInfo(config.TIMEZONE))

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_current_datetime
    )

    def save(self) -> int:
        with get_db().session() as session:
            if not self.id:
                session.add(self)
            session.commit()
            return self.id

    def delete(self) -> None:
        with get_db().session() as session:
            session.delete(self)
            session.commit()
