from models.base import Base
from utils.db_utils import get_db

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

class Admin(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

