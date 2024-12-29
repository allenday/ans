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

### Bot Core
1. Message Handling
   - Private chat configuration
   - Group chat monitoring
   - Message to storage pipeline
   - Media attachment handling

2. Configuration Management
   - GitHub token setup
   - Repository configuration
   - User preferences
   - Per-group settings

3. State Management
   - User sessions
   - Configuration flows
   - Active conversations

### Interface Classes

```python
class BotConfig:
    """Bot configuration and settings"""
    token: str
    admin_users: List[int]
    github_token: Optional[str]
    github_repo: Optional[str]

class UserSession:
    """Track user interaction state"""
    user_id: int
    state: str
    context: Dict[str, Any]
    config: BotConfig

class GroupConfig:
    """Per-group settings"""
    group_id: int
    topic_id: str
    enabled: bool
    filters: Dict[str, Any]

class ChroniclerBot:
    """Main bot class"""
    async def start(self):
        """Start the bot"""
    
    async def handle_message(self, update: Update):
        """Process incoming messages"""
    
    async def handle_command(self, update: Update):
        """Handle bot commands"""
```

### Development Tasks
1. [ ] Set up bot framework with python-telegram-bot
2. [ ] Implement configuration management
3. [ ] Add private chat command handling
4. [ ] Add group chat monitoring
5. [ ] Integrate with storage system
6. [ ] Add user session management
7. [ ] Implement configuration flows
8. [ ] Add comprehensive tests
9. [ ] Document bot usage and commands

### Testing Strategy
1. Unit Tests
   - Command handling
   - Configuration management
   - Message processing

2. Integration Tests
   - Bot initialization
   - Storage integration
   - Configuration flows

3. Mock Tests
   - Telegram API interactions
   - GitHub integration
   - Message handling pipeline 