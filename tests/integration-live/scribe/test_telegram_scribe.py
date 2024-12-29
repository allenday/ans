import os
import pytest
import pytest_asyncio
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator
from telegram import Bot, Update
from telegram.ext import Application
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from chronicler.scribe.telegram_scribe import TelegramScribe
from chronicler.scribe.interface import ScribeConfig
from chronicler.storage.interface import StorageAdapter, Message, Topic, User, Attachment

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MockStorage(StorageAdapter):
    """Mock storage for testing"""
    def __init__(self):
        self.messages = {}
        self.topics = {}
        self.attachments = {}
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialized MockStorage")
    
    async def init_storage(self, user: User) -> 'StorageAdapter':
        self.logger.debug(f"Initializing storage for user {user.id}")
        return self
    
    async def create_topic(self, topic: Topic, ignore_exists: bool = False) -> None:
        self.logger.debug(f"Creating topic {topic.id} (ignore_exists={ignore_exists})")
        if topic.id not in self.topics or ignore_exists:
            self.topics[topic.id] = topic
            self.logger.info(f"Created topic {topic.id}")
        else:
            self.logger.debug(f"Topic {topic.id} already exists")
    
    async def save_message(self, topic_id: str, message: Message) -> None:
        self.logger.info(f"Saving message to topic {topic_id}: {message.content}")
        if topic_id not in self.messages:
            self.logger.debug(f"Creating new message list for topic {topic_id}")
            self.messages[topic_id] = []
        self.messages[topic_id].append(message)
        self.logger.debug(f"Topic {topic_id} now has {len(self.messages[topic_id])} messages")
    
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        key = f"{topic_id}:{message_id}"
        self.logger.debug(f"Saving attachment {attachment.id} for {key}")
        if key not in self.attachments:
            self.logger.debug(f"Creating new attachment list for {key}")
            self.attachments[key] = []
        self.attachments[key].append(attachment)
        self.logger.debug(f"{key} now has {len(self.attachments[key])} attachments")
    
    async def sync(self) -> None:
        self.logger.debug("Mock sync operation - no action needed")
        pass

    async def get_messages(self, topic_id: str) -> list[Message]:
        """Get all messages for a topic"""
        messages = self.messages.get(topic_id, [])
        self.logger.debug(f"Retrieved {len(messages)} messages for topic {topic_id}")
        return messages

    async def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration"""
        self.logger.debug(f"Setting GitHub config with repo: {repo}")
        pass

@pytest.fixture
def telegram_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    logger.debug(f"TELEGRAM_BOT_TOKEN: {'set' if token else 'not set'}")
    if not token:
        pytest.skip("TELEGRAM_BOT_TOKEN not set")
    return token

@pytest.fixture
def test_group_id() -> int:
    group_id = os.getenv("TELEGRAM_TEST_GROUP_ID")
    logger.debug(f"TELEGRAM_TEST_GROUP_ID: {group_id if group_id else 'not set'}")
    if not group_id:
        pytest.skip("TELEGRAM_TEST_GROUP_ID not set")
    return int(group_id)

@pytest.fixture
def test_topic_id() -> str:
    topic_id = os.getenv("TELEGRAM_TEST_TOPIC_ID")
    logger.debug(f"TELEGRAM_TEST_TOPIC_ID: {topic_id if topic_id else 'not set'}")
    if not topic_id:
        pytest.skip("TELEGRAM_TEST_TOPIC_ID not set")
    return str(topic_id)

@pytest_asyncio.fixture
async def bot(telegram_token: str) -> AsyncGenerator[Bot, None]:
    async with Bot(telegram_token) as bot:
        yield bot

@pytest_asyncio.fixture
async def storage() -> AsyncGenerator[StorageAdapter, None]:
    yield MockStorage()

@pytest_asyncio.fixture
async def scribe(telegram_token: str, storage: StorageAdapter) -> AsyncGenerator[TelegramScribe, None]:
    config = ScribeConfig(
        token=telegram_token,
        admin_users=[12345]  # Placeholder admin user
    )
    scribe = TelegramScribe(config, storage)
    await scribe.start()
    yield scribe
    await scribe.stop()

@pytest.mark.asyncio
async def test_telegram_scribe_initialization(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str
):
    """Test basic initialization of TelegramScribe with provided credentials"""
    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)
    
    # Verify configuration
    assert test_group_id in scribe.group_configs
    config = scribe.group_configs[test_group_id]
    assert config.topic_id == test_topic_id
    assert config.enabled is True

@pytest.mark.asyncio
async def test_telegram_scribe_message_monitoring(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    bot: Bot,
    storage: MockStorage
):
    """Test that scribe can monitor and process messages from specified group/topic"""
    logger = logging.getLogger(__name__)
    
    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)
    
    test_message = "Test message from integration test " + str(datetime.now())
    logger.info(f"Sending test message: {test_message}")
    
    # Send a test message
    message = await bot.send_message(
        chat_id=test_group_id,
        text=test_message,
        message_thread_id=int(test_topic_id)
    )
    
    # Create an Update object and process it directly
    update = Update(update_id=1, message=message)
    await scribe.handle_message(update)
    
    # Verify message was stored
    stored_messages = storage.messages.get(test_topic_id, [])
    assert len(stored_messages) > 0, "No messages were stored"
    
    latest_message = stored_messages[-1]
    assert latest_message.content == test_message, "Stored message content doesn't match"
    
    # Message is kept for manual inspection
    logger.info(f"\nTest message sent to group {test_group_id}, topic {test_topic_id}")
    logger.info(f"Message content: {test_message}")
    logger.info(f"Message ID: {message.message_id}") 

@pytest.mark.asyncio
async def test_telegram_scribe_sticker_message(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    bot: Bot,
    storage: MockStorage
):
    """Test handling of sticker messages"""
    logger.info("Testing sticker message handling")

    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)

    # Send a sticker message using a valid sticker ID from web3titans set
    sticker_id = "CAACAgEAAxkBAAEwZZ1ncNik9eL1aexK9If_Tjc72hhIggAC2AIAAlCDWUeaKuTaRf5AajYE"
    message = await bot.send_sticker(
        chat_id=test_group_id,
        sticker=sticker_id,
        message_thread_id=int(test_topic_id)
    )

    # Process the message
    update = Update(update_id=1, message=message)
    await scribe.handle_message(update)

    # Verify message was stored
    stored_messages = storage.messages.get(test_topic_id, [])
    assert len(stored_messages) > 0, "No messages were stored"
    
    latest_message = stored_messages[-1]
    logger.info(f"Stored message content: {latest_message.content}")
    logger.info(f"Stored message metadata: {latest_message.metadata}")
    logger.info(f"Stored message attachments: {latest_message.attachments}")
    
    # Verify sticker details
    assert latest_message.attachments is not None, "No attachments stored"
    assert len(latest_message.attachments) == 1, "Wrong number of attachments"
    assert latest_message.attachments[0].type == "image/webp", "Wrong attachment type"
    assert "sticker_set" in latest_message.metadata, "No sticker set in metadata"
    assert latest_message.metadata["sticker_set"] == "web3titans", "Wrong sticker set"
    
    # Message details for manual inspection
    logger.info(f"\nSticker message sent to group {test_group_id}, topic {test_topic_id}")
    logger.info(f"Message ID: {message.message_id}")

@pytest.mark.asyncio
async def test_telegram_scribe_photo_message(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    bot: Bot,
    storage: MockStorage
):
    """Test handling of photo messages"""
    logger.info("Testing photo message handling")

    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)

    # Use an existing test image file
    photo_path = Path("tests/integration-live/scribe/test_data/doge.webp")
    if not photo_path.exists():
        pytest.skip("Test image file not found")

    try:
        # Send a photo message with caption
        caption = f"Test photo caption - {datetime.now()}"
        with open(photo_path, "rb") as photo:
            message = await bot.send_photo(
                chat_id=test_group_id,
                photo=photo,
                caption=caption,
                message_thread_id=int(test_topic_id)
            )

        # Process the message
        update = Update(update_id=1, message=message)
        await scribe.handle_message(update)

        # Verify message was stored
        stored_messages = storage.messages.get(test_topic_id, [])
        assert len(stored_messages) > 0, "No messages were stored"
        latest_message = stored_messages[-1]
        assert latest_message.content == caption, "Caption not stored correctly"
        assert latest_message.attachments is not None, "No attachments stored"
        assert len(latest_message.attachments) == 1, "Wrong number of attachments"
        assert latest_message.attachments[0].type == "image/jpeg", "Wrong attachment type"

        # Message details for manual inspection
        logger.info(f"\nPhoto message sent to group {test_group_id}, topic {test_topic_id}")
        logger.info(f"Message content: {caption}")
        logger.info(f"Message ID: {message.message_id}")

    finally:
        pass  # No cleanup needed since we're using an existing file

@pytest.mark.asyncio
async def test_telegram_scribe_document_message(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    bot: Bot,
    storage: MockStorage
):
    """Test handling of document messages"""
    logger.info("Testing document message handling")

    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)

    # Create a test document file
    doc_path = Path("test_document.txt")
    with open(doc_path, "w") as f:
        f.write("Test document content")

    try:
        # Send a document message with caption
        caption = f"Test document caption - {datetime.now()}"
        with open(doc_path, "rb") as doc:
            message = await bot.send_document(
                chat_id=test_group_id,
                document=doc,
                caption=caption,
                message_thread_id=int(test_topic_id)
            )

        # Process the message
        update = Update(update_id=1, message=message)
        await scribe.handle_message(update)

        # Verify message was stored
        stored_messages = storage.messages.get(test_topic_id, [])
        assert len(stored_messages) > 0, "No messages were stored"
        latest_message = stored_messages[-1]
        assert latest_message.content == caption, "Caption not stored correctly"
        assert latest_message.attachments is not None, "No attachments stored"
        assert len(latest_message.attachments) == 1, "Wrong number of attachments"
        assert latest_message.attachments[0].type.startswith("text/"), "Wrong attachment type"

        # Message details for manual inspection
        logger.info(f"\nDocument message sent to group {test_group_id}, topic {test_topic_id}")
        logger.info(f"Message content: {caption}")
        logger.info(f"Message ID: {message.message_id}")

    finally:
        # Clean up test file
        doc_path.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_telegram_scribe_voice_message(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    bot: Bot,
    storage: MockStorage
):
    """Test handling of voice messages"""
    logger = logging.getLogger(__name__)
    
    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)
    
    # Send a voice message
    logger.info("Sending test voice message")
    with open("tests/integration-live/scribe/test_data/test_voice.ogg", "rb") as voice:
        message = await bot.send_voice(
            chat_id=test_group_id,
            voice=voice,
            caption="Test voice message",
            message_thread_id=int(test_topic_id)
        )
    
    # Process the message
    update = Update(update_id=1, message=message)
    await scribe.handle_message(update)
    
    # Verify message was stored
    stored_messages = storage.messages.get(test_topic_id, [])
    assert len(stored_messages) > 0, "No messages were stored"
    
    latest_message = stored_messages[-1]
    assert latest_message.content == "Test voice message", "Caption not stored correctly"
    assert latest_message.attachments is not None, "No attachments stored"
    assert len(latest_message.attachments) == 1, "Wrong number of attachments"
    assert latest_message.attachments[0].type == "audio/ogg", "Wrong attachment type"
    assert "voice_duration" in latest_message.metadata, "No voice duration in metadata" 