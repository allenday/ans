"""Integration tests for storage processor with git integration."""
import pytest
import os
import git
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from chronicler.storage.interface import User, Topic, Message, Attachment, StorageAdapter
from chronicler.storage.coordinator import StorageCoordinator
from chronicler.processors.storage_processor import StorageProcessor
from chronicler.services.git_sync_service import GitSyncService
from chronicler.frames import TextFrame, ImageFrame, DocumentFrame, AudioFrame, VoiceFrame, StickerFrame
from contextlib import asynccontextmanager

class MockStorageCoordinator(StorageAdapter):
    """Mock storage coordinator for testing."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.initialized = False
        self.messages = []
        self.attachments = []
        self.topics = set()
        
    async def init_storage(self, user: User) -> 'StorageAdapter':
        self.initialized = True
        return self
        
    async def create_topic(self, topic_id: str, title: str = None) -> str:
        self.topics.add(topic_id)
        return topic_id
        
    async def has_topic(self, topic_id: str) -> bool:
        return topic_id in self.topics
        
    async def save_message(self, topic_id: str, message: Message) -> tuple[Path, list[Path]]:
        # Copy original metadata and only set defaults if not present
        metadata = message.metadata.copy()
        if 'direction' not in metadata:
            metadata['direction'] = 'outgoing'
        if 'is_from_bot' not in metadata:
            metadata['is_from_bot'] = False
                
        message_copy = Message(
            content=message.content,
            source=message.source,
            timestamp=message.timestamp,
            attachments=message.attachments,
            metadata=metadata
        )
        
        self.messages.append((topic_id, message_copy))
        message_path = self.repo_path / "messages" / topic_id / "messages.jsonl"
        message_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write message to JSONL file
        with open(message_path, 'a') as f:
            f.write(f"{{'content': '{message_copy.content}', 'metadata': {message_copy.metadata}}}\n")
        
        media_paths = []
        for attachment in message_copy.attachments:
            media_path = self.repo_path / "media" / topic_id / attachment.filename
            media_path.parent.mkdir(parents=True, exist_ok=True)
            # Write attachment data
            with open(media_path, 'wb') as f:
                f.write(attachment.data)
            media_paths.append(media_path)
        return message_path, media_paths
        
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        self.attachments.append((topic_id, message_id, attachment))
        
    async def sync(self) -> None:
        pass
        
    async def set_github_config(self, token: str, repo: str) -> None:
        pass
        
    def is_initialized(self) -> bool:
        return self.initialized

@pytest.fixture
def storage_path(tmp_path):
    """Create a temporary storage path."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True)
    
    # Initialize Git repository
    repo = git.Repo.init(storage_dir)
    
    # Configure Git user for commits
    with repo.config_writer() as git_config:
        git_config.set_value('user', 'name', 'Test User')
        git_config.set_value('user', 'email', 'test@example.com')
    
    # Create initial structure
    messages_dir = storage_dir / "messages"
    media_dir = storage_dir / "media"
    messages_dir.mkdir()
    media_dir.mkdir()
    
    # Add and commit initial structure
    repo.index.add([str(messages_dir), str(media_dir)])
    repo.index.commit("Initial commit")
    
    # Create and checkout main branch if it doesn't exist
    try:
        repo.git.branch('main')
    except git.exc.GitCommandError as e:
        if 'already exists' not in str(e):
            raise
    repo.git.checkout('main')
    
    return storage_dir

@pytest.fixture
def git_config():
    """Set up Git configuration for testing."""
    os.environ['GIT_REPO_URL'] = 'https://github.com/test/repo.git'
    os.environ['GIT_BRANCH'] = 'main'
    os.environ['GIT_USERNAME'] = 'test'
    os.environ['GIT_ACCESS_TOKEN'] = 'test_token'
    os.environ['GIT_SYNC_INTERVAL'] = '300'

@pytest.fixture
@asynccontextmanager
async def storage_processor(storage_path, git_config):
    """Create a storage processor with mock coordinator."""
    coordinator = MockStorageCoordinator(storage_path)
    
    # Mock git push operations
    mock_remote = MagicMock()
    mock_remote.push = MagicMock()
    
    with patch('chronicler.processors.storage_processor.StorageCoordinator', return_value=coordinator), \
         patch('git.Remote', return_value=mock_remote), \
         patch('git.Repo.remotes', new_callable=MagicMock) as mock_remotes:
        mock_remotes.origin = mock_remote
        processor = StorageProcessor(storage_path=storage_path)
        processor.git_sync_service = GitSyncService(
            git_processor=processor.git_processor,
            sync_interval=300
        )
        await processor.start()
        try:
            yield processor
        finally:
            await processor.stop()

class TestStorageIntegration:
    """Integration tests for storage processor with git integration."""
    
    @pytest.mark.asyncio
    async def test_bidirectional_messages(self, storage_processor):
        """Test handling of sent and received messages."""
        async with storage_processor as processor:
            # Test SENT message
            sent_frame = TextFrame(content="Hello from user")
            sent_frame.metadata = {
                'chat_id': '123',
                'direction': 'outgoing',
                'is_from_bot': False,
                'thread_id': '456',
                'chat_title': 'Test Chat'
            }
            await processor.process_frame(sent_frame)
            
            # Test RECEIVED message
            received_frame = TextFrame(content="Hello from bot")
            received_frame.metadata = {
                'chat_id': '123',
                'direction': 'incoming',
                'is_from_bot': True,
                'thread_id': '456',
                'chat_title': 'Test Chat'
            }
            await processor.process_frame(received_frame)
            
            # Verify both messages were saved with correct metadata
            assert len(processor.storage.messages) == 2
            sent_topic_id, sent_message = processor.storage.messages[0]
            received_topic_id, received_message = processor.storage.messages[1]
            
            assert sent_message.metadata['direction'] == 'outgoing'
            assert not sent_message.metadata['is_from_bot']
            assert received_message.metadata['direction'] == 'incoming'
            assert received_message.metadata['is_from_bot']
    
    @pytest.mark.asyncio
    async def test_multiple_media_types(self, storage_processor):
        """Test handling of various media types."""
        async with storage_processor as processor:
            media_frames = [
                ImageFrame(content=b"test_image", size=(100, 100), format="jpg"),
                DocumentFrame(content=b"test_doc", filename="test.pdf", mime_type="application/pdf"),
                AudioFrame(content=b"test_audio", duration=60, mime_type="audio/mp3"),
                VoiceFrame(content=b"test_voice", duration=30, mime_type="audio/ogg"),
                StickerFrame(content=b"test_sticker", emoji="😊", set_name="test_set")
            ]
            
            for frame in media_frames:
                frame.metadata = {
                    'chat_id': '123',
                    'direction': 'incoming',
                    'thread_id': '456',
                    'chat_title': 'Test Chat'
                }
                await processor.process_frame(frame)
            
            # Verify all media types were saved
            assert len(processor.storage.messages) == len(media_frames)
            for msg in processor.storage.messages:
                assert len(msg[1].attachments) == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage_processor):
        """Test concurrent processing of multiple frames."""
        async with storage_processor as processor:
            frames = [
                TextFrame(content=f"Message {i}")
                for i in range(5)
            ]
            for frame in frames:
                frame.metadata = {
                    'chat_id': '123',
                    'thread_id': '456',
                    'chat_title': 'Test Chat'
                }
            
            # Process frames concurrently
            await asyncio.gather(
                *[processor.process_frame(frame) for frame in frames]
            )
            
            # Verify all messages were saved
            assert len(processor.storage.messages) == len(frames)
    
    @pytest.mark.asyncio
    async def test_special_path_handling(self, storage_processor):
        """Test storage paths with spaces and special characters."""
        async with storage_processor as processor:
            frame = TextFrame(content="Test message")
            frame.metadata = {
                'chat_id': 'Group with spaces!',
                'thread_id': 'Thread & Special #Chars',
                'chat_title': 'Topic & Special #Chars'
            }
            
            await processor.process_frame(frame)
            
            # Verify message was saved successfully
            assert len(processor.storage.messages) == 1
            topic_id, message = processor.storage.messages[0]
            assert message.content == "Test message" 