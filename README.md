# Chronicler - LLM-Assisted Journaling System

A Telegram-based journaling system that enables rich conversations with LLMs while preserving context in git repositories.

## Development

### Branch Rules
We follow a strict branching strategy:

1. Branch Naming:
   - `feature/*` - New features
   - `fix/*` - Bug fixes
   - `docs/*` - Documentation updates
   - `refactor/*` - Code refactoring

2. Protected Main Branch:
   - No direct pushes to `main`
   - Changes must come through Pull Requests
   - PRs require:
     - Passing CI checks
     - Code review approval
     - Up-to-date branch status

3. Workflow:
   ```bash
   # Start new work
   git checkout -b feature/your-feature-name
   
   # Make changes, then
   git add .
   git commit -m "feat: your clear commit message"
   git push -u origin feature/your-feature-name
   
   # Create PR through GitHub interface
   ```

### Development Workflow

We follow Test-Driven Development (TDD):

1. Create Feature Branch
   ```bash
   git checkout -b feature/your-feature
   ```

2. Write Tests (in order):
   - Unit tests (`tests/unit/`)
   - Mock integration tests (`tests/integration-mock/`)
   - Live integration tests (`tests/integration-live/`)

3. Implement Feature:
   - Write minimal code to make tests pass
   - Refactor while keeping tests green
   - Document in code and README

4. Push and Create PR:
   ```bash
   git push -u origin feature/your-feature
   # Create PR through GitHub interface
   ```

### Component Development Status

- [x] Storage System
  - Git-based storage with YAML frontmatter
  - Local and remote repository support
  - Comprehensive test coverage

- [ ] Telegram Bot (Next)
  - Message handling and routing
  - User session management
  - Integration with storage system

- [ ] LLM Integration (Future)
  - Context management
  - Response generation
  - Model configuration

## Project Structure
[Project structure details to be added as we develop]

## Setup
[Setup instructions to be added]

## Storage Format

Messages are stored in a git repository with the following structure:

```
user_journal/
├── metadata.yaml
└── topics/
    └── topic_name/
        ├── messages.jsonl
        └── media/
            ├── jpg/
            │   └── photo_123.jpg
            ├── webp/
            │   └── sticker_456.webp
            ├── txt/
            │   └── document_789.txt
            ├── pdf/
            ├── mp4/
            ├── mp3/
            └── ogg/
```

Each message is stored in JSONL format (one JSON object per line) with the following structure:

```json
{
    "content": "Message content here",
    "source": "telegram_user_123",
    "timestamp": "2024-01-01T12:00:00+00:00",
    "metadata": {
        "message_id": 123,
        "chat_id": -1001234567890,
        "from_user": 123456789,
        "file_ids": ["file_id_from_telegram"]
    },
    "attachments": [
        {
            "id": "photo_123",
            "type": "image/jpeg",
            "filename": "photo_123.jpg",
            "url": "topics/topic_name/media/jpg/photo_123.jpg"
        }
    ]
}
```

Key features of the storage system:
- Topics are organized by name rather than ID for better readability
- Media files are organized by type in subdirectories
- Messages reference local file paths for attachments
- Original Telegram file IDs are preserved in metadata

## Development Setup

### Git Integration Testing

For running live integration tests with GitHub:

1. Create a test repository on GitHub
2. Configure local environment:
   ```bash
   # Create .env file in project root
   echo "GITHUB_TEST_REPO=https://github.com/yourusername/test-repo.git" >> .env
   echo "GITHUB_TOKEN=your_personal_access_token" >> .env
   ```
3. Generate a Personal Access Token:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Create a token with `repo` scope
   - Copy token to .env file

### Telegram Integration Testing

For running live integration tests with Telegram:

1. Create a Telegram Bot:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Save the provided bot token

2. Set up Test Environment:
   - Create a new Telegram group for testing
   - Add your bot to the group
   - If using topics, enable forum mode in group settings
   - Create a test topic in the group

3. Get Required IDs:
   ```bash
   # Replace YOUR_BOT_TOKEN with the token from step 1
   curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
   After sending a message in your test group/topic, you'll see a response containing:
   - `message.chat.id` (Group ID, will be negative)
   - `message.message_thread_id` (Topic ID, if using topics)

4. Configure Environment:
   ```bash
   # Add to your .env file
   echo "TELEGRAM_BOT_TOKEN=your_bot_token" >> .env
   echo "TELEGRAM_TEST_GROUP_ID=your_group_id" >> .env
   echo "TELEGRAM_TEST_GROUP_NAME=your_group_name" >> .env
   echo "TELEGRAM_TEST_TOPIC_ID=your_topic_id" >> .env
   echo "TELEGRAM_TEST_TOPIC_NAME=your_topic_name" >> .env
   ```

5. Optional User API Setup (if needed):
   - Visit [https://my.telegram.org/apps](https://my.telegram.org/apps)
   - Create a new application
   - Save the `api_id` and `api_hash`
   - Add to .env:
     ```bash
     echo "TELEGRAM_APP_ID=your_app_id" >> .env
     echo "TELEGRAM_APP_HASH=your_api_hash" >> .env
     echo "TELEGRAM_USER_PHONE=your_phone" >> .env
     ```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit

# Run only mock integration tests
pytest tests/integration-mock

# Run live integration tests (requires GitHub setup)
pytest tests/integration-live
```

## Documentation
- Added `.env.example` for required configuration
- Updated README.md with setup instructions
- Updated .gitignore for environment files
