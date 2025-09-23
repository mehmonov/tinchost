from datetime import datetime
from sqlalchemy import (
    Integer,
    DateTime
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
    Session
)

def get_current_datetime():
    return datetime.now()

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
