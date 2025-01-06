"""Storage coordination."""
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

from chronicler.storage.interface import User, Topic, Message, Attachment, StorageAdapter
from chronicler.storage.git import GitStorageAdapter
from chronicler.storage.filesystem import FileSystemStorage
from chronicler.storage.serializer import MessageSerializer
from chronicler.storage.telegram import TelegramAttachmentHandler

logger = logging.getLogger(__name__)

class StorageCoordinator(StorageAdapter):
    """Coordinates storage components to save messages and attachments."""
    
    def __init__(self, repo_path: Path):
        logger.info(f"COORD - Initializing storage coordinator with path: {repo_path}")
        self.repo_path = repo_path
        self.git = GitStorageAdapter(repo_path)
        self.fs = FileSystemStorage(repo_path)
        self.serializer = MessageSerializer()
        self.telegram = TelegramAttachmentHandler()
        logger.debug("COORD - All components initialized")
        
    async def init_storage(self, user: User) -> None:
        """Initialize storage system."""
        try:
            logger.info(f"COORD - Initializing storage for user: {user.name} (ID: {user.id})")
            
            # Initialize Git repository
            logger.debug("COORD - Initializing Git repository")
            await self.git.init_repo()
            
            # Create and commit initial metadata
            logger.debug("COORD - Creating initial metadata")
            metadata = {
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'metadata': user.metadata
                }
            }
            metadata_path = self.repo_path / "metadata.yaml"
            self.serializer.write_metadata(metadata_path, metadata)
            
            # Stage and commit metadata
            logger.debug("COORD - Committing initial metadata")
            await self.git.stage_files(['metadata.yaml'])
            await self.git.commit_changes("Initial commit")
            
            logger.info("COORD - Storage initialization completed successfully")
        except Exception as e:
            logger.error(f"COORD - Failed to initialize storage: {e}", exc_info=True)
            raise
        
    async def create_topic(self, topic: Topic) -> str:
        """Create a new topic."""
        try:
            logger.info(f"COORD - Creating topic: {topic.name} (ID: {topic.id})")
            
            # Read and update metadata
            logger.debug("COORD - Updating metadata")
            metadata_path = self.repo_path / "metadata.yaml"
            metadata = self.serializer.read_metadata(metadata_path)
            
            # Update metadata with topic info
            metadata = self.serializer.update_topic_metadata(
                metadata=metadata,
                topic_name=topic.name,
                topic_id=topic.id,
                source=topic.metadata['source'],
                group_id=topic.metadata['chat_id'],
                topic_metadata=topic.metadata
            )
            
            # Write updated metadata
            self.serializer.write_metadata(metadata_path, metadata)
            
            # Create topic directory
            logger.debug("COORD - Creating topic directory")
            topic_path = self.fs.get_topic_path(
                source=topic.metadata['source'],
                group_id=topic.metadata['chat_id'],
                topic_id=topic.id
            )
            
            # Stage and commit changes
            logger.debug("COORD - Committing topic creation")
            await self.git.stage_files(['metadata.yaml'])
            await self.git.commit_changes(f"Created topic: {topic.name}")
            
            logger.info(f"COORD - Successfully created topic: {topic.id}")
            return topic.id
        except Exception as e:
            logger.error(f"COORD - Failed to create topic: {e}", exc_info=True)
            raise
        
    async def save_message(self, topic_id: str, message: Message) -> None:
        """Save a message and its attachments."""
        try:
            logger.info(f"COORD - Saving message to topic {topic_id}")
            
            # Get topic path
            logger.debug("COORD - Getting topic path")
            topic_path = self.fs.get_topic_path(
                source=message.metadata['source'],
                group_id=message.metadata['chat_id'],
                topic_id=topic_id
            )
            
            # Process attachments
            attachment_paths = []
            attachment_infos = []
            
            if message.attachments:
                logger.info(f"COORD - Processing {len(message.attachments)} attachments")
                for i, attachment in enumerate(message.attachments, 1):
                    logger.debug(f"COORD - Processing attachment {i}/{len(message.attachments)}")
                    # Get attachment info
                    info = self.telegram.get_attachment_info(message, attachment)
                    attachment_infos.append(info)
                    
                    # Get file path and save attachment
                    file_path = self.fs.get_attachment_path(topic_path, info.category, *info.path_parts)
                    await self.fs.save_file(file_path, attachment.data)
                    attachment_paths.append(str(file_path.relative_to(self.repo_path)))
            
            # Update message content (e.g., emoji for stickers)
            logger.debug("COORD - Updating message content")
            self.telegram.update_message_content(message)
            
            # Create attachment metadata
            logger.debug("COORD - Creating attachment metadata")
            attachment_metadata = [{
                'id': att.id,
                'type': att.type,
                'filename': info.filename,
                'path': self.telegram.get_attachment_path_str(info)
            } for att, info in zip(message.attachments or [], attachment_infos)]
            
            # Serialize and save message
            logger.debug("COORD - Saving message to JSONL")
            message_json = self.serializer.serialize_message(message, attachment_metadata)
            messages_file = topic_path / "messages.jsonl"
            await self.fs.append_jsonl(messages_file, message_json)
            
            # Stage and commit all changes
            logger.debug("COORD - Committing changes")
            files_to_commit = [str(messages_file.relative_to(self.repo_path))] + attachment_paths
            await self.git.stage_files(files_to_commit)
            
            commit_msg = f"Added message to topic {topic_id}"
            if message.attachments:
                commit_msg += f" with {len(message.attachments)} attachments"
            await self.git.commit_changes(commit_msg)
            
            logger.info(f"COORD - Successfully saved message to topic {topic_id}")
        except Exception as e:
            logger.error(f"COORD - Failed to save message: {e}", exc_info=True)
            raise 

    async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None:
        """Save an attachment for a message."""
        try:
            logger.info(f"COORD - Saving attachment {attachment.id} for message {message_id} in topic {topic_id}")
            
            # Get topic path
            topic_path = self.fs.get_topic_path(
                source=attachment.metadata['source'],
                group_id=attachment.metadata['chat_id'],
                topic_id=topic_id
            )
            
            # Get attachment info and save
            info = self.telegram.get_attachment_info(None, attachment)
            file_path = self.fs.get_attachment_path(topic_path, info.category, *info.path_parts)
            await self.fs.save_file(file_path, attachment.data)
            
            # Stage and commit
            relative_path = str(file_path.relative_to(self.repo_path))
            await self.git.stage_files([relative_path])
            await self.git.commit_changes(f"Added attachment {attachment.id} to message {message_id}")
            
            logger.info(f"COORD - Successfully saved attachment {attachment.id}")
        except Exception as e:
            logger.error(f"COORD - Failed to save attachment: {e}", exc_info=True)
            raise

    async def sync(self) -> None:
        """Sync changes with remote repository."""
        try:
            logger.info("COORD - Syncing changes with remote")
            await self.git.push_changes()
            logger.info("COORD - Successfully synced changes")
        except Exception as e:
            logger.error(f"COORD - Failed to sync changes: {e}", exc_info=True)
            raise

    async def set_github_config(self, token: str, repo: str) -> None:
        """Configure GitHub repository settings."""
        try:
            logger.info("COORD - Setting GitHub configuration")
            await self.git.configure_remote(token, repo)
            logger.info("COORD - Successfully configured GitHub")
        except Exception as e:
            logger.error(f"COORD - Failed to set GitHub config: {e}", exc_info=True)
            raise 