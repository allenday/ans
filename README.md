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

## Project Structure
[Project structure details to be added as we develop]

## Setup
[Setup instructions to be added]