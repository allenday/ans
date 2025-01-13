from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime, timezone
import uuid
from typing import Generator, Any, Dict
import json
import shutil
from chronicler.logging import get_logger, trace_operation
import re

from chronicler.storage.interface import (
    StorageAdapter, User, Topic, Message, 
    Attachment
)

logger = get_logger("storage.git")

class GitStorageAdapter(StorageAdapter):
    """Git-based storage implementation"""
    
    MESSAGES_FILE = "messages.jsonl"  # Changed from messages.md
    
    def __init__(self, base_path: Path):
        logger.info("INIT - GitStorageAdapter", extra={
            'context': {'base_path': str(base_path)}
        })
        self.base_path = Path(base_path)
        self._repo = None
        self._user = None
        self._initialized = False
        self.repo_path = None
    
    def is_initialized(self) -> bool:
        """Check if storage is initialized"""
        return self._initialized and self._repo is not None
        
    def __await__(self) -> Generator[Any, None, 'GitStorageAdapter']:
        """Make the adapter awaitable after initialization"""
        if not self._initialized:
            logger.error("Attempted to await uninitialized adapter")
            raise RuntimeError("Must call init_storage() before awaiting adapter")
        yield
        return self
    
    @trace_operation('storage.git')
    async def init_storage(self, user: User) -> None:
        """Initialize storage for a user."""
        # Set repository path
        self.repo_path = self.base_path / f"{user.id}_journal"
        
        # Create repository directory
        self.repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize git repository if not already initialized
        if not self.is_initialized():
            self._repo = Repo.init(str(self.repo_path))
            
            # Create initial metadata
            metadata = {
                'user_id': user.id,
                'topics': {}
            }
            
            # Write metadata file
            metadata_path = self.repo_path / "metadata.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            # Add and commit metadata file
            self._repo.index.add(['.'])
            self._repo.index.commit("Initialize repository")

        self._initialized = True
    
    @trace_operation('storage.git')
    async def create_topic(self, topic: Topic) -> None:
        """Create a new topic."""
        if not self.is_initialized():
            raise RuntimeError("Must initialize repository first")
        
        # Validate topic name
        if '/' in topic.name:
            raise ValueError("Topic name cannot contain '/'")
        
        # Read current metadata
        metadata = await self._read_metadata()
        
        # Check if topic already exists
        if topic.id in metadata['topics']:
            raise ValueError(f"Topic {topic.id} already exists")
        
        # Validate source if chat_id present
        if topic.metadata and 'chat_id' in topic.metadata and 'source' not in topic.metadata:
            raise ValueError("Source must be specified when chat_id is present")
        
        # Create topic directory
        topic_dir = self.repo_path / topic.id
        topic_dir.mkdir(parents=True, exist_ok=True)
        
        # Create messages file
        messages_file = topic_dir / self.MESSAGES_FILE
        with open(messages_file, 'w') as f:
            f.write('')
        
        # Update metadata
        metadata['topics'][topic.id] = {
            'name': topic.name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'path': str(topic_dir.relative_to(self.repo_path))
        }
        if topic.metadata:
            metadata['topics'][topic.id].update(topic.metadata)
        
        # Write metadata and commit changes
        await self._write_metadata(metadata)
        
        # Add and commit topic files
        self._repo.index.add(['.'])
        self._repo.index.commit(f"Created topic {topic.name}")
    
    @trace_operation('storage.git')
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic."""
        if not self.is_initialized():
            raise RuntimeError("Must initialize repository first")

        # Read metadata to verify topic exists
        metadata = await self._read_metadata()
        if topic_id not in metadata['topics']:
            raise ValueError(f"Topic {topic_id} does not exist")

        # Validate message metadata
        if message.metadata and 'chat_id' in message.metadata and 'source' not in message.metadata:
            raise ValueError("Source must be specified when chat_id is present")

        # Get topic directory
        topic_dir = self.repo_path / topic_id
        if not topic_dir.exists():
            raise RuntimeError(f"Topic directory {topic_dir} does not exist")

        # Save message to messages file
        messages_file = topic_dir / self.MESSAGES_FILE
        message_data = {
            'id': str(uuid.uuid4()) if not hasattr(message, 'id') or not message.id else message.id,
            'content': message.content,
            'source': message.source,
            'timestamp': datetime.now(timezone.utc).isoformat() if not message.timestamp else message.timestamp.isoformat(),
            'metadata': message.metadata or {}
        }

        # Handle attachments
        if message.attachments:
            message_data['attachments'] = []
            for attachment in message.attachments:
                # Determine media type directory
                media_type = attachment.type.split('/')[0]
                media_dir = topic_dir / "media" / media_type
                media_dir.mkdir(parents=True, exist_ok=True)

                # Save attachment file
                file_ext = Path(attachment.filename).suffix
                attachment_path = media_dir / f"{attachment.id}{file_ext}"
                with open(attachment_path, 'wb') as f:
                    f.write(attachment.data)

                # Add attachment metadata
                message_data['attachments'].append({
                    'id': attachment.id,
                    'type': attachment.type,
                    'filename': attachment.filename,
                    'path': str(attachment_path.relative_to(topic_dir))
                })

        # Append message to messages file
        with open(messages_file, 'a') as f:
            f.write(json.dumps(message_data) + '\n')

        # Add and commit changes
        self._repo.index.add(['.'])
        self._repo.index.commit(f"Added message {message_data['id']} to topic {topic_id}")
    
    @trace_operation('storage.git')
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment to the topic's attachments directory"""
        if not self.is_initialized():
            raise RuntimeError("Must initialize repository first")

        # Read metadata to verify topic exists
        metadata = await self._read_metadata()
        if topic_id not in metadata['topics']:
            raise ValueError(f"Topic {topic_id} does not exist")

        # Get topic directory
        topic_dir = self.repo_path / topic_id
        if not topic_dir.exists():
            raise RuntimeError(f"Topic directory {topic_dir} does not exist")

        # Determine media type directory
        media_type = attachment.type.split('/')[0]
        media_dir = topic_dir / "media" / media_type
        media_dir.mkdir(parents=True, exist_ok=True)

        # Save attachment file
        file_ext = Path(attachment.filename).suffix
        attachment_path = media_dir / f"{attachment.id}{file_ext}"
        with open(attachment_path, 'wb') as f:
            f.write(attachment.data)

        # Add and commit changes
        self._repo.index.add(['.'])
        self._repo.index.commit(f"Added attachment {attachment.filename} to topic {topic_id}")
    
    @trace_operation('storage.git')
    async def sync(self) -> None:
        """Sync changes with remote repository."""
        if not self.is_initialized():
            raise RuntimeError("Must initialize repository first")
        
        if not self._repo.remotes:
            raise RuntimeError("No remote repository configured")
        
        # Push changes to remote
        try:
            origin = self._repo.remotes['origin']
            origin.push()
        except Exception as e:
            raise RuntimeError(f"Failed to push changes: {str(e)}")
    
    @trace_operation('storage.git')
    async def set_github_config(self, token: str, repo: str) -> None:
        """Configure GitHub remote with token auth."""
        if not self._initialized:
            raise RuntimeError("Must initialize repository first")

        logger.info("Setting GitHub configuration")
        
        remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
        self._repo.create_remote("origin", remote_url)
        
        logger.info("Successfully configured GitHub remote")

    async def _read_metadata(self) -> dict:
        """Read metadata from file."""
        metadata_path = self.repo_path / "metadata.json"
        if not metadata_path.exists():
            return {'user_id': None, 'topics': {}}
        with open(metadata_path) as f:
            return json.load(f)

    async def _write_metadata(self, metadata: dict) -> None:
        """Write metadata to file."""
        metadata_path = self.repo_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        self._repo.index.add([str(metadata_path)])
        self._repo.index.commit("Update metadata") 