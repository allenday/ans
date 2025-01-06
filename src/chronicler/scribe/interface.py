from abc import ABC, abstractmethod
from unittest.mock import Mock
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from telegram import Message as TelegramMessage, Update
from datetime import datetime
import logging
import mimetypes

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
        """Convert a Telegram message to a storage message"""
        metadata = {
            'message_id': message.message_id,
            'chat_id': message.chat.id,
            'chat_type': message.chat.type,
            'file_ids': [],
            'source': 'telegram',
            'chat_title': message.chat.title if message.chat.title else 'chronicler-dev'
        }
        
        # Add user info if available
        if message.from_user:
            metadata['user_id'] = message.from_user.id
            if message.from_user.username:
                metadata['username'] = message.from_user.username
        
        # Handle forwarded messages
        if hasattr(message, 'forward_from') and message.forward_from:
            metadata['forwarded_from'] = {
                'user_id': message.forward_from.id,
                'username': message.forward_from.username,
                'name': message.forward_from.first_name
            }
            if message.forward_date:
                metadata['forward_date'] = message.forward_date.isoformat()
        
        # Initialize attachments list
        attachments = []
        
        # Handle different types of media
        if message.photo:
            # Get largest photo size
            photo = max(message.photo, key=lambda x: x.file_size or 0)
            metadata['file_ids'].append(photo.file_id)
            attachments.append(Attachment(
                id=photo.file_id,
                type="image/jpeg",
                filename=f"{message.message_id}_{photo.file_id}.jpg"
            ))
        
        # Video
        if getattr(message, 'video', None):
            metadata['file_ids'].append(message.video.file_id)
            metadata['video_duration'] = message.video.duration
            attachments.append(Attachment(
                id=message.video.file_id,
                type="video/mp4",
                filename=f"{message.message_id}_{message.video.file_id}.mp4"
            ))
        
        # Document
        if getattr(message, 'document', None):
            metadata['file_ids'].append(message.document.file_id)
            # Use original filename if available, otherwise construct from file_id
            original_name = message.document.file_name
            if not original_name:
                ext = mimetypes.guess_extension(message.document.mime_type) if message.document.mime_type else '.bin'
                original_name = f"{message.document.file_id}{ext}"
            attachments.append(Attachment(
                id=message.document.file_id,
                type=message.document.mime_type or "application/octet-stream",
                filename=f"{message.message_id}_{original_name}"
            ))
        
        # Animation
        if getattr(message, 'animation', None):
            metadata['file_ids'].append(message.animation.file_id)
            attachments.append(Attachment(
                id=message.animation.file_id,
                type="video/mp4",
                filename=f"{message.message_id}_{message.animation.file_id}.mp4"
            ))
        
        # Voice
        if getattr(message, 'voice', None):
            metadata['file_ids'].append(message.voice.file_id)
            metadata['voice_duration'] = message.voice.duration
            attachments.append(Attachment(
                id=message.voice.file_id,
                type="audio/ogg",
                filename=f"{message.message_id}_{message.voice.file_id}.ogg"
            ))
        
        # Audio
        if getattr(message, 'audio', None):
            metadata['file_ids'].append(message.audio.file_id)
            metadata['audio_duration'] = message.audio.duration
            if message.audio.title:
                metadata['audio_title'] = message.audio.title
            if message.audio.performer:
                metadata['audio_performer'] = message.audio.performer
            attachments.append(Attachment(
                id=message.audio.file_id,
                type="audio/mp3",
                filename=f"{message.message_id}_{message.audio.file_id}.mp3"
            ))
        
        # Sticker
        if getattr(message, 'sticker', None):
            metadata['file_ids'].append(message.sticker.file_id)
            metadata['sticker_emoji'] = message.sticker.emoji
            metadata['sticker_set'] = message.sticker.set_name
            metadata['sticker_type'] = message.sticker.type
            attachments.append(Attachment(
                id=message.sticker.file_id,
                type="image/webp",
                filename=f"{message.message_id}_{message.sticker.file_id}.webp"
            ))
        
        return Message(
            content=message.text or message.caption or "",
            source=f"telegram_{message.chat.id}",
            timestamp=message.date,
            metadata=metadata,
            attachments=attachments if attachments else None
        )

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