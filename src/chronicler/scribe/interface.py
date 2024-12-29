from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto
from telegram import Update, Message as TelegramMessage
from chronicler.storage.interface import Message, Topic, Attachment
from datetime import datetime

@dataclass
class CommandResponse:
    """Response from a command handler"""
    text: str
    error: bool = False
    metadata: Dict[str, Any] = None

class UserState(Enum):
    """Possible states for user sessions"""
    IDLE = auto()
    AWAITING_GITHUB_TOKEN = auto()
    AWAITING_GITHUB_REPO = auto()
    CONFIGURING_GROUP = auto()

@dataclass
class ScribeConfig:
    """Scribe configuration and settings"""
    token: str
    admin_users: List[int]
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    
    def __post_init__(self):
        if not self.token:
            raise ValueError("Token cannot be empty")
        if not self.admin_users:
            raise ValueError("Must specify at least one admin user")

@dataclass
class UserSession:
    """Track user interaction state"""
    user_id: int
    state: UserState = UserState.IDLE
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GroupConfig:
    """Per-group settings"""
    group_id: int
    topic_id: str
    enabled: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)

class MessageConverter:
    """Convert Telegram messages to storage format"""
    
    @staticmethod
    async def to_storage_message(telegram_msg: TelegramMessage) -> Message:
        """Convert Telegram message to storage format"""
        # Extract attachments and metadata
        attachments = []
        metadata = {
            "message_id": telegram_msg.message_id,
            "chat_id": telegram_msg.chat.id,
            "chat_type": telegram_msg.chat.type,
            "from_user": telegram_msg.from_user.id,
            "file_ids": []
        }

        # Handle stickers
        if telegram_msg.sticker:
            attachments.append(Attachment(
                id=f"sticker_{telegram_msg.message_id}",
                type="image/webp",  # Standard format for Telegram stickers
                filename=f"sticker_{telegram_msg.message_id}.webp"
            ))
            metadata["file_ids"].append(telegram_msg.sticker.file_id)
            metadata["sticker_emoji"] = telegram_msg.sticker.emoji
            metadata["sticker_set"] = telegram_msg.sticker.set_name
            metadata["sticker_type"] = telegram_msg.sticker.type

        # Handle photo attachments
        if telegram_msg.photo:
            # Use the last (highest quality) photo
            photo = telegram_msg.photo[-1]
            attachments.append(Attachment(
                id=f"photo_{telegram_msg.message_id}",
                type="image/jpeg",
                filename=f"photo_{telegram_msg.message_id}.jpg"
            ))
            metadata["file_ids"].append(photo.file_id)

        # Handle video attachments
        if telegram_msg.video:
            attachments.append(Attachment(
                id=f"video_{telegram_msg.message_id}",
                type=telegram_msg.video.mime_type or "video/mp4",
                filename=f"video_{telegram_msg.message_id}.mp4"
            ))
            metadata["file_ids"].append(telegram_msg.video.file_id)
            metadata["video_duration"] = telegram_msg.video.duration

        # Handle document attachments
        if telegram_msg.document:
            attachments.append(Attachment(
                id=f"doc_{telegram_msg.message_id}",
                type=telegram_msg.document.mime_type or "application/octet-stream",
                filename=telegram_msg.document.file_name or f"document_{telegram_msg.message_id}"
            ))
            metadata["file_ids"].append(telegram_msg.document.file_id)

        # Handle animations/GIFs
        if telegram_msg.animation:
            attachments.append(Attachment(
                id=f"anim_{telegram_msg.message_id}",
                type=telegram_msg.animation.mime_type or "video/mp4",
                filename=f"animation_{telegram_msg.message_id}.mp4"
            ))
            metadata["file_ids"].append(telegram_msg.animation.file_id)

        # Handle voice messages
        if telegram_msg.voice:
            attachments.append(Attachment(
                id=f"voice_{telegram_msg.message_id}",
                type=telegram_msg.voice.mime_type or "audio/ogg",
                filename=f"voice_{telegram_msg.message_id}.ogg"
            ))
            metadata["file_ids"].append(telegram_msg.voice.file_id)
            metadata["voice_duration"] = telegram_msg.voice.duration

        # Handle audio messages
        if telegram_msg.audio:
            attachments.append(Attachment(
                id=f"audio_{telegram_msg.message_id}",
                type=telegram_msg.audio.mime_type or "audio/mpeg",
                filename=telegram_msg.audio.file_name or f"audio_{telegram_msg.message_id}.mp3"
            ))
            metadata["file_ids"].append(telegram_msg.audio.file_id)
            metadata["audio_duration"] = telegram_msg.audio.duration
            if telegram_msg.audio.title:
                metadata["audio_title"] = telegram_msg.audio.title
            if telegram_msg.audio.performer:
                metadata["audio_performer"] = telegram_msg.audio.performer

        # Handle forwarded messages
        if telegram_msg.forward_from:
            metadata["forwarded_from"] = telegram_msg.forward_from.id
            metadata["forward_date"] = telegram_msg.forward_date.isoformat()
            metadata["original_sender"] = telegram_msg.forward_from.first_name

        # Create storage message
        return Message(
            content=telegram_msg.text or "",
            source=f"telegram_{telegram_msg.from_user.id}",
            timestamp=telegram_msg.date or datetime.utcnow(),
            metadata=metadata,
            attachments=attachments if attachments else None
        )

class ScribeInterface:
    """Interface for scribe operations"""
    async def start(self) -> None:
        """Start the scribe"""
        raise NotImplementedError
    
    async def stop(self) -> None:
        """Stop the scribe"""
        raise NotImplementedError
    
    async def handle_message(self, update: Update) -> None:
        """Process incoming messages"""
        raise NotImplementedError
    
    async def handle_command(self, update: Update) -> None:
        """Handle scribe commands"""
        raise NotImplementedError 