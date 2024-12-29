from datetime import datetime
from pathlib import Path
from typing import List

from .interface import Message

class MessageStore:
    """Handles message serialization and storage in JSONL files"""
    
    @staticmethod
    def save_messages(file_path: Path, messages: List[Message]) -> None:
        """Save multiple messages to a JSONL file"""
        with open(file_path, 'w') as f:
            for msg in messages:
                f.write(msg.to_json() + '\n')
    
    @staticmethod
    def load_messages(file_path: Path) -> List[Message]:
        """Load all messages from a JSONL file"""
        if not file_path.exists() or file_path.stat().st_size == 0:
            return []
            
        messages = []
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    messages.append(Message.from_json(line))
        return messages 