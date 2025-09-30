from typing import Any
from dataclasses import dataclass
from config import config


@dataclass
class Admin:
    username: str = config.ADMIN_USERNAME
    email: str = config.ADMIN_EMAIL
    is_admin: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin
        }

