from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: str
    name: str
    metadata: Dict[str, Any] = None

@dataclass
class Topic:
    id: str
    name: str
    metadata: Dict[str, Any] = None

@dataclass
class Message:
    content: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    attachments: List['Attachment'] = None

    def to_json(self) -> str:
        """Convert message to JSON string"""
        logger.debug(f"Serializing message from {self.source}")
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        # Handle attachments - convert bytes to None for serialization
        if data.get('attachments'):
            logger.debug(f"Processing {len(data['attachments'])} attachments")
            for att in data['attachments']:
                if 'data' in att:
                    att['data'] = None
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string with validation"""
        logger.debug("Deserializing message from JSON")
        data = json.loads(json_str)
        # Validate required fields
        for field in ['content', 'source', 'timestamp']:
            if field not in data:
                logger.error(f"Missing required field in JSON: {field}")
                raise ValueError(f"Missing required field: {field}")
        
        # Convert timestamp back to datetime
        logger.debug(f"Converting timestamp: {data['timestamp']}")
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Clean metadata - remove special fields
        if 'metadata' in data:
            data['metadata'] = {k:v for k,v in data['metadata'].items()
                              if k not in ('source', 'timestamp', 'type')}
        return cls(**data)

@dataclass
class Attachment:
    id: str
    type: str
    filename: str
    data: Optional[bytes] = None
    url: Optional[str] = None

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