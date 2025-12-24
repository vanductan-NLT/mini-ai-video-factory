"""
User model for Mini Video Factory with Supabase Auth integration
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    """User model representing authenticated users from Supabase Auth"""
    id: str  # This is auth_id from Supabase Auth
    username: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user instance from database result"""
        return cls(
            id=data.get('auth_id') or data.get('id'),
            username=data.get('username', ''),
            email=data.get('email'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        )
    
    def to_dict(self) -> dict:
        """Convert user instance to dictionary"""
        return {
            'auth_id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def update_last_login(self) -> None:
        """Update the last login timestamp to current time"""
        self.last_login = datetime.utcnow()