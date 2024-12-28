# Architecture Overview

## Core Components

### 1. Telegram Interface
- Bot interface using `python-telegram-bot`
- Handles supergroup and topic management
- Command parsing for system controls
- Message routing to appropriate handlers

### 2. Storage Layer
- Git-based persistence using `GitPython`
- One repository per user
- Structure:
  ```
  user_journal/
  ├── topics/
  │   ├── topic_id_1/
  │   │   ├── messages.md
  │   │   └── media/
  │   └── topic_id_2/
  │       ├── messages.md
  │       └── media/
  └── metadata.yaml
  ```

### 3. LLM Integration
- Abstract interface for LLM providers
- Swappable backends (GPT-4, Claude, etc.)
- Interface:
  ```python
  class LLMProvider(Protocol):
      async def generate_response(
          self,
          messages: list[Message],
          context: Context
      ) -> str: ...
  ```

### 4. Journal Manager
- Coordinates between Telegram, Storage, and LLM
- Handles message threading and context
- Manages topic lifecycle
- Interface:
  ```python
  class JournalManager:
      async def record_message(msg: Message, topic: Topic) -> None
      async def create_topic(name: str) -> Topic
      async def get_context(topic: Topic) -> Context
  ```

## Data Flow
1. User sends message in Telegram topic
2. Bot receives message via webhook/polling
3. JournalManager:
   - Records message to git
   - Updates context
   - Routes to LLM if needed
4. Response stored and sent back to Telegram

## Configuration
- Environment variables for tokens/keys
- YAML for system configuration
- Per-user settings in git metadata

## Extension Points
1. LLM Provider interface
2. Storage backends
3. Command handlers
4. Context processors 