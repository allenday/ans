"""File system storage organization."""
from pathlib import Path
from chronicler.logging import get_logger, trace_operation
from typing import List, Optional

logger = get_logger(__name__)

class FileSystemStorage:
    """Handles file system organization and operations."""
    
    def __init__(self, base_path: Path):
        logger.info(f"FS - Initializing storage with base path: {base_path}")
        self.base_path = base_path
        
    @trace_operation('storage.filesystem')
    def get_topic_path(self, source: str, group_id: str, topic_id: str) -> Path:
        """Generate and ensure topic directory path exists."""
        logger.info(f"FS - Getting topic path: source={source}, group={group_id}, topic={topic_id}")
        topic_path = self.base_path / source / str(group_id) / str(topic_id)
        try:
            topic_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"FS - Created/verified topic directory: {topic_path}")
            return topic_path
        except Exception as e:
            logger.error(f"FS - Failed to create topic directory {topic_path}: {e}", exc_info=True)
            raise
        
    @trace_operation('storage.filesystem')
    def get_attachment_path(self, topic_path: Path, category: str, *parts: str) -> Path:
        """Generate and ensure attachment path exists.
        
        Args:
            topic_path: Base topic directory
            category: Attachment category (e.g., 'sticker', 'photo')
            *parts: Additional path parts (e.g., pack name, filename)
        """
        logger.info(f"FS - Getting attachment path: category={category}, parts={parts}")
        try:
            path = topic_path / "attachments" / category / Path(*parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"FS - Created/verified attachment directory: {path.parent}")
            return path
        except Exception as e:
            logger.error(f"FS - Failed to create attachment path {path}: {e}", exc_info=True)
            raise

    @trace_operation('storage.filesystem')
    def save_file(self, path: Path, content: bytes) -> None:
        """Save file to disk."""
        try:
            logger.info(f"FS - Saving file: {path}")
            logger.debug(f"FS - File size: {len(content)} bytes")
            with open(path, 'wb') as f:
                f.write(content)
            logger.debug(f"FS - Successfully wrote file: {path}")
        except Exception as e:
            logger.error(f"FS - Failed to write file {path}: {e}", exc_info=True)
            raise
            
    @trace_operation('storage.filesystem')
    def append_jsonl(self, path: Path, content: str) -> None:
        """Append line to JSONL file."""
        try:
            logger.info(f"FS - Appending to JSONL: {path}")
            logger.debug(f"FS - Content length: {len(content)} chars")
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
            logger.debug(f"FS - Successfully appended to: {path}")
        except Exception as e:
            logger.error(f"FS - Failed to append to JSONL {path}: {e}", exc_info=True)
            raise 