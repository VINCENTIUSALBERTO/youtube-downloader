"""
User model for YouTube Downloader Bot.

Provides user-related data structures and helper methods.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User data model."""
    
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    tokens: int
    is_banned: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from database dict."""
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            tokens=data.get("tokens", 0),
            is_banned=bool(data.get("is_banned", False)),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
        )
    
    @property
    def display_name(self) -> str:
        """Get user display name."""
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        if self.username:
            return f"@{self.username}"
        return f"User {self.user_id}"
    
    def has_tokens(self, amount: int = 1) -> bool:
        """Check if user has enough tokens."""
        return self.tokens >= amount
