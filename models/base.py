from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    DateTime
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy.orm.session import make_transient
from utils.db_utils import get_db
from utils.common import get_current_datetime


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_current_datetime
    )

    def save(self, session: Session | None = None) -> int:
        if session is None:
            session = get_db().session()
        with session:
            if self.id:
                if not hasattr(self, "_sa_instance_state"):
                    raise Exception(
                        "SQLAlchemy: invalid User instance with id")

                # The following is for use case when we delete
                # a record and want to re-insert using the
                # original instance.
                if self._sa_instance_state._deleted:  # type: ignore
                    make_transient(self)
            session.add(self)
            session.commit()
            return self.id

    def delete(self, session: Session | None = None) -> None:
        if session is None:
            session = get_db().session()
        with session:
            session.delete(self)
            session.commit()
