"""Base frame class for the pipeline."""
from chronicler.logging import get_logger
from dataclasses import dataclass, field, KW_ONLY
from typing import Optional, Dict, Any, Union
from abc import ABC

from chronicler.transports.events import EventMetadata

logger = get_logger("chronicler.frames.base")

@dataclass
class Frame(ABC):
    """Base frame class."""
    _: KW_ONLY
    content: Optional[str] = None
    metadata: Union[Dict[str, Any], EventMetadata] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert metadata to dict if it's an EventMetadata object."""
        if isinstance(self.metadata, EventMetadata):
            # Convert EventMetadata to dict
            required_fields = ['chat_id', 'thread_id']
            metadata_dict = {
                'chat_id': self.metadata.chat_id,
                'chat_title': self.metadata.chat_title,
                'sender_id': self.metadata.sender_id,
                'sender_name': self.metadata.sender_name,
                'message_id': self.metadata.message_id,
                'platform': self.metadata.platform,
                'timestamp': self.metadata.timestamp,
                'reply_to': self.metadata.reply_to,
                'thread_id': self.metadata.thread_id,
                'channel_id': self.metadata.channel_id,
                'guild_id': self.metadata.guild_id,
                'is_private': self.metadata.is_private,
                'is_group': self.metadata.is_group,
                'type': self.__class__.__name__.lower()
            }
            # Keep required fields regardless of value and non-None optional fields
            self.metadata = {
                k: v for k, v in metadata_dict.items() 
                if k in required_fields or (v is not None)
            }
        else:
            # If metadata is already a dict, ensure it has the frame type
            self.metadata['type'] = self.__class__.__name__.lower()
        
        """Log frame creation."""
        logger.debug(f"FRAME - Created {self.__class__.__name__} with metadata: {self.metadata}") 