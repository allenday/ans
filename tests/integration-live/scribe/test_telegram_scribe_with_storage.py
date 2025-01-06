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

from chronicler.scribe.telegram_scribe import TelegramScribe
from chronicler.storage.interface import StorageAdapter, User, Topic, Message, Attachment
from chronicler.storage.git import GitStorageAdapter
from chronicler.scribe.interface import ScribeConfig, MessageConverter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@pytest.fixture
def telegram_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    logger.debug(f"TELEGRAM_BOT_TOKEN: {'set' if token else 'not set'}")
    if not token:
        pytest.skip("TELEGRAM_BOT_TOKEN not set")
    return token

@pytest.fixture
def github_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    logger.debug(f"GITHUB_TOKEN: {'set' if token else 'not set'}")
    if not token:
        pytest.skip("GITHUB_TOKEN not set")
    return token

@pytest.fixture
def github_repo() -> str:
    repo = os.getenv("GITHUB_TEST_REPO")
    logger.debug(f"GITHUB_TEST_REPO: {repo if repo else 'not set'}")
    if not repo:
        pytest.skip("GITHUB_TEST_REPO not set")
    # Remove https://github.com/ if present
    repo = repo.replace("https://github.com/", "")
    # Remove .git if present
    repo = repo.replace(".git", "")
    logger.debug(f"Using GitHub repo: {repo}")
    return repo

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

@pytest.fixture
def test_topic_name() -> str:
    topic_name = os.getenv("TELEGRAM_TEST_TOPIC_NAME")
    logger.debug(f"TELEGRAM_TEST_TOPIC_NAME: {topic_name if topic_name else 'not set'}")
    if not topic_name:
        pytest.skip("TELEGRAM_TEST_TOPIC_NAME not set")
    return str(topic_name)

@pytest_asyncio.fixture
async def bot(telegram_token: str) -> AsyncGenerator[Bot, None]:
    async with Bot(telegram_token) as bot:
        yield bot

@pytest_asyncio.fixture
async def storage(github_token: str, github_repo: str) -> AsyncGenerator[StorageAdapter, None]:
    storage = GitStorageAdapter(Path("./test_storage"))
    # Initialize with test user
    test_user = User(id="test_user", name="Test User")
    await storage.init_storage(test_user)
    # Now set GitHub config
    await storage.set_github_config(github_token, github_repo)
    yield storage

def create_test_image() -> bytes:
    """Create a small test image for media tests"""
    from PIL import Image
    import io
    
    # Create a small 10x10 red image
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

@pytest_asyncio.fixture
async def scribe(telegram_token: str, storage: StorageAdapter) -> AsyncGenerator[TelegramScribe, None]:
    config = ScribeConfig(
        telegram_token=telegram_token,
        admin_users=[12345]  # Placeholder admin user
    )
    scribe = TelegramScribe(config=config, storage=storage)
    await scribe.start()
    yield scribe
    await scribe.stop()

@pytest.mark.asyncio
async def test_telegram_scribe_with_git_storage(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    test_topic_name: str,
    bot: Bot,
    storage: GitStorageAdapter
):
    """Test that messages are properly stored in Git storage"""
    logger.info("Starting live integration test with Git storage")
    
    # Create topic with name and group info
    topic = Topic(
        id=test_topic_id, 
        name=test_topic_name,
        metadata={
            'source': 'telegram',
            'chat_id': test_group_id,
            'chat_title': 'chronicler-dev'
        }
    )
    await storage.create_topic(topic, ignore_exists=True)
    
    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)
    
    # Create a unique test message
    test_message = f"Test message with Git storage - {datetime.now()}"
    logger.info(f"Sending test message: {test_message}")
    
    # Send a test message
    message = await bot.send_message(
        chat_id=test_group_id,
        text=test_message,
        message_thread_id=int(test_topic_id)
    )
    
    # Process the message
    update = Update(update_id=1, message=message)
    storage_message = await MessageConverter.to_storage_message(message)
    logger.info(f"Chat title: {storage_message.metadata.get('chat_title', 'None')}")
    logger.info(f"Chat type: {storage_message.metadata.get('chat_type', 'None')}")
    logger.info(f"Chat ID: {storage_message.metadata.get('chat_id', 'None')}")
    logger.info(f"Messages file path: {storage.repo_path / 'telegram' / storage_message.metadata['chat_title'] / test_topic_name / GitStorageAdapter.MESSAGES_FILE}")
    # Update the chat_title in the message metadata
    storage_message.metadata['chat_title'] = 'chronicler-dev'
    await scribe.handle_message(update)
    
    # Wait for message to be processed and saved
    await asyncio.sleep(2)
    
    # Verify message was stored
    messages_file = storage.repo_path / "telegram" / storage_message.metadata['chat_title'] / test_topic_name / GitStorageAdapter.MESSAGES_FILE
    logger.info(f"Checking file: {messages_file}")
    assert messages_file.exists(), "Messages file not found"
    content = messages_file.read_text()
    logger.info(f"File contents: {content}")
    assert "Test message with Git storage" in content, "Test message not found in storage"

@pytest.mark.asyncio
async def test_telegram_scribe_media_with_git_storage(
    scribe: TelegramScribe,
    test_group_id: int,
    test_topic_id: str,
    test_topic_name: str,
    bot: Bot,
    storage: GitStorageAdapter
):
    """Test that media messages are properly stored in Git storage"""
    logger.info("Starting live integration test with Git storage for media messages")
    
    # Create topic with name and group info
    topic = Topic(
        id=test_topic_id, 
        name=test_topic_name,
        metadata={
            'source': 'telegram',
            'chat_id': test_group_id,
            'chat_title': 'chronicler-dev'
        }
    )
    await storage.create_topic(topic, ignore_exists=True)
    
    # Configure the test group
    scribe.configure_group(test_group_id, test_topic_id)
    
    # Create a test photo message
    test_caption = f"Test photo message - {datetime.now()}"
    logger.info(f"Sending test photo with caption: {test_caption}")
    
    # Create a small test image
    image_data = create_test_image()
    
    # Send a photo message
    message = await bot.send_photo(
        chat_id=test_group_id,
        photo=image_data,
        caption=test_caption,
        message_thread_id=int(test_topic_id)
    )
    
    # Process the message
    update = Update(update_id=1, message=message)
    storage_message = await MessageConverter.to_storage_message(message)
    logger.info(f"Chat title: {storage_message.metadata.get('chat_title', 'None')}")
    logger.info(f"Chat type: {storage_message.metadata.get('chat_type', 'None')}")
    logger.info(f"Chat ID: {storage_message.metadata.get('chat_id', 'None')}")
    logger.info(f"Messages file path: {storage.repo_path / 'telegram' / storage_message.metadata['chat_title'] / test_topic_name / GitStorageAdapter.MESSAGES_FILE}")
    # Update the chat_title in the message metadata
    storage_message.metadata['chat_title'] = 'chronicler-dev'
    await scribe.handle_message(update)
    
    # Wait for message to be processed and saved
    await asyncio.sleep(2)
    
    # Send a sticker message
    sticker_message = await bot.send_sticker(
        chat_id=test_group_id,
        sticker="CAACAgEAAxkBAAEwZZ1ncNik9eL1aexK9If_Tjc72hhIggAC2AIAAlCDWUeaKuTaRf5AajYE",  # Web3Titans sticker
        message_thread_id=int(test_topic_id)
    )
    
    # Process the sticker message
    sticker_update = Update(update_id=2, message=sticker_message)
    storage_sticker_message = await MessageConverter.to_storage_message(sticker_message)
    # Update the chat_title in the message metadata
    storage_sticker_message.metadata['chat_title'] = 'chronicler-dev'
    await scribe.handle_message(sticker_update)
    
    # Wait for sticker message to be processed and saved
    await asyncio.sleep(2)
    
    # Verify message and media were stored
    messages_file = storage.repo_path / "telegram" / storage_message.metadata['chat_title'] / test_topic_name / GitStorageAdapter.MESSAGES_FILE
    logger.info(f"Checking file: {messages_file}")
    assert messages_file.exists(), "Messages file not found"
    content = messages_file.read_text()
    logger.info(f"File contents: {content}")
    assert "Test photo message" in content, "Test caption not found in storage"
    
    # Verify photo file exists with new naming format
    photo_id = message.photo[-1].file_id
    photo_dir = storage.repo_path / "telegram" / storage_message.metadata['chat_title'] / test_topic_name / "attachments" / "jpg"
    photo_file = photo_dir / f"{message.message_id}_{photo_id}.jpg"
    assert photo_file.exists(), "Photo file not found"
    
    # Verify sticker file exists
    sticker_id = sticker_message.sticker.file_id
    sticker_dir = storage.repo_path / "telegram" / storage_message.metadata['chat_title'] / test_topic_name / "attachments" / "webp"
    sticker_file = sticker_dir / f"{sticker_message.message_id}_{sticker_id}.webp"
    assert sticker_file.exists(), "Sticker file not found"
    
    # Verify sticker metadata in messages.jsonl
    assert sticker_message.sticker.file_id in content, "Sticker ID not found in message metadata"
    assert sticker_message.sticker.set_name in content, "Sticker set name not found in message metadata"
    
    # Sync with GitHub
    await storage.sync()
    
    # Wait a bit for GitHub to process the push
    await asyncio.sleep(5)
    
    # TODO: Add GitHub API check to verify files exist in the repository 