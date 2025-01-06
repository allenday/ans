# Chronicler Development Guide

This directory contains development documentation for the Chronicler project.

## Key Files

- `architecture.md`: Overview of the pipeline-based architecture
- `backlog.md`: Development roadmap and known issues
- `checklist.md`: **Mandatory** development checklist (must follow for all changes)
- `conventions.md`: Code style and development conventions
- `docs.md`: Detailed documentation of components and APIs
- `git-workflow.md`: Git workflow and branching strategy

## Quick Start

1. **Setup Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Bot**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run Tests**
   ```bash
   pytest tests/00-unit    # Unit tests
   pytest tests/01-mock    # Mock integration tests
   pytest tests/02-live    # Live integration tests
   ```

4. **Run Bot**
   ```bash
   python -m chronicler.pipeline.pipecat_runner --token YOUR_BOT_TOKEN --storage /path/to/storage
   ```

## Development Flow

**Important**: Follow the [Development Checklist](checklist.md) for ALL changes.

1. Create feature branch
2. Write tests first (TDD)
3. Implement changes with:
   - Comprehensive logging
   - Exception handling
   - Type hints
   - Docstrings
4. Run all tests
5. Review checklist items
6. Submit PR

## Scope-Based Development

To start a new development session:

1. Define scope using the following template:
   ```
   <SCOPE>
   GOAL: Clear one-sentence description of the goal
   CONTEXT: Any relevant context or background
   REQUIREMENTS:
   - Specific requirement 1
   - Specific requirement 2
   CONSTRAINTS:
   - Any technical or business constraints
   ACCEPTANCE:
   - Acceptance criteria 1
   - Acceptance criteria 2
   </SCOPE>
   ```

2. The AI will:
   - Create feature branch
   - Follow checklist.md step by step
   - Implement according to architecture.md
   - Follow conventions.md
   - Update backlog.md

3. Scope Control:
   - Initial scope is locked once validated
   - New requirements MUST go to backlog.md
   - AI will respond to scope creep with:
     ```
     <SCOPE_CREEP>
     ORIGINAL_SCOPE: [Brief reminder of original scope]
     NEW_REQUEST: [What was just requested]
     RECOMMENDATION: Add to backlog and complete current scope first
     RATIONALE: [Why this should wait]
     ACTION: Adding to backlog.md under Future Work
     </SCOPE_CREEP>
     ```
   - Scope changes require explicit approval:
     ```
     <SCOPE_CHANGE>
     IMPACT: [What would change]
     RISKS: [What could go wrong]
     TIMELINE: [How it affects delivery]
     APPROVE?: [y/n]
     </SCOPE_CHANGE>
     ```

4. Example scope:
   ```
   <SCOPE>
   GOAL: Add support for video note messages in Telegram
   CONTEXT: Video notes are circular, short video messages
   REQUIREMENTS:
   - Handle video note type in TelegramTransport
   - Store as MP4 files with metadata
   - Preserve duration and thumbnail
   CONSTRAINTS:
   - Must maintain backward compatibility
   - Must handle missing thumbnails
   ACCEPTANCE:
   - Video notes saved with correct format
   - Thumbnails saved separately
   - Duration preserved in metadata
   </SCOPE>
   ```

## Key Components

- `pipeline/`: Core pipeline architecture
- `processors/`: Message processors
- `storage/`: Storage implementation
- `transports/`: I/O handlers

## Testing Strategy

- Unit tests: Test components in isolation
- Mock tests: Test integration with mocked services
- Live tests: Test with real external services 