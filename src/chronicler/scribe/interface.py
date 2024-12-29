from abc import ABC, abstractmethod
from unittest.mock import Mock
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from telegram import Message as TelegramMessage, Update
from datetime import datetime
import logging

from chronicler.storage.interface import Message, Attachment

logger = logging.getLogger(__name__)

class UserState(Enum):
    """User session states"""
    IDLE = "idle"
    AWAITING_GITHUB_TOKEN = "awaiting_github_token"
    AWAITING_GITHUB_REPO = "awaiting_repo"
    AWAITING_TELEGRAM_TOPIC = "awaiting_topic"
    AWAITING_TELEGRAM_FILTER = "awaiting_filter"

@dataclass
class UserSession:
    """User session data"""
    user_id: int
    state: UserState = UserState.IDLE
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        logger.debug(f"Creating user session for {self.user_id} in state {self.state}")
        if self.context is None:
            self.context = {}

@dataclass
class GroupConfig:
    """Group configuration"""
    group_id: int
    topic_id: str
    enabled: bool = True
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        logger.debug(f"Creating group config for {self.group_id} with topic {self.topic_id}")
        if self.filters is None:
            self.filters = {}

@dataclass
class ScribeConfig:
    """Configuration for a scribe instance"""
    telegram_token: str = None
    token: str = None  # Alias for telegram_token for backward compatibility
    admin_users: list[int] = field(default_factory=list)
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Handle token alias
        self.telegram_token = self.telegram_token or self.token
        if not self.telegram_token:
            raise ValueError("Either telegram_token or token must be provided")
        self.token = self.telegram_token  # Ensure both are set to the same value
        
        logger.debug("Creating scribe config")
        logger.debug(f"GitHub integration: {'configured' if self.github_token and self.github_repo else 'not configured'}")
        if self.github_token:
            logger.debug("GitHub token is set")
        if self.github_repo:
            logger.debug(f"GitHub repo is set to: {self.github_repo}")
        logger.debug("Telegram token is set")
        logger.debug(f"Admin users: {self.admin_users}")

@dataclass
class CommandResponse:
    """Command response data"""
    text: str
    error: bool = False
    
    def __post_init__(self):
        logger.debug(f"Creating command response: {'ERROR: ' if self.error else ''}{self.text}")

class MessageConverter:
    """Converts between Telegram and internal message formats"""
    
    @staticmethod
    async def to_storage_message(message: TelegramMessage) -> Message:
        """Convert a Telegram message to storage format"""
        try:
            # Extract basic metadata
            metadata = {
                'message_id': message.message_id,
                'chat_id': message.chat.id,
                'chat_type': message.chat.type,
                'chat_title': message.chat.title if message.chat.title else str(message.chat.id),
                'user_id': message.from_user.id if message.from_user else None,
                'username': message.from_user.username if message.from_user else None,
                'file_ids': []  # Will be populated with attachment file IDs
            }
            
            # Handle forwarded messages
            if getattr(message, 'forward_from', None):
                metadata['forwarded_from'] = {
                    'user_id': message.forward_from.id,
                    'username': message.forward_from.username
                }
                metadata['forward_date'] = message.forward_date
            
            # Get message content
            content = message.text or message.caption or ""
            if isinstance(content, Mock):
                content = ""
            
            # Handle attachments
            attachments = []
            
            # Photo
            if message.photo:
                photo = message.photo[-1]  # Get highest resolution
                metadata['file_ids'].append(photo.file_id)
                attachments.append(Attachment(
                    id=photo.file_id,
                    type="image/jpeg",
                    filename=f"{message.message_id}_{photo.file_id}.jpg"
                ))
            
            # Video
            if getattr(message, 'video', None):
                metadata['file_ids'].append(message.video.file_id)
                attachments.append(Attachment(
                    id=message.video.file_id,
                    type="video/mp4",
                    filename=f"{message.message_id}_{message.video.file_id}.mp4"
                ))
            
            # Document
            if getattr(message, 'document', None):
                metadata['file_ids'].append(message.document.file_id)
                filename = message.document.file_name
                if not filename:
                    filename = f"{message.message_id}_{message.document.file_id}"
                elif not filename.startswith(str(message.message_id)):
                    filename = f"{message.message_id}_{filename}"
                attachments.append(Attachment(
                    id=message.document.file_id,
                    type=message.document.mime_type or "application/octet-stream",
                    filename=filename
                ))
            
            # Animation
            if getattr(message, 'animation', None):
                metadata['file_ids'].append(message.animation.file_id)
                attachments.append(Attachment(
                    id=message.animation.file_id,
                    type="video/mp4",
                    filename=f"{message.message_id}_{message.animation.file_id}.mp4"
                ))
            
            # Sticker
            if getattr(message, 'sticker', None):
                metadata['file_ids'].append(message.sticker.file_id)
                metadata['sticker_set'] = message.sticker.set_name
                metadata['sticker_emoji'] = message.sticker.emoji
                metadata['sticker_type'] = message.sticker.type
                attachments.append(Attachment(
                    id=message.sticker.file_id,
                    type="image/webp",
                    filename=f"{message.message_id}_{message.sticker.file_id}.webp"
                ))
            
            # Voice
            if getattr(message, 'voice', None):
                metadata['file_ids'].append(message.voice.file_id)
                metadata['voice_duration'] = message.voice.duration
                attachments.append(Attachment(
                    id=message.voice.file_id,
                    type=message.voice.mime_type or "audio/ogg",
                    filename=f"{message.message_id}_{message.voice.file_id}.ogg"
                ))
            
            # Audio
            if getattr(message, 'audio', None):
                metadata['file_ids'].append(message.audio.file_id)
                metadata['audio_duration'] = message.audio.duration
                metadata['audio_title'] = message.audio.title
                metadata['audio_performer'] = message.audio.performer
                attachments.append(Attachment(
                    id=message.audio.file_id,
                    type=message.audio.mime_type or "audio/mp3",
                    filename=f"{message.message_id}_{message.audio.file_id}.mp3"
                ))
            
            return Message(
                content=content,
                source=f"telegram_{message.chat.id}",
                timestamp=message.date,
                metadata=metadata,
                attachments=attachments if attachments else None
            )
            
        except Exception as e:
            logger.error(f"Failed to convert message: {e}", exc_info=True)
            raise

class ScribeInterface(ABC):
    """Base interface for scribe implementations"""
    
    @abstractmethod
    async def handle_message(self, update: Update) -> CommandResponse:
        """Handle incoming message"""
        pass
    
    @abstractmethod
    async def handle_command(self, update: Update) -> CommandResponse:
        """Handle scribe command"""
        pass 