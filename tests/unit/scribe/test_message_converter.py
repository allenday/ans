import pytest
from chronicler.scribe.interface import MessageConverter
# Update other imports as needed 
from datetime import datetime
from unittest.mock import Mock, AsyncMock
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
async def test_message_converter():
    """Test message conversion functionality"""
    # Create mock Telegram message
    message = Mock(spec=TelegramMessage)
    message.message_id = 789
    message.text = "Test message"
    message.date = datetime.utcnow()
    message.chat = Mock()
    message.chat.id = 456
    message.chat.type = "group"
    message.chat.title = "Test Group"
    message.from_user = Mock()
    message.from_user.id = 123
    message.from_user.username = "test_user"
    message.photo = None
    message.video = None
    message.document = None
    message.voice = None
    message.audio = None
    message.animation = None
    message.forward_from = None
    message.forward_date = None
    message.sticker = None
    
    # Convert to storage message
    converter = MessageConverter()
    storage_message = await converter.to_storage_message(message)
    
    # Verify conversion
    assert storage_message.content == "Test message"
    assert storage_message.source == "telegram_456"
    assert storage_message.metadata["chat_id"] == 456
    assert storage_message.metadata["message_id"] == 789
    assert storage_message.metadata["user_id"] == 123
    assert storage_message.metadata["username"] == "test_user"

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_basic_message_conversion(mock_telegram_message):
    """Test converting basic text message"""
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Test message"
    assert storage_msg.source == f"telegram_{mock_telegram_message.chat.id}"
    assert storage_msg.metadata["message_id"] == mock_telegram_message.message_id
    assert storage_msg.metadata["chat_id"] == mock_telegram_message.chat.id
    assert storage_msg.metadata["chat_type"] == mock_telegram_message.chat.type
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
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Photo caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "image/jpeg"
    assert storage_msg.attachments[0].filename == f"{mock_telegram_message.message_id}_{photo.file_id}.jpg"
    assert storage_msg.attachments[0].id == photo.file_id
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
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Video caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "video/mp4"
    assert storage_msg.attachments[0].filename == f"{mock_telegram_message.message_id}_{video.file_id}.mp4"
    assert storage_msg.attachments[0].id == video.file_id
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
    mock_telegram_message.text = "Document caption"
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Document caption"
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "application/pdf"
    assert storage_msg.attachments[0].filename == f"{mock_telegram_message.message_id}_{doc.file_name}"
    assert storage_msg.metadata["file_ids"] == ["doc123"]

@pytest.mark.unit
@pytest.mark.scribe
@pytest.mark.asyncio
async def test_forwarded_message_conversion(mock_telegram_message):
    """Test converting forwarded message"""
    forward_from = Mock(spec=User)
    forward_from.id = 999
    forward_from.username = "original_user"
    forward_from.first_name = "Original"
    mock_telegram_message.forward_from = forward_from
    mock_telegram_message.forward_date = datetime.utcnow()
    mock_telegram_message.text = "Forwarded message"
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert storage_msg.content == "Forwarded message"
    assert storage_msg.metadata["forwarded_from"]["user_id"] == 999
    assert storage_msg.metadata["forwarded_from"]["username"] == "original_user"
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
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
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
    
    converter = MessageConverter()
    storage_msg = await converter.to_storage_message(mock_telegram_message)
    
    assert len(storage_msg.attachments) == 1
    assert storage_msg.attachments[0].type == "image/webp"  # Standard sticker format
    assert storage_msg.attachments[0].filename == f"{mock_telegram_message.message_id}_{sticker.file_id}.webp"
    assert storage_msg.attachments[0].id == sticker.file_id
    assert storage_msg.metadata["file_ids"] == ["sticker123"]
    assert storage_msg.metadata["sticker_emoji"] == "😊"
    assert storage_msg.metadata["sticker_set"] == "StickerSet1"
    assert storage_msg.metadata["sticker_type"] == "regular"

@pytest.mark.asyncio
async def test_voice_message_conversion():
    """Test converting a voice message"""
    voice = Mock()
    voice.file_id = "voice123"
    voice.duration = 30
    voice.mime_type = "audio/ogg"
    
    message = Mock()
    message.message_id = 123
    message.voice = voice
    message.text = None
    message.caption = None
    message.date = datetime.utcnow()
    message.chat = Mock(id=456, type="group")
    message.from_user = Mock(id=789, username="test_user")
    message.photo = []  # Empty list for no photos
    message.video = None
    message.document = None
    message.animation = None
    message.audio = None
    message.sticker = None
    
    result = await MessageConverter.to_storage_message(message)
    
    assert result.attachments is not None
    assert len(result.attachments) == 1
    assert result.attachments[0].id == "voice123"
    assert result.attachments[0].type == "audio/ogg"
    assert result.attachments[0].filename == "123_voice123.ogg"
    assert result.metadata["voice_duration"] == 30
    assert result.metadata["file_ids"] == ["voice123"]

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