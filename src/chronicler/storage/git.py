from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid
from typing import Generator, Any
import logging

from chronicler.storage.interface import (
    StorageAdapter, User, Topic, Message, 
    Attachment
)
from chronicler.storage.messages import MessageStore

logger = logging.getLogger(__name__)

class GitStorageAdapter(StorageAdapter):
    """Git-based storage implementation"""
    
    MESSAGES_FILE = "messages.jsonl"  # Changed from messages.md
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self._repo = None
        self._user = None
        self.repo_path = None
        self._initialized = False
    
    def __await__(self) -> Generator[Any, None, 'GitStorageAdapter']:
        """Make the adapter awaitable after initialization"""
        if not self._initialized:
            raise RuntimeError("Must call init_storage() before awaiting adapter")
        yield
        return self
    
    async def init_storage(self, user: User) -> 'GitStorageAdapter':
        """Initialize a git repository for the user"""
        logger.info(f"Initializing storage for user {user.id}")
        self._user = user
        self.repo_path = self.base_path / f"{user.id}_journal"
        
        # Create base directories
        logger.debug(f"Creating repository structure at {self.repo_path}")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        topics_dir = self.repo_path / "topics"
        topics_dir.mkdir(exist_ok=True)
        
        # Initialize metadata file
        metadata_path = self.repo_path / "metadata.yaml"
        if not metadata_path.exists():
            with open(metadata_path, 'w') as f:
                yaml.dump({
                    'user_id': user.id,
                    'topics': {}
                }, f)
        
        # Initialize git repo
        if not (self.repo_path / ".git").exists():
            self._repo = Repo.init(self.repo_path, initial_branch='main')
            self._repo.index.add(['topics', 'metadata.yaml'])
            self._repo.index.commit("Initial repository structure")
        else:
            self._repo = Repo(self.repo_path)
        
        self._initialized = True
        return self
    
    async def create_topic(self, topic: Topic, ignore_exists: bool = False) -> None:
        """Create a new topic directory with basic structure"""
        logger.info(f"Creating topic {topic.id} with name '{topic.name}'")
        if '/' in topic.id:
            logger.error(f"Invalid topic ID '{topic.id}': contains '/'")
            raise ValueError("Topic ID cannot contain '/'")
            
        topic_path = self.repo_path / "topics" / topic.id
        if topic_path.exists() and not ignore_exists:
            logger.error(f"Topic {topic.id} already exists")
            raise ValueError(f"Topic {topic.id} already exists")
            
        logger.debug(f"Creating topic directory structure at {topic_path}")
        topic_path.mkdir(parents=True, exist_ok=True)
        (topic_path / self.MESSAGES_FILE).touch()
        (topic_path / "media").mkdir(exist_ok=True)
        
        # Update metadata
        metadata_path = self.repo_path / "metadata.yaml"
        logger.debug(f"Updating metadata for topic {topic.id}")
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        metadata['topics'][topic.id] = {
            'name': topic.name,
            'created_at': datetime.utcnow().isoformat(),
            **(topic.metadata or {})
        }
        logger.debug(f"Topic metadata: {metadata['topics'][topic.id]}")
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
            
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.index.add([f'topics/{topic.id}', 'metadata.yaml'])
        self._repo.index.commit(f"Created topic: {topic.name}")
    
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic's messages.jsonl file"""
        logger.info(f"Saving message to topic {topic_id}")
        logger.debug(f"Message content length: {len(message.content)} chars")
        topic_path = self.repo_path / "topics" / topic_id
        if not topic_path.exists():
            logger.error(f"Topic {topic_id} does not exist")
            raise ValueError(f"Topic {topic_id} does not exist")
            
        messages_file = topic_path / self.MESSAGES_FILE
        # Load existing messages and append new one
        existing = MessageStore.load_messages(messages_file)
        MessageStore.save_messages(messages_file, existing + [message])
        
        if not self._repo:
            self._repo = Repo(self.repo_path)
            
        self._repo.index.add([f'topics/{topic_id}/{self.MESSAGES_FILE}'])
        
        # Get topic name from metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        topic_name = metadata['topics'][topic_id]['name']
        
        self._repo.index.commit(f"Added message to topic: {topic_name}")
    
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment to the topic's media directory"""
        logger.info(f"Saving attachment {attachment.filename} to topic {topic_id}")
        topic_path = self.repo_path / "topics" / topic_id
        if not topic_path.exists():
            logger.error(f"Topic {topic_id} does not exist")
            raise ValueError(f"Topic {topic_id} does not exist")
            
        media_path = topic_path / "media"
        file_path = media_path / attachment.filename
        
        # Save the file if we have data
        if attachment.data:
            logger.debug(f"Writing {len(attachment.data)} bytes to {file_path}")
            with open(file_path, 'wb') as f:
                f.write(attachment.data)
                
            if not self._repo:
                self._repo = Repo(self.repo_path)
            logger.debug(f"Committing attachment {attachment.filename}")
            self._repo.index.add([str(file_path.relative_to(self.repo_path))])
            self._repo.index.commit(f"Added attachment: {attachment.filename}")
        else:
            logger.debug(f"No data to write for attachment {attachment.filename}")
    
    async def sync(self) -> None:
        """Synchronize with remote"""
        logger.info("Syncing with remote repository")
        if not self._repo:
            self._repo = Repo(self.repo_path)
        
        # Push changes to remote if available
        if 'origin' in self._repo.remotes:
            try:
                logger.debug("Fetching from remote")
                self._repo.git.fetch('origin')
                
                # Check if we need to pull
                if self._repo.is_dirty() or self._repo.head.ref.commit != self._repo.refs['origin/main'].commit:
                    logger.debug("Changes detected, pulling with rebase")
                    self._repo.git.pull('--rebase', 'origin', 'main')
                
                logger.debug("Pushing changes to remote")
                self._repo.git.push('-u', 'origin', 'main')
            except Exception as e:
                logger.error(f"Git sync failed: {e}")
                raise
    
    def add_remote(self, name: str, url: str) -> None:
        """Add a remote repository"""
        logger.info(f"Adding remote '{name}' with URL: {url}")
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.create_remote(name, url)

    async def set_github_config(self, token: str, repo: str) -> None:
        """Set GitHub configuration"""
        logger.info("Setting GitHub configuration")
        if not self._repo:
            logger.error("Repository not initialized")
            raise RuntimeError("Must initialize repository first")

        # Update remote URL with token
        remote_url = f"https://{token}@github.com/{repo}.git"
        if 'origin' in self._repo.remotes:
            self._repo.delete_remote('origin')
        self._repo.create_remote('origin', remote_url)
        
        # Save config in metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        metadata['github'] = {
            'repo': repo,
            # Don't save token in metadata for security
        }
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
            
        self._repo.index.add(['metadata.yaml'])
        self._repo.index.commit("Updated GitHub configuration") 