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
from sqlalchemy.orm.session import make_transient
from utils.db_utils import get_db
from utils.common import get_current_datetime


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_current_datetime
    )

    def save(self) -> int:
        with get_db().session() as session:
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

    def delete(self) -> None:
        with get_db().session() as session:
            session.delete(self)
            session.commit()
