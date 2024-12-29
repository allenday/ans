import pytest
from chronicler.scribe.interface import MessageConverter
# Update other imports as needed 
from datetime import datetime
from unittest.mock import Mock
from telegram import (
    Message as TelegramMessage, Chat, User, PhotoSize,
    Video, Document, Voice, Audio, Animation, Sticker
)
from chronicler.scribe.interface import MessageConverter
from chronicler.storage.interface import Message, Attachment

@pytest.fixture
def mock_telegram_message():
    """Create a mock Telegram message"""
    msg = Mock(spec=TelegramMessage)
    msg.message_id = 123
    msg.text = "Test message"
    msg.date = datetime.utcnow()
    msg.chat = Mock(spec=Chat)
    msg.chat.id = 456
    msg.chat.type = "group"
    msg.from_user = Mock(spec=User)
    msg.from_user.id = 789
    # Initialize all media types as None
    msg.photo = None
    msg.video = None
    msg.document = None
    msg.voice = None
    msg.audio = None
    msg.animation = None
    msg.forward_from = None
    msg.forward_date = None
    msg.sticker = None
    msg.attachments = []  # Initialize empty attachments list
    return msg

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_basic_message_conversion(mock_telegram_message):
    """Test converting basic text message"""
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Test message"
    assert storage_msg.source == "telegram_789"
    assert storage_msg.metadata["message_id"] == 123
    assert storage_msg.metadata["chat_id"] == 456
    assert storage_msg.metadata["chat_type"] == "group"
    assert storage_msg.attachments is None

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_photo_message_conversion(mock_telegram_message):
    """Test converting message with photo"""
    photo = Mock(spec=PhotoSize)
    photo.file_id = "photo123"
    photo.file_unique_id = "unique123"
    mock_telegram_message.photo = [photo]
    mock_telegram_message.text = "Photo caption"
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Photo caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "image/jpeg"
    assert storage_msg.attachments[0].filename.startswith("photo_")
    assert storage_msg.attachments[0].id == f"photo_{mock_telegram_message.message_id}"
    assert storage_msg.metadata["file_ids"] == ["photo123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_video_message_conversion(mock_telegram_message):
    """Test converting message with video"""
    video = Mock(spec=Video)
    video.file_id = "video123"
    video.file_unique_id = "unique123"
    video.mime_type = "video/mp4"
    video.duration = 30
    mock_telegram_message.video = video
    mock_telegram_message.text = "Video caption"
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Video caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "video/mp4"
    assert storage_msg.metadata["video_duration"] == 30
    assert storage_msg.metadata["file_ids"] == ["video123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_document_message_conversion(mock_telegram_message):
    """Test converting message with document"""
    doc = Mock(spec=Document)
    doc.file_id = "doc123"
    doc.file_unique_id = "unique123"
    doc.file_name = "test.pdf"
    doc.mime_type = "application/pdf"
    mock_telegram_message.document = doc
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "application/pdf"
    assert storage_msg.attachments[0].filename == "test.pdf"
    assert storage_msg.metadata["file_ids"] == ["doc123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_forwarded_message_conversion(mock_telegram_message):
    """Test converting forwarded message"""
    forward_from = Mock(spec=User)
    forward_from.id = 999
    forward_from.first_name = "Original"
    mock_telegram_message.forward_from = forward_from
    mock_telegram_message.forward_date = datetime.utcnow()
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.metadata["forwarded_from"] == 999
    assert "forward_date" in storage_msg.metadata

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_animation_message_conversion(mock_telegram_message):
    """Test converting message with animation"""
    animation = Mock(spec=Animation)
    animation.file_id = "anim123"
    animation.file_unique_id = "unique123"
    animation.mime_type = "video/mp4"
    mock_telegram_message.animation = animation
    mock_telegram_message.text = "Animation caption"
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Animation caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "video/mp4"
    assert storage_msg.metadata["file_ids"] == ["anim123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_sticker_message_conversion(mock_telegram_message):
    """Test converting message with sticker"""
    sticker = Mock(spec=Sticker)
    sticker.file_id = "sticker123"
    sticker.file_unique_id = "unique123"
    sticker.set_name = "StickerSet1"
    sticker.emoji = "😊"
    sticker.type = "regular"  # or "animated" or "video"
    mock_telegram_message.sticker = sticker
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "image/webp"  # Standard sticker format
    assert storage_msg.attachments[0].filename.startswith("sticker_")
    assert storage_msg.metadata["file_ids"] == ["sticker123"]
    assert storage_msg.metadata["sticker_emoji"] == "😊"
    assert storage_msg.metadata["sticker_set"] == "StickerSet1"
    assert storage_msg.metadata["sticker_type"] == "regular" 

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_voice_message_conversion(mock_telegram_message):
    """Test converting message with voice"""
    voice = Mock(spec=Voice)
    voice.file_id = "voice123"
    voice.file_unique_id = "unique123"
    voice.mime_type = "audio/ogg"
    voice.duration = 15
    mock_telegram_message.voice = voice
    mock_telegram_message.text = None  # Voice messages typically don't have text
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == ""  # Empty content for voice messages
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "audio/ogg"
    assert storage_msg.metadata["voice_duration"] == 15
    assert storage_msg.metadata["file_ids"] == ["voice123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_audio_message_conversion(mock_telegram_message):
    """Test converting message with audio"""
    audio = Mock(spec=Audio)
    audio.file_id = "audio123"
    audio.file_unique_id = "unique123"
    audio.mime_type = "audio/mp3"
    audio.duration = 180
    audio.title = "Test Song"
    audio.performer = "Test Artist"
    mock_telegram_message.audio = audio
    mock_telegram_message.text = "Audio caption"
    
    storage_msg = await MessageConverter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Audio caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "audio/mp3"
    assert storage_msg.metadata["audio_duration"] == 180
    assert storage_msg.metadata["audio_title"] == "Test Song"
    assert storage_msg.metadata["audio_performer"] == "Test Artist"
    assert storage_msg.metadata["file_ids"] == ["audio123"] 