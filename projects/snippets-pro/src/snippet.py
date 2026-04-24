"""Snippet data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Snippet:
    """Represents a code snippet."""
    
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    code: str = ""
    language: str = "python"
    tags: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "code": self.code,
            "language": self.language,
            "tags": ",".join(self.tags) if self.tags else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        """Create from database row."""
        tags = data.get("tags", "").split(",") if data.get("tags") else []
        tags = [t.strip() for t in tags if t.strip()]
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            code=data.get("code", ""),
            language=data.get("language", "python"),
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )
