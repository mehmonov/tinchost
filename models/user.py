from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    String, Text,
    select
)
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column
)
from models.base import Base
from utils.db_utils import get_db


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)

    def delete(self, session: Session | None = None) -> bool:  # type: ignore
        """Delete user from database"""
        try:

            if session is None:
                session = get_db().session()

            with session:
                from models.subdomain import Subdomain

                subdomains = session.scalars(
                    select(Subdomain)
                    .filter(Subdomain.user_id == self.id)
                ).all()

                for subdomain in subdomains:
                    subdomain.delete(session)

                session.delete(self) # no need to user super().delete()
                session.commit()

            return True

        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_subdomains(self) -> Sequence[Subdomain]:  # type: ignore
        """Get all subdomains for this user"""
        from models.subdomain import Subdomain
        return Subdomain.get_by_user_id(self.id)


    @classmethod
    def get_by_id(cls, user_id: int) -> User | None:
        """Get user by ID"""
        with get_db().session() as session:
            return session.get(User, user_id)

    @classmethod
    def get_by_github_id(cls, github_id: int) -> User | None:
        """Get user by GitHub ID"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .filter(User.github_id == github_id)
            ).one_or_none()  # checks for data integrity
            # on unique columns
            # https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.ScalarResult.one_or_none

    @classmethod
    def get_by_username(cls, username: str) -> User | None:
        """Get user by username"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .filter(User.username == username)
            ).one_or_none()

    @classmethod
    def get_all(cls) -> Sequence[User]:
        """Get all users"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .order_by(User.created_at.desc())
            ).all()

    def to_dict(self, isoformat=True) -> dict[str, Any]:
        """Convert user to dictionary"""
        created_at = self.created_at
        if created_at and isoformat:
            created_at = created_at.isoformat()  # type: ignore

        return {
            'id': self.id,
            'github_id': self.github_id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': created_at,
        }
