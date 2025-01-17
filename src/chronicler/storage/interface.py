from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import uuid
from chronicler.logging import get_logger

logger = get_logger(__name__)

@dataclass
class User:
    """User data"""
    id: str
    name: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        logger.debug("Created user", extra={
            'user_id': self.id,
            'user_name': self.name
        })

@dataclass
class Topic:
    """Topic data"""
    id: str
    name: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        logger.debug("Created topic", extra={
            'topic_id': self.id,
            'topic_name': self.name
        })

@dataclass
class Message:
    """Message data"""
    content: str
    source: str
    id: str = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    attachments: List['Attachment'] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.attachments:
            logger.debug("Created message", extra={
                'message_id': self.id,
                'source': self.source,
                'content_length': len(self.content),
                'attachment_count': len(self.attachments)
            })
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class Attachment:
    """Attachment data"""
    id: str
    type: str
    filename: str
    data: Optional[bytes] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        logger.debug(f"Creating attachment {self.id} of type {self.type}")
        if self.data:
            logger.debug(f"Attachment has {len(self.data)} bytes of data")
        if self.url:
            logger.debug(f"Attachment has URL: {self.url}")

class StorageAdapter(ABC):
    """Base class for storage implementations"""
    
    @abstractmethod
    async def init_storage(self, user: User) -> 'StorageAdapter':
        """Initialize storage for a user"""
        pass
    
    @abstractmethod
    async def create_topic(self, topic: Topic, ignore_exists: bool = False) -> None:
        """Create a new topic"""
        pass
    
    @abstractmethod
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic"""
        pass
    
    @abstractmethod
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment"""
        pass
    
    @abstractmethod
    async def sync(self) -> None:
        """Synchronize with remote storage"""
        pass

    @abstractmethod
    async def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration"""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if storage is initialized"""
        pass 