# Project Documentation Reference

## Core Documentation
The primary project documentation is located in `/docs/README.md`. Key points for AI assistance:

### Project Scope
- Telegram-based journaling system with LLM integration
- Git-based persistence (one repo per user)
- Markdown format for entries
- Support for media attachments

### Key Technical Requirements
1. Telegram Integration
   - Supergroups and topics for organization
   - Multi-participant support (human + AI)

2. Storage
   - Git-based (one commit per entry)
   - Markdown formatted
   - Media attachment support

3. LLM Integration
   - Swappable backends
   - System command interface
   - Extensible agent architecture

## Development Priorities
1. Core Telegram bot functionality
2. Git operations and storage
3. LLM service abstraction
4. Command parsing system 

# Technical Documentation

## Architecture Principles

### Adapter Pattern
We use adapters to abstract external services, allowing easy swapping of implementations:

1. **Storage Adapters**
   ```
   StorageAdapter (Interface)
   ├── GitStorageAdapter
   │   ├── GitHubStorage (Implemented)
   │   └── GitLabStorage (Future)
   └── Other Storage Implementations (Future)
   ```

2. **Message Source Adapters**
   ```
   MessageSourceAdapter (Interface)
   ├── TelegramAdapter (Next)
   ├── DiscordAdapter (Future)
   ├── TwitterAdapter (Future)
   └── Other Platform Adapters
   ```

## Component Architecture

### Storage System (Completed)
- **Core Interface**: `StorageAdapter`
  - Message persistence
  - Topic management
  - Content organization

- **Git Implementation**: `GitStorageAdapter`
  - Repository operations (init, commit)
  - Remote operations (abstract from specific providers)
  - Data format: YAML frontmatter in markdown

- **Current Provider**: `GitHubStorage`
  - GitHub-specific remote operations
  - Authentication handling
  - API integration

### Message Sources (Next)
- **Core Interface**: `MessageSourceAdapter`
  ```python
  class MessageSourceAdapter:
      async def listen(self) -> AsyncIterator[Message]
      async def reply(self, message: Message) -> None
      async def create_topic(self, name: str) -> Topic
  ```

- **Telegram Implementation** (Next)
  - Message handling
  - Session management
  - Platform-specific features

### Common Data Models
```python
@dataclass
class Message:
    content: str
    metadata: dict
    source: str  # Platform identifier
    timestamp: datetime
    attachments: list[Attachment]  # Media files

@dataclass
class Attachment:
    id: str
    type: str  # mime type
    filename: str
    data: bytes | None  # None if not yet downloaded
    url: str | None    # Source URL if available
    metadata: dict

@dataclass
class Topic:
    id: str
    name: str
    metadata: dict
``` 

## Implementation Plan

### Current Sprint: Interface Layer
1. **Core Data Models** (Next)
   ```python
   # src/chronicler/models.py
   class Message, Topic, User, Attachment
   ```

2. **Storage Interface** (Next)
   ```python
   # src/chronicler/storage/interface.py
   class StorageAdapter:
       async def init_storage(self, user: User) -> None
       async def create_topic(self, topic: Topic) -> None
       async def save_message(self, topic_id: str, message: Message) -> None
       async def save_attachment(self, topic_id: str, message_id: str, attachment: Attachment) -> None
       async def sync(self) -> None
   ```

3. **Refactor Current Implementation**
   - Move GitStorage to GitStorageAdapter
   - Implement StorageAdapter interface
   - Split GitHub-specific code to GitHubStorage

4. **Message Source Interface**
   ```python
   # src/chronicler/sources/interface.py
   class MessageSourceAdapter:
       async def listen(self) -> AsyncIterator[Message]
       async def reply(self, message: Message) -> None
       async def create_topic(self, name: str) -> Topic
       async def download_attachment(self, attachment: Attachment) -> Attachment  # Updates data field
   ```

### Future Work
- Telegram adapter implementation
- Additional storage providers (GitLab)
- Additional message sources (Discord)

### Migration Notes
- Current GitStorage implementation will need refactoring
- Keep existing tests but reorganize for new structure
- Add interface compliance tests 