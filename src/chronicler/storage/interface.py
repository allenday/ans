"""Storage interface definitions."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class Message:
    """Message data."""
    content: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    id: Optional[str] = None