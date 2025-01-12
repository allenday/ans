from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid
from typing import Generator, Any, List
import logging
import json
import shutil
import git

from chronicler.storage.interface import (
    StorageAdapter, User, Topic, Message, 
    Attachment
)

logger = logging.getLogger(__name__)

class GitStorageAdapter(StorageAdapter):
    """Git-based storage implementation"""
    
    MESSAGES_FILE = "messages.jsonl"  # Changed from messages.md
    
    def __init__(self, base_path: Path):
        logger.info(f"Initializing GitStorageAdapter with base path: {base_path}")
        self.base_path = Path(base_path)
        self._repo = None
        self._user = None
        self._initialized = False
    
    def __await__(self) -> Generator[Any, None, 'GitStorageAdapter']:
        """Make the adapter awaitable after initialization"""
        if not self._initialized:
            logger.error("Attempted to await uninitialized adapter")
            raise RuntimeError("Must call init_storage() before awaiting adapter")
        yield
        return self
    
    async def init_storage(self, user: User) -> 'GitStorageAdapter':
        """Initialize a git repository for the user"""
        logger.info(f"Initializing storage for user {user.id}")
        self._user = user
        
        # Create base directories
        logger.debug(f"Creating repository structure at {self.base_path}")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize git repo
        if not (self.base_path / ".git").exists():
            logger.info("Initializing new git repository")
            self._repo = git.Repo.init(self.base_path)
            # Create initial commit if needed
            if not any(self._repo.heads):
                with open(self.base_path / "README.md", 'w') as f:
                    f.write("# Message Archive\n\nThis repository contains archived messages and media.")
                self._repo.index.add(["README.md"])
                self._repo.index.commit("Initial commit")
                logger.debug("Created initial commit with repository structure")
        else:
            logger.info("Using existing git repository")
            self._repo = git.Repo(self.base_path)
            
        # Ensure we're on the main branch
        if 'main' not in self._repo.heads:
            self._repo.create_head('main')
            logger.debug("Created main branch")
        self._repo.heads.main.checkout()
        logger.debug("Checked out main branch")
        
        self._initialized = True
        logger.info(f"Storage initialization complete for user {user.id}")
        return self
    
    async def create_topic(self, topic: Topic, ignore_exists: bool = False) -> None:
        """Create a new topic directory with basic structure"""
        logger.info(f"Creating topic {topic.id} with name '{topic.name}'")
        if '/' in topic.name:
            logger.error(f"Invalid topic name '{topic.name}': contains '/'")
            raise ValueError("Topic name cannot contain '/'")
        
        # Determine directory structure based on source
        if topic.metadata:
            if 'chat_id' in topic.metadata and 'source' not in topic.metadata:
                logger.error(f"Topic {topic.id} has chat_id but no source specified")
                raise ValueError("Source must be specified when chat_id is present")
            
            source = topic.metadata.get('source', 'default')
            group_id = topic.metadata.get('chat_id', 'default')
            topic_path = self.base_path / source / str(group_id) / str(topic.id)
            logger.debug(f"Using transport path: {topic_path}")
            logger.debug(f"Source: {source}, Group ID: {group_id}, Topic ID: {topic.id}")
        else:
            # Default path: topics/topic_id
            topic_path = self.base_path / "topics" / str(topic.id)
            logger.debug(f"Using default topics path: {topic_path}")
            
        # Create topic directory
        topic_path.mkdir(parents=True, exist_ok=True)
        
        # Create messages file if it doesn't exist
        messages_file = topic_path / self.MESSAGES_FILE
        if not messages_file.exists():
            messages_file.touch()
            
        # Stage and commit changes
        await self.stage_files([str(messages_file.relative_to(self.base_path))])
        await self.commit_changes(f"Created topic: {topic.name}")
    
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic's messages.jsonl file"""
        logger.info(f"Saving message to topic {topic_id}")
        logger.debug(f"Message content length: {len(message.content)} chars")
        logger.debug(f"Message has {len(message.attachments) if message.attachments else 0} attachments")
        
        try:
            # Get topic info from metadata
            metadata_path = self.base_path / "metadata.yaml"
            logger.debug(f"Reading metadata from {metadata_path}")
            with open(metadata_path) as f:
                metadata = yaml.safe_load(f) or {}
            
            # Find topic in metadata structure
            topic_info = None
            if message.metadata:
                if 'chat_id' in message.metadata and 'source' not in message.metadata:
                    logger.error(f"Message for topic {topic_id} has chat_id but no source specified")
                    raise ValueError("Source must be specified when chat_id is present")
                
                source = message.metadata.get('source')
                if source:
                    # Use the source as is, don't split by underscore
                    group_id = str(message.metadata.get('chat_id', 'default'))
                    logger.debug(f"Processing {source} message for group {group_id}")
                    if ('sources' in metadata and 
                        source in metadata['sources'] and
                        'groups' in metadata['sources'][source] and
                        group_id in metadata['sources'][source]['groups'] and
                        'topics' in metadata['sources'][source]['groups'][group_id] and
                        str(topic_id) in metadata['sources'][source]['groups'][group_id]['topics']):
                        topic_info = metadata['sources'][source]['groups'][group_id]['topics'][str(topic_id)]
                        topic_path = self.base_path / source / group_id / str(topic_id)
                        logger.debug(f"Found {source} topic at {topic_path}")
            
            if not topic_info:
                # Non-sourced topic or not found in sources
                logger.debug("Processing non-sourced message")
                if 'topics' in metadata and str(topic_id) in metadata['topics']:
                    topic_info = metadata['topics'][str(topic_id)]
                    topic_path = self.base_path / "topics" / str(topic_id)
                    logger.debug(f"Found topic at {topic_path}")
            
            if not topic_info:
                logger.error(f"Topic {topic_id} does not exist")
                raise ValueError(f"Topic {topic_id} does not exist")
            
            if not topic_path.exists():
                logger.error(f"Topic directory {topic_path} does not exist")
                raise ValueError(f"Topic directory {topic_path} does not exist")
            
            # Handle attachments if present
            files_to_commit = []
            if message.attachments:
                for attachment in message.attachments:
                    # Determine media type directory
                    media_type = attachment.type.split('/')[1]  # e.g., 'jpeg' from 'image/jpeg'
                    if media_type == 'jpeg': media_type = 'jpg'
                    elif media_type == 'mpeg': media_type = 'mp3'
                    elif media_type == 'markdown': media_type = 'txt'
                    elif media_type == 'plain': media_type = 'txt'
                    
                    logger.debug(f"Processing attachment of type {media_type}")
                    
                    # Create type-specific directory under attachments
                    media_dir_name = "attachments" if topic_info.get('metadata', {}).get('source') else "media"
                    attachments_dir = topic_path / media_dir_name / media_type
                    attachments_dir.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created media directory at {attachments_dir}")
                    
                    # Use file_id as filename with appropriate extension
                    extension = Path(attachment.filename).suffix
                    if not extension:
                        extension = f".{media_type}"
                    file_path = attachments_dir / f"{attachment.id}{extension}"
                    logger.debug(f"Saving attachment to {file_path}")
                    
                    # Save attachment data
                    with open(file_path, 'wb') as f:
                        f.write(attachment.data)
                    files_to_commit.append(str(file_path.relative_to(self.base_path)))
                    logger.debug(f"Saved attachment data to {file_path}")
            
            # Save message to messages.jsonl
            messages_file = topic_path / self.MESSAGES_FILE
            logger.debug(f"Saving message to {messages_file}")
            message_data = {
                'content': message.content,
                'source': message.source,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata
            }
            
            if message.attachments:
                message_data['attachments'] = [{
                    'id': att.id,
                    'type': att.type,
                    'original_name': att.filename
                } for att in message.attachments]
            
            # Ensure the messages file directory exists
            messages_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(messages_file, 'a') as f:
                f.write(json.dumps(message_data) + '\n')
            
            # Add messages file to files to commit
            files_to_commit.append(str(messages_file.relative_to(self.base_path)))
            
            # Stage all files
            await self.stage_files(files_to_commit)
            
            # Commit changes
            await self.commit_changes(f"Added message to topic {topic_id} with {len(message.attachments) if message.attachments else 0} attachments")
            logger.info(f"Successfully saved message to topic {topic_id}")
            
            # Return paths for testing
            return messages_file, [Path(f) for f in files_to_commit]
            
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
        
        # Find topic in metadata structure
        topic_info = None
        topic_path = None
        
        # First check in sources
        if 'sources' in metadata:
            for source, source_info in metadata['sources'].items():
                if 'groups' in source_info:
                    for group_id, group_info in source_info['groups'].items():
                        if ('topics' in group_info and 
                            str(topic_id) in group_info['topics']):
                            topic_info = group_info['topics'][str(topic_id)]
                            topic_path = self.repo_path / source / group_id / str(topic_id)
                            break
                    if topic_info:
                        break
        
        # If not found in sources, check root topics
        if not topic_info and 'topics' in metadata:
            if str(topic_id) in metadata['topics']:
                topic_info = metadata['topics'][str(topic_id)]
                topic_path = self.repo_path / "topics" / str(topic_id)
        
        if not topic_info:
            logger.error(f"Topic {topic_id} does not exist")
            raise ValueError(f"Topic {topic_id} does not exist")
        
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
        metadata = topic_info.get('metadata', {})
        if 'chat_id' in metadata and 'source' not in metadata:
            logger.error(f"Topic {topic_id} has chat_id but no source specified")
            raise ValueError("Source must be specified when chat_id is present")
        
        media_dir_name = "attachments" if metadata.get('source') else "media"
        media_dir = topic_path / media_dir_name / media_type
        media_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created media directory at {media_dir}")
        
        # Use file_id as filename with appropriate extension
        extension = Path(attachment.filename).suffix
        if not extension:
            extension = f".{media_type}"
        file_path = media_dir / f"{attachment.id}{extension}"
        logger.debug(f"Using filename: {file_path.name}")
        
        # Save the file if we have data
        if attachment.data:
            logger.debug(f"Writing {len(attachment.data)} bytes to {file_path}")
            with open(file_path, 'wb') as f:
                f.write(attachment.data)
                
            # Stage changes
            attachment_path = str(file_path.relative_to(self.repo_path))
            self._repo.index.add([attachment_path])
            logger.debug(f"Staged attachment: {attachment_path}")

            # Commit changes
            self._repo.index.commit(f"Added attachment to topic: {topic_info['name']}")
            logger.info(f"Successfully saved attachment {attachment.id} to topic {topic_id}")
        else:
            logger.debug(f"No data to write for attachment {attachment.id}")
    
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

    def is_initialized(self) -> bool:
        """Check if storage is initialized."""
        return self._initialized and self.repo_path and self.repo_path.exists() and (self.repo_path / "metadata.yaml").exists()

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

    async def stage_files(self, files: List[str]) -> None:
        """Stage files for commit"""
        logger.debug(f"Staging files: {files}")
        try:
            # Files should already be relative to repo root
            # Just verify they exist and stage them
            for file in files:
                file_path = self.base_path / file
                if not file_path.exists():
                    logger.error(f"File not found: {file_path}")
                    raise FileNotFoundError(f"File not found: {file_path}")
            
            # Stage the files using relative paths
            self._repo.index.add(files)
            logger.debug("Successfully staged files")
        except Exception as e:
            logger.error(f"Failed to stage files: {e}")
            raise

    async def commit_changes(self, message: str) -> None:
        """Commit staged changes.
        
        Args:
            message: Commit message
        """
        logger.debug(f"Committing changes with message: {message}")
        self._repo.index.commit(message)
        logger.debug("Successfully committed changes") 