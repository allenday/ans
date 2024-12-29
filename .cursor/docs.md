# Project Documentation

## Current State

### Storage System (Completed)
- Git-based storage implementation ✓
- Topic and message organization ✓
- Local and remote repository support ✓
- JSONL format for messages ✓
- Attachment handling ✓
- Comprehensive test coverage ✓

### Core Components
- Message interface and data models ✓
- Storage adapter abstraction ✓
- GitHub integration for remote storage ✓

## Next Sprint: Telegram Bot Integration

### Requirements
1. Bot Setup and Configuration
   - Bot token management
   - User authentication
   - Command handling framework

2. Message Processing
   - Parse incoming messages
   - Create topics from conversations
   - Handle media attachments
   - Map Telegram messages to storage format

3. User Session Management
   - Track active conversations
   - Manage topic context
   - Handle user preferences

4. Storage Integration
   - Map Telegram chats to topics
   - Save messages using storage adapter
   - Handle media file downloads
   - Periodic sync with remote

### Technical Design
1. Bot Framework
   ```python
   class TelegramBot:
       async def start(self):
           """Initialize bot and start polling"""
           
       async def handle_message(self, message):
           """Process incoming messages"""
           
       async def handle_command(self, command):
           """Handle bot commands"""
   ```

2. Session Management
   ```python
   class UserSession:
       def __init__(self, user_id: str):
           self.current_topic: Optional[str] = None
           self.storage: StorageAdapter = None
   ```

3. Message Processing Pipeline
   ```python
   class MessageProcessor:
       async def process(self, message):
           """Convert Telegram message to storage format"""
           
       async def handle_media(self, message):
           """Process media attachments"""
   ```

## Testing Strategy
1. Unit Tests
   - Command parsing
   - Message conversion
   - Session management

2. Integration Tests
   - Bot initialization
   - Message handling flow
   - Storage integration

3. Live Tests
   - Real Telegram API interaction
   - End-to-end message flow

## Development Tasks
1. [ ] Set up Telegram bot framework
2. [ ] Implement basic command handling
3. [ ] Add message processing pipeline
4. [ ] Integrate with storage system
5. [ ] Add user session management
6. [ ] Implement media handling
7. [ ] Add comprehensive tests
8. [ ] Document bot usage and commands 