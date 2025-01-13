# Chronicler Development Guide

This directory contains development documentation for the Chronicler project.

## Key Documentation Files

1. `ARCHITECTURE.md`: Overview of the pipeline-based architecture
2. `BACKLOG.md`: Development roadmap and known issues
3. `CHECKLIST.md`: Static development checklist (must follow for all changes)
4. `CONVENTIONS.md`: Code style, workflow, and development conventions
5. `IMPLEMENTATION.md`: Detailed documentation of components and APIs
6. `PRD.template.md`: Template for Product Requirements Document

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

## Branch-Specific Development Flow

**Important**: Create a checklist from [CHECKLIST.template.md](.cursor/CHECKLIST.template.md) for ALL changes.

1. Create feature branch from develop:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```
2. Initialize branch documentation:
   ```bash
   mkdir -p .cursor/scratch/feature/your-feature-name
   # Use git commands to maintain history
   git mv .cursor/PRD.template.md .cursor/scratch/feature/your-feature-name/PRD.md
   git mv .cursor/CHECKLIST.md .cursor/scratch/feature/your-feature-name/CHECKLIST.md
   # Restore the templates
   git checkout HEAD .cursor/PRD.template.md .cursor/CHECKLIST.md
   ```
3. Write tests first (TDD)
4. Implement changes following [CONVENTIONS.md](CONVENTIONS.md) with:
   1. Comprehensive logging
   2. Exception handling
   3. Type hints
   4. Docstrings
5. Run all tests
6. Review checklist items
7. When completing an item:
   1. Update status in PRD.md or CHECKLIST.md (🕔 -> ✅)
   2. Run the status update script:
      ```bash
      .cursor/scripts/status-update.sh <file> <item> <old_status> <new_status> <description>
      # Example:
      .cursor/scripts/status-update.sh .cursor/docs/feature/your-feature/PRD.md "4.3.2" "🕔" "✅" "Add logging to core components"
      ```
8. Submit PR to develop branch

## Scope-Based Development

To start a new development session:

1. Define scope using the following template:
   ```
   📋 SCOPE DEFINITION
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
     🛑 STOP: Scope deviation detected
     While implementing requirement X.Y (Description)
     Found: [What was discovered]
     Recommendation: Add to BACKLOG.md - [Reason]
     ```
   - Scope changes require explicit approval:
     ```
     🚨 SCOPE CHANGE REQUESTED
     Current: Requirement X.Y (Description)
     Change: [What needs to change]
     Impact: [What would change]
     Risks: [What could go wrong]
     Timeline: [How it affects delivery]
     Proceed? [y/n]
     ```

4. Example scope:
   ```
   📋 SCOPE DEFINITION
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
   ```

## Core Components
See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

1. `pipeline/`: Core pipeline architecture
2. `processors/`: Message processors
3. `storage/`: Storage implementation
4. `transports/`: I/O handlers

## Testing Strategy
See [CONVENTIONS.md](CONVENTIONS.md) for detailed testing guidelines.

- Unit tests: Test components in isolation
- Mock tests: Test integration with mocked services
- Live tests: Test with real external services