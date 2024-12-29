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
    └── topic_123/
       ├── messages.jsonl
        └── media/
```

Each message is stored in JSONL format (one JSON object per line) with the following structure:

```
# messages.jsonl
{"content": "Message content here", "source": "user", "timestamp": "2024-01-01T12:00:00+00:00", "metadata": {}}
```

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
