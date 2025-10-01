from __future__ import annotations
import os
import shutil
from datetime import datetime
from typing import Optional, Sequence
from pathlib import Path
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from models.base import Base
from utils.db_utils import get_db
from utils.common import get_current_datetime
from config import config


class Subdomain(Base):
    """Subdomain model"""
    __tablename__ = "subdomains"
    id: Mapped[int] = mapped_column(primary_key=True)
    from models.user import User
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True)
    subdomain_name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=get_current_datetime
    )

    def delete(self, session: Session | None = None) -> bool:  # type: ignore
        """Delete subdomain and its files"""
        try:
            """
            Order analysis:
            Order:  delete record = del_rec
                    delete files = del_f

                    del_rec fails --> no loss
                    del_f fails --> record restored and some file loss
                    otherwise success

            Order:  delete files = del_f
                    delete record = del_rec

                    del_f fails --> some file loss
                    del_rec fails --> complete file loss
                    otherwise: success
            Conclusion:
                    Order matters. Choose first.
            """
            super().delete(session)
            if self.file_path and os.path.exists(self.file_path):
                shutil.rmtree(self.file_path)

            return True
        except Exception as e:
            self.save() # resurrect the record
            print(f"Error deleting subdomain: {e}")
            return False

    def update_name(self, new_name: str) -> bool:
        """Update subdomain name and move files"""
        if not new_name:
            return False

        # Check if new name is available
        if self.name_exists(new_name):
            return False

        try:
            old_path = self.file_path
            new_path = os.path.join(config.SITES_FOLDER, new_name)

            # Move files if they exist
            if os.path.exists(old_path):
                os.rename(old_path, new_path)

            self.subdomain_name = new_name
            self.file_path = new_path
            self.save()

            return True
        except Exception as e:
            print(f"Error updating subdomain name: {e}")
            return False

    def get_url(self) -> str:
        """Get full URL for subdomain"""
        return f"https://{self.subdomain_name}.{config.BASE_DOMAIN}"

    def get_file_size(self) -> int:
        """Get total size of files in bytes"""
        if not os.path.exists(self.file_path):
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.file_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

    def get_file_count(self) -> int:
        """Get total number of files"""
        if not os.path.exists(self.file_path):
            return 0

        file_count = 0
        for dirpath, dirnames, filenames in os.walk(self.file_path):
            file_count += len(filenames)
        return file_count

    @classmethod
    def get_by_id(cls, subdomain_id: int) -> Subdomain | None:
        """Get subdomain by ID"""
        with get_db().session() as session:
            return session.get(Subdomain, subdomain_id)

    @classmethod
    def get_by_name(cls, subdomain_name: str) -> Subdomain | None:
        """Get subdomain by name"""
        with get_db().session() as session:
            return session.scalars(
                select(Subdomain)
                .filter(Subdomain.subdomain_name == subdomain_name)
            ).one_or_none()

    @classmethod
    def get_by_user_id(cls, user_id: int) -> Sequence[Subdomain]:
        """Get all subdomains for a user"""
        with get_db().session() as session:
            return session.scalars(
                select(Subdomain)
                .filter(Subdomain.user_id == user_id)
                .order_by(Subdomain.created_at.desc())
            ).all()

    @classmethod
    def get_all(cls) -> Sequence[Subdomain]:
        """Get all subdomains"""
        with get_db().session() as session:
            return session.scalars(
                select(Subdomain)
                .order_by(Subdomain.created_at.desc())
            ).all()

    @classmethod
    def name_exists(cls, subdomain_name: str) -> bool:
        """Check if subdomain name exists"""
        with get_db().session() as session:
            result = session.scalars(
                select(Subdomain.id)
                .filter(Subdomain.subdomain_name == subdomain_name)
            ).one_or_none()

            return True if result else False

    @classmethod
    def generate_unique_name(cls, base_name: str | None = None) -> str:
        """Generate unique 5-character random subdomain name"""
        import random
        import string

        # Always generate 5-character random name, ignore base_name
        while True:
            name = ''.join(random.choices(string.ascii_lowercase, k=5))
            if not cls.name_exists(name):
                return name

    def to_dict(self, isoformat=True) -> dict:
        """Convert subdomain to dictionary"""
        created_at = self.created_at
        updated_at = self.updated_at
        if created_at and isoformat:
            created_at = created_at.isoformat()  # type: ignore
        if updated_at and isoformat:
            updated_at = updated_at.isoformat()  # type: ignore

        return {
            'id': self.id,
            'user_id': self.user_id,
            'subdomain_name': self.subdomain_name,
            'file_path': self.file_path,
            'original_filename': self.original_filename,
            'created_at': created_at,
            'updated_at': updated_at,
            'url': self.get_url(),
            'file_size': self.get_file_size(),
            'file_count': self.get_file_count()
        }
