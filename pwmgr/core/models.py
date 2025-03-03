"""
Data models for password manager.
"""
import uuid
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class PasswordEntry:
    """
    Represents a single password entry in the password manager.
    """
    name: str
    username: str
    password: str
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """
        Convert the password entry to a dictionary.
        
        Returns:
            Dictionary representation of the password entry
        """
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordEntry':
        """
        Create a password entry from a dictionary.
        
        Args:
            data: Dictionary containing password entry data
            
        Returns:
            PasswordEntry object
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            username=data["username"],
            password=data["password"],
            notes=data.get("notes"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        ) 