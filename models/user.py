from datetime import datetime
from typing import Optional, Sequence
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
    is_admin: Mapped[bool] = mapped_column(default=False)

    def delete(self) -> bool:  # type: ignore
        """Delete user from database"""
        try:

            # preferred this over super().delete()
            # since we can achieve two operations
            # in one session and also rollback safety.
            with get_db().session() as session:
                from models.admin import Admin
                from models.subdomain import Subdomain

                admin_record = session.scalars(
                    select(Admin)
                    .filter(Admin.user_id == self.id)
                ).one_or_none()

                if admin_record:
                    session.delete(admin_record)

                subdomains = session.scalars(
                    select(Subdomain)
                    .filter(Subdomain.user_id == self.id)
                ).all()

                for subdomain in subdomains:
                    subdomain.delete(session)

                session.delete(self)
                session.commit()


            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_subdomains(self) -> Sequence['Subdomain']:  # type: ignore
        """Get all subdomains for this user"""
        from models.subdomain import Subdomain
        return Subdomain.get_by_user_id(self.id)

    def make_admin(self) -> bool:
        """Make user admin"""
        try:
            from models.admin import Admin
            with get_db().session() as session:
                new_admin_record = Admin(user_id=self.id)
                session.add(new_admin_record)
                self.is_admin = True
                self.save(session)
                session.commit()
            return True
        except Exception as e:
            print(f"Error making user admin: {e}")
            return False

    def remove_admin(self) -> bool:
        """Remove admin privileges"""
        try:
            from models.admin import Admin
            with get_db().session() as session:
                admin_record = session.scalars(
                    select(Admin)
                    .filter(Admin.user_id == self.id)
                ).one_or_none()
                if admin_record:
                    session.delete(admin_record)
                self.is_admin = False
                self.save(session)
                session.commit()

            return True
        except Exception as e:
            print(f"Error removing admin privileges: {e}")
            return False


    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Get user by ID"""
        with get_db().session() as session:
            return session.get(User, user_id)

    @classmethod
    def get_by_github_id(cls, github_id: int) -> Optional['User']:
        """Get user by GitHub ID"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .filter(User.github_id == github_id)
            ).one_or_none()  # checks for data integrity
            # on unique columns
            # https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.ScalarResult.one_or_none

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .filter(User.username == username)
            ).one_or_none()

    @classmethod
    def get_all(cls) -> Sequence['User']:
        """Get all users"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
                .order_by(User.created_at.desc())
            ).all()

    def to_dict(self, isoformat=True) -> dict:
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
            'is_admin': self.is_admin
        }
