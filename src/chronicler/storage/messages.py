from datetime import datetime
from pathlib import Path
from typing import List
import logging

from .interface import Message

logger = logging.getLogger(__name__)

class MessageStore:
    """Handles message serialization and storage in JSONL files"""
    
    @staticmethod
    def save_messages(file_path: Path, messages: List[Message]) -> None:
        """Save multiple messages to a JSONL file"""
        logger.info(f"Saving {len(messages)} messages to {file_path}")
        with open(file_path, 'w') as f:
            for msg in messages:
                logger.debug(f"Writing message from {msg.source} at {msg.timestamp}")
                f.write(msg.to_json() + '\n')
    
    @staticmethod
    def load_messages(file_path: Path) -> List[Message]:
        """Load all messages from a JSONL file"""
        logger.info(f"Loading messages from {file_path}")
        if not file_path.exists() or file_path.stat().st_size == 0:
            logger.debug(f"No messages found in {file_path}")
            return []
            
        messages = []
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    logger.debug("Parsing message from JSONL line")
                    messages.append(Message.from_json(line))
        logger.debug(f"Loaded {len(messages)} messages")
        return messages 