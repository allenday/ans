"""Message and metadata serialization."""
from pathlib import Path
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, List

from chronicler.storage.interface import Message, Attachment

logger = logging.getLogger(__name__)

class MessageSerializer:
    """Handles message serialization and metadata management."""
    
    def serialize_message(self, message: Message, attachments: List[Dict[str, str]]) -> str:
        """Convert message to JSONL format."""
        try:
            logger.info("SER - Serializing message")
            logger.debug(f"SER - Message content length: {len(message.content) if message.content else 0}")
            logger.debug(f"SER - Attachments count: {len(attachments)}")
            
            # Create a clean copy of metadata without binary data
            message_data = {
                'content': message.content,
                'source': message.source,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata,
                'attachments': attachments  # This is already cleaned metadata from coordinator
            }
            
            # Ensure no binary data in the message
            if message_data['content'] and isinstance(message_data['content'], bytes):
                message_data['content'] = message_data['content'].decode('utf-8', errors='replace')
            
            result = json.dumps(message_data, ensure_ascii=False)
            logger.debug(f"SER - Serialized message length: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"SER - Failed to serialize message: {e}", exc_info=True)
            raise
        
    def read_metadata(self, path: Path) -> Dict[str, Any]:
        """Read metadata from YAML file."""
        try:
            logger.info(f"SER - Reading metadata from: {path}")
            try:
                with open(path) as f:
                    metadata = yaml.safe_load(f) or {}
                logger.debug(f"SER - Read metadata with {len(metadata)} top-level keys")
                return metadata
            except FileNotFoundError:
                logger.debug("SER - No existing metadata file, returning empty dict")
                return {}
        except Exception as e:
            logger.error(f"SER - Failed to read metadata from {path}: {e}", exc_info=True)
            raise
            
    def write_metadata(self, path: Path, metadata: Dict[str, Any]) -> None:
        """Write metadata to YAML file."""
        try:
            logger.info(f"SER - Writing metadata to: {path}")
            logger.debug(f"SER - Metadata has {len(metadata)} top-level keys")
            with open(path, 'w') as f:
                yaml.dump(metadata, f)
            logger.debug(f"SER - Successfully wrote metadata to {path}")
        except Exception as e:
            logger.error(f"SER - Failed to write metadata to {path}: {e}", exc_info=True)
            raise
            
    def update_topic_metadata(self, metadata: Dict[str, Any], topic_name: str, topic_id: str,
                            source: str, group_id: str, topic_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update metadata structure with topic information."""
        try:
            logger.info(f"SER - Updating topic metadata: source={source}, group={group_id}, topic={topic_id}")
            
            # Initialize sources structure if needed
            if 'sources' not in metadata:
                logger.debug("SER - Initializing sources structure")
                metadata['sources'] = {}
            if source not in metadata['sources']:
                logger.debug(f"SER - Initializing source: {source}")
                metadata['sources'][source] = {'groups': {}}
                
            # Add group and topic info
            source_data = metadata['sources'][source]
            if group_id not in source_data['groups']:
                logger.debug(f"SER - Adding new group: {group_id}")
                source_data['groups'][group_id] = {
                    'name': topic_name,
                    'topics': {}
                }
                
            # Add topic to group
            logger.debug(f"SER - Adding/updating topic {topic_id} in group {group_id}")
            source_data['groups'][group_id]['topics'][topic_id] = {
                'name': topic_name,
                'metadata': topic_metadata
            }
            
            logger.debug("SER - Successfully updated topic metadata")
            return metadata
        except Exception as e:
            logger.error(f"SER - Failed to update topic metadata: {e}", exc_info=True)
            raise 