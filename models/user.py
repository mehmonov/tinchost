from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text
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
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True)
    # subdomains: Mapped[list["Subdomain"]] = relationship(
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )

    def delete(self) -> bool:
        """Delete user from database"""
        try:
            # Delete admin privileges if exists
            # loga4m: I should think about relationship
            # between User model and Admin models.
            super.delete()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_subdomains(self) -> List['Subdomain']:
        """Get all subdomains for this user"""
        return self.subdomains
    
    def make_admin(self) -> bool:
        """Make user admin"""
        try:
            db.execute_query("INSERT OR IGNORE INTO admin_users (user_id) VALUES (?)", (self.id,))
            return True
        except Exception as e:
            print(f"Error making user admin: {e}")
            return False
    
    def remove_admin(self) -> bool:
        """Remove admin privileges"""
        if not self.id:
            return False
        
        try:
            db.execute_query("DELETE FROM admin_users WHERE user_id = ?", (self.id,))
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
            return session.scalar(
                select(User)
                .filter(User.github_id == github_id)
            ).one_or_none() # checks for data integrity
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
    def get_all(cls) -> List['User']:
        """Get all users"""
        with get_db().session() as session:
            return session.scalars(
                select(User)
            ).all()
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'github_id': self.github_id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin
        }
