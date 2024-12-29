from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid
from typing import Generator, Any

from .interface import StorageAdapter, User, Topic, Message, Attachment
from .messages import MessageStore

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
        self._user = user
        self.repo_path = self.base_path / f"{user.id}_journal"
        
        # Create base directories
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
        if '/' in topic.id:
            raise ValueError("Topic ID cannot contain '/'")
            
        topic_path = self.repo_path / "topics" / topic.id
        if topic_path.exists() and not ignore_exists:
            raise ValueError(f"Topic {topic.id} already exists")
            
        topic_path.mkdir(parents=True, exist_ok=True)
        (topic_path / self.MESSAGES_FILE).touch()
        (topic_path / "media").mkdir(exist_ok=True)
        
        # Update metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        metadata['topics'][topic.id] = {
            'name': topic.name,
            'created_at': datetime.utcnow().isoformat(),
            **(topic.metadata or {})
        }
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
            
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.index.add([f'topics/{topic.id}', 'metadata.yaml'])
        self._repo.index.commit(f"Created topic: {topic.name}")
    
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic's messages.jsonl file"""
        topic_path = self.repo_path / "topics" / topic_id
        if not topic_path.exists():
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
        topic_path = self.repo_path / "topics" / topic_id
        if not topic_path.exists():
            raise ValueError(f"Topic {topic_id} does not exist")
            
        media_path = topic_path / "media"
        file_path = media_path / attachment.filename
        
        # Save the file if we have data
        if attachment.data:
            with open(file_path, 'wb') as f:
                f.write(attachment.data)
                
            if not self._repo:
                self._repo = Repo(self.repo_path)
            self._repo.index.add([str(file_path.relative_to(self.repo_path))])
            self._repo.index.commit(f"Added attachment: {attachment.filename}")
    
    async def sync(self) -> None:
        """Synchronize with remote"""
        if not self._repo:
            self._repo = Repo(self.repo_path)
        
        # Push changes to remote if available
        if 'origin' in self._repo.remotes:
            try:
                self._repo.git.push('-u', 'origin', 'main')
            except Exception as e:
                # If push fails, try pulling first then push again
                self._repo.git.pull('--rebase', 'origin', 'main')
                self._repo.git.push('-u', 'origin', 'main')
    
    def add_remote(self, name: str, url: str) -> None:
        """Add a remote repository"""
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.create_remote(name, url) 