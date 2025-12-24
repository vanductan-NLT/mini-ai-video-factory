"""
User model for Mini Video Factory authentication system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    """User model representing authenticated users in the system"""
    id: str
    username: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    @classmethod
    def create_new(cls, username: str, password_hash: str) -> 'User':
        """Create a new user instance with generated ID and current timestamp"""
        return cls(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            last_login=None
        )
    
    def update_last_login(self) -> None:
        """Update the last login timestamp to current time"""
        self.last_login = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert user instance to dictionary for database operations"""
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user instance from dictionary (database result)"""
        return cls(
            id=data['id'],
            username=data['username'],
            password_hash=data['password_hash'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_login=datetime.fromisoformat(data['last_login']) if data['last_login'] else None
        )