from abc import abstractmethod
from pathlib import Path
from git import Repo
import yaml
import frontmatter
from datetime import datetime
import uuid
from typing import Generator, Any
import json
import shutil
from chronicler.logging import get_logger, trace_operation

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
        self.repo_path = None
        self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if storage is initialized"""
        return self._initialized
        
    def __await__(self) -> Generator[Any, None, 'GitStorageAdapter']:
        """Make the adapter awaitable after initialization"""
        if not self._initialized:
            logger.error("Attempted to await uninitialized adapter")
            raise RuntimeError("Must call init_storage() before awaiting adapter")
        yield
        return self
    
    @trace_operation('storage.git')
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
        logger.debug(f"Created base directories: {self.repo_path}, {topics_dir}")
        
        # Initialize metadata file
        metadata_path = self.repo_path / "metadata.yaml"
        if not metadata_path.exists():
            logger.debug("Creating initial metadata.yaml file")
            with open(metadata_path, 'w') as f:
                yaml.dump({
                    'user_id': user.id,
                    'topics': {}
                }, f)
        
        # Initialize git repo
        if not (self.repo_path / ".git").exists():
            logger.info("Initializing new git repository")
            self._repo = Repo.init(self.repo_path, initial_branch='main')
            self._repo.index.add(['topics', 'metadata.yaml'])
            self._repo.index.commit("Initial repository structure")
            logger.debug("Created initial commit with repository structure")
        else:
            logger.info("Using existing git repository")
            self._repo = Repo(self.repo_path)
        
        self._initialized = True
        logger.info(f"Storage initialization complete for user {user.id}")
        return self
    
    @trace_operation('storage.git')
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
            topic_path = self.repo_path / source / str(group_id) / str(topic.id)
            logger.debug(f"Using transport path: {topic_path}")
            logger.debug(f"Source: {source}, Group ID: {group_id}, Topic ID: {topic.id}")
        else:
            # Default path: topics/topic_id
            topic_path = self.repo_path / "topics" / str(topic.id)
            logger.debug(f"Using default topics path: {topic_path}")
        
        if topic_path.exists() and not ignore_exists:
            logger.error(f"Topic {topic.id} already exists at {topic_path}")
            raise ValueError(f"Topic {topic.id} already exists")
        
        try:
            # Create topic directory
            topic_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created topic directory at {topic_path}")
            
            # Create messages file
            messages_file = topic_path / self.MESSAGES_FILE
            messages_file.parent.mkdir(parents=True, exist_ok=True)
            messages_file.touch()
            logger.debug(f"Created messages file at {messages_file}")
            
            # Create attachments directory
            attachments_dir = topic_path / "attachments"
            attachments_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created attachments directory at {attachments_dir}")
            
            # Update metadata
            metadata_path = self.repo_path / "metadata.yaml"
            logger.debug(f"Updating metadata at {metadata_path}")
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = yaml.safe_load(f) or {}
            else:
                metadata = {}
            
            # Initialize sources section if needed
            if 'sources' not in metadata:
                metadata['sources'] = {}
            
            # Update group and topic mappings for sourced topics
            if topic.metadata:
                source = topic.metadata.get('source', 'default')
                group_id = str(topic.metadata.get('chat_id', 'default'))
                group_name = topic.metadata.get('chat_title', 'default')
                logger.debug(f"Updating source metadata - Source: {source}, Group: {group_name} ({group_id})")
                
                # Initialize source if needed
                if source not in metadata['sources']:
                    metadata['sources'][source] = {'groups': {}}
                
                # Update or create group entry
                if group_id not in metadata['sources'][source]['groups']:
                    metadata['sources'][source]['groups'][group_id] = {
                        'name': group_name,
                        'topics': {}
                    }
                
                # Add topic to group
                metadata['sources'][source]['groups'][group_id]['topics'][str(topic.id)] = {
                    'name': topic.name,
                    'created_at': datetime.utcnow().isoformat(),
                    'metadata': topic.metadata
                }
            else:
                logger.debug(f"Updating standard topic metadata for topic {topic.id}")
                # For non-sourced topics, store in root topics section
                if 'topics' not in metadata:
                    metadata['topics'] = {}
                metadata['topics'][str(topic.id)] = {
                    'name': topic.name,
                    'created_at': datetime.utcnow().isoformat(),
                    'metadata': topic.metadata
                }
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                yaml.dump(metadata, f)
            logger.debug("Metadata file updated successfully")
            
            # Stage changes
            if topic.metadata:
                # Create directories if they don't exist
                source_dir = self.repo_path / source
                if not source_dir.exists():
                    source_dir.mkdir(parents=True, exist_ok=True)
                
                group_dir = source_dir / str(group_id)
                if not group_dir.exists():
                    group_dir.mkdir(parents=True, exist_ok=True)
                
                # Stage each path separately
                self._repo.index.add([source])
                self._repo.index.add([f'{source}/{group_id}'])
                self._repo.index.add([str(topic_path.relative_to(self.repo_path))])
                self._repo.index.add(['metadata.yaml'])
                logger.debug("Staged all files")
            else:
                # For non-sourced topics, add everything at once
                self._repo.index.add([
                    str(topic_path.relative_to(self.repo_path)),
                    'metadata.yaml'
                ])
                logger.debug("Staged topic files and metadata")
            
            # Commit changes
            self._repo.index.commit(f"Created topic: {topic.name}")
            logger.info(f"Successfully created topic {topic.id} at {topic_path}")
            
        except Exception as e:
            logger.error(f"Failed to create topic {topic.id}: {e}", exc_info=True)
            raise
    
    @trace_operation('storage.git')
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message to a topic's messages.jsonl file"""
        logger.info(f"Saving message to topic {topic_id}")
        logger.debug(f"Message content length: {len(message.content)} chars")
        logger.debug(f"Message has {len(message.attachments) if message.attachments else 0} attachments")
        
        try:
            # Get topic info from metadata
            metadata_path = self.repo_path / "metadata.yaml"
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
                        topic_path = self.repo_path / source / group_id / str(topic_id)
                        logger.debug(f"Found {source} topic at {topic_path}")
            
            if not topic_info:
                # Non-sourced topic or not found in sources
                logger.debug("Processing non-sourced message")
                if 'topics' in metadata and str(topic_id) in metadata['topics']:
                    topic_info = metadata['topics'][str(topic_id)]
                    topic_path = self.repo_path / "topics" / str(topic_id)
                    logger.debug(f"Found topic at {topic_path}")
            
            if not topic_info:
                logger.error(f"Topic {topic_id} does not exist")
                raise ValueError(f"Topic {topic_id} does not exist")
            
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
                    attachment_paths.append(str(file_path.relative_to(self.repo_path)))
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
            
            with open(messages_file, 'a') as f:
                f.write(json.dumps(message_data) + '\n')
            
            # Stage changes
            messages_path = str(messages_file.relative_to(self.repo_path))
            self._repo.index.add([messages_path])
            logger.debug(f"Staged messages file: {messages_path}")

            if attachment_paths:
                for attachment_path in attachment_paths:
                    self._repo.index.add([attachment_path])
                    logger.debug(f"Staged attachment: {attachment_path}")

            # Commit changes
            self._repo.index.commit(f"Added message to topic: {topic_info['name']}")
            logger.info(f"Successfully saved message to topic {topic_id}")
            
        except Exception as e:
            logger.error(f"Failed to save message to topic {topic_id}: {e}", exc_info=True)
            raise
    
    @trace_operation('storage.git')
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
    
    @trace_operation('storage.git')
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
    
    @trace_operation('storage.git')
    def add_remote(self, name: str, url: str) -> None:
        """Add a remote repository"""
        logger.info(f"Adding remote '{name}' with URL: {url}")
        if not self._repo:
            self._repo = Repo(self.repo_path)
        self._repo.create_remote(name, url)

    @trace_operation('storage.git')
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