from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid
from typing import Generator, Any
import logging
import json
import shutil

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
        if '/' in topic.name:
            logger.error(f"Invalid topic name '{topic.name}': contains '/'")
            raise ValueError("Topic name cannot contain '/'")
        
        # Determine directory structure based on source
        if topic.metadata and ('chat_title' in topic.metadata or 'group_name' in topic.metadata):
            # Telegram-style path: telegram/group/topic
            group_name = topic.metadata.get('chat_title') or topic.metadata.get('group_name', 'default')
            topic_path = self.repo_path / "telegram" / group_name / topic.name
            logger.debug(f"Using Telegram-style path with group '{group_name}'")
        else:
            # Default path: topics/topic_name
            topic_path = self.repo_path / "topics" / topic.name
            logger.debug(f"Using default topics path")
        
        if topic_path.exists() and not ignore_exists:
            logger.error(f"Topic {topic.name} already exists at {topic_path}")
            raise ValueError(f"Topic {topic.name} already exists")
        
        # Create topic directory and files
        try:
            # Create topic directory
            topic_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created topic directory at {topic_path}")
            
            # Create messages file
            messages_file = topic_path / self.MESSAGES_FILE
            messages_file.parent.mkdir(parents=True, exist_ok=True)
            messages_file.touch()
            logger.debug(f"Created messages file at {messages_file}")
            
            # Create media/attachments directory based on path type
            if "telegram" in str(topic_path):
                attachments_dir = topic_path / "attachments"
            else:
                attachments_dir = topic_path / "media"
            attachments_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created media directory at {attachments_dir}")
            
            # Update metadata
            topic_info = {
                'id': topic.id,
                'name': topic.name,
                'path': str(topic_path.relative_to(self.repo_path)),  # Store full relative path
                'created_at': datetime.utcnow().isoformat(),
                'metadata': topic.metadata
            }
            
            # Load existing metadata or create new
            metadata_path = self.repo_path / "metadata.yaml"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = yaml.safe_load(f) or {}
            else:
                metadata = {'topics': {}}
                
            metadata['topics'][topic.id] = topic_info
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                yaml.dump(metadata, f)
            
            # Stage changes - use relative paths consistently
            if "telegram" in str(topic_path):
                telegram_dir = self.repo_path / "telegram"
                if not telegram_dir.exists():
                    telegram_dir.mkdir(parents=True, exist_ok=True)
                    self._repo.index.add(['telegram'])
                
                group_dir = telegram_dir / topic_info['path'].split('/')[1]
                if not group_dir.exists():
                    group_dir.mkdir(parents=True, exist_ok=True)
                    self._repo.index.add([str(Path('telegram') / topic_info['path'].split('/')[1])])
            else:
                topics_dir = self.repo_path / "topics"
                if not topics_dir.exists():
                    topics_dir.mkdir(parents=True, exist_ok=True)
                
            # Add all topic files
            self._repo.index.add([
                str(topic_path.relative_to(self.repo_path)),
                'metadata.yaml'
            ])
            
            # Commit changes
            self._repo.index.commit(f"Created topic: {topic.name}")
            logger.info(f"Successfully created topic {topic.name} at {topic_path}")
            
        except Exception as e:
            logger.error(f"Failed to create topic {topic.name}: {str(e)}")
            raise
    
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic's messages.jsonl file"""
        logger.info(f"Saving message to topic {topic_id}")
        logger.debug(f"Message content length: {len(message.content)} chars")
        logger.debug(f"Message has {len(message.attachments) if message.attachments else 0} attachments")
        
        try:
            # Get topic info from metadata
            metadata_path = self.repo_path / "metadata.yaml"
            with open(metadata_path) as f:
                metadata = yaml.safe_load(f) or {}
            
            if topic_id not in metadata['topics']:
                logger.error(f"Topic {topic_id} does not exist")
                raise ValueError(f"Topic {topic_id} does not exist")
            
            topic_info = metadata['topics'][topic_id]
            
            # Update group name if chat_title is available
            if message.metadata and 'chat_title' in message.metadata:
                old_path = self.repo_path / topic_info['path']
                group_name = message.metadata['chat_title']
                new_path = self.repo_path / "telegram" / group_name / topic_info['name']
                
                if old_path != new_path:
                    logger.debug(f"Updating topic path from {old_path} to {new_path}")
                    
                    # Create new directory structure
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if old_path.exists():
                        # Move contents instead of renaming directory
                        shutil.copytree(old_path, new_path, dirs_exist_ok=True)
                        shutil.rmtree(old_path)
                        
                        # Clean up empty directories
                        try:
                            old_path.parent.rmdir()  # Only removes if empty
                        except OSError:
                            pass  # Directory not empty, leave it
                    
                    topic_info['path'] = str(new_path.relative_to(self.repo_path))
                    
                    # Update metadata
                    with open(metadata_path, 'w') as f:
                        yaml.dump(metadata, f)
                    self._repo.index.add(['metadata.yaml'])
            
            topic_path = self.repo_path / topic_info['path']
            logger.debug(f"Using topic path: {topic_path}")
            
            if not topic_path.exists():
                logger.error(f"Topic directory {topic_path} does not exist")
                raise ValueError(f"Topic directory {topic_path} does not exist")
            
            # Handle attachments if present
            attachment_paths = []
            if message.attachments:
                for attachment in message.attachments:
                    # Determine media type directory
                    media_type = attachment.type.split('/')[1]  # e.g., 'jpeg' from 'image/jpeg'
                    if media_type == 'jpeg': media_type = 'jpg'
                    elif media_type == 'mpeg': media_type = 'mp3'
                    elif media_type == 'markdown': media_type = 'txt'
                    elif media_type == 'plain': media_type = 'txt'
                    
                    # Create type-specific directory under attachments/media
                    media_dir_name = "attachments" if "telegram" in str(topic_path) else "media"
                    media_dir = topic_path / media_dir_name / media_type
                    media_dir.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created media directory at {media_dir}")
                    
                    # Save the file
                    file_path = media_dir / attachment.filename
                    logger.debug(f"Saving attachment to {file_path}")
                    
                    if attachment.data:
                        logger.debug(f"Writing {len(attachment.data)} bytes to {file_path}")
                        with open(file_path, 'wb') as f:
                            f.write(attachment.data)
                        
                        # Stage the attachment file using relative path
                        rel_path = str(file_path.relative_to(self.repo_path))
                        logger.debug(f"Staging attachment at relative path: {rel_path}")
                        self._repo.index.add([rel_path])
                        
                        # Store relative path for JSON
                        attachment_paths.append({
                            'id': attachment.id,
                            'type': attachment.type,
                            'filename': attachment.filename,
                            'path': str(file_path.relative_to(topic_path))
                        })
                        
                        # Update attachment metadata
                        attachment.url = str(file_path.relative_to(self.repo_path))
                        attachment.data = None  # Clear binary data after saving
                        logger.debug(f"Saved attachment to {file_path}")
                    else:
                        logger.warning(f"No data to write for attachment {attachment.filename}")
            
            # Save message to messages.jsonl
            messages_file = topic_path / self.MESSAGES_FILE
            message_data = {
                'content': message.content,
                'source': message.source,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata,
                'attachments': attachment_paths if attachment_paths else None
            }
            
            with open(messages_file, 'a') as f:
                f.write(json.dumps(message_data) + '\n')
            logger.debug(f"Saved message to {messages_file}")
            
            # Stage the messages file using relative path
            rel_messages_path = str(messages_file.relative_to(self.repo_path))
            logger.debug(f"Staging messages file at relative path: {rel_messages_path}")
            self._repo.index.add([rel_messages_path])
            
            # Commit all changes
            self._repo.index.commit(f"Added message to topic: {topic_info['name']}")
            logger.info(f"Successfully saved message to topic {topic_id}")
            
        except Exception as e:
            logger.error(f"Failed to save message to topic {topic_id}: {e}", exc_info=True)
            raise
    
    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment to the topic's attachments directory"""
        logger.info(f"Saving attachment {attachment.filename} to topic {topic_id}")
        
        # Get topic info from metadata
        metadata_path = self.repo_path / "metadata.yaml"
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f) or {}
        
        if topic_id not in metadata['topics']:
            logger.error(f"Topic {topic_id} does not exist")
            raise ValueError(f"Topic {topic_id} does not exist")
            
        topic_info = metadata['topics'][topic_id]
        topic_path = self.repo_path / topic_info['path']
        
        if not topic_path.exists():
            logger.error(f"Topic directory {topic_path} does not exist")
            raise ValueError(f"Topic directory {topic_path} does not exist")
        
        # Determine media type directory
        media_type = attachment.type.split('/')[1]  # e.g., 'jpeg' from 'image/jpeg'
        if media_type == 'jpeg': media_type = 'jpg'
        elif media_type == 'mpeg': media_type = 'mp3'
        elif media_type == 'plain': media_type = 'txt'
        elif media_type == 'markdown': media_type = 'txt'
        elif media_type == 'octet-stream':
            # For binary files, use extension from filename or 'bin' as default
            ext = Path(attachment.filename).suffix.lstrip('.')
            media_type = ext if ext else 'bin'
        
        # Create type-specific directory under attachments/media
        media_dir_name = "attachments" if "telegram" in str(topic_path) else "media"
        media_dir = topic_path / media_dir_name / media_type
        media_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created media directory at {media_dir}")
        
        # Always use the original filename
        filename = Path(attachment.filename).name
        logger.debug(f"Using filename: {filename}")
        
        file_path = media_dir / filename
        
        # Save the file if we have data
        if attachment.data:
            logger.debug(f"Writing {len(attachment.data)} bytes to {file_path}")
            with open(file_path, 'wb') as f:
                f.write(attachment.data)
                
            # Stage and commit changes
            rel_path = str(file_path.relative_to(self.repo_path))
            self._repo.index.add([rel_path])
            self._repo.index.commit(f"Added attachment: {filename}")
            
            # Update attachment metadata with relative path
            attachment.url = str(file_path.relative_to(self.repo_path))
            attachment.data = None  # Clear binary data after saving
            logger.debug(f"Saved attachment to {file_path}")
        else:
            logger.debug(f"No data to write for attachment {filename}")
    
    async def sync(self) -> None:
        """Synchronize with remote"""
        logger.info("Syncing with remote repository")
        if not self._repo:
            self._repo = Repo(self.repo_path)
        
        # Push changes to remote if available
        if 'origin' in self._repo.remotes:
            try:
                logger.debug("Pushing changes to remote")
                self._repo.git.push('-f', 'origin', 'main')
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

    async def _update_metadata(self, topic: Topic) -> None:
        """Update metadata.yaml with topic information"""
        metadata_path = self.repo_path / "metadata.yaml"
        logger.debug(f"Updating metadata for topic {topic.id}")
        
        # Load existing metadata or create new
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = yaml.safe_load(f) or {}
        else:
            metadata = {}
        
        # Ensure topics dict exists
        if 'topics' not in metadata:
            metadata['topics'] = {}
        
        # Get group name from metadata or use default
        group_name = topic.metadata.get('group_name', 'default')
        
        # Update topic metadata with full path
        metadata['topics'][topic.id] = {
            'name': topic.name,
            'created_at': datetime.utcnow().isoformat(),
            'path': f"telegram/{group_name}/{topic.name}",  # Full path including telegram and group
            **(topic.metadata or {})
        }
        logger.debug(f"Topic metadata: {metadata['topics'][topic.id]}")
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
        
        # Stage metadata file
        self._repo.index.add(['metadata.yaml']) 