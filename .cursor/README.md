# Chronicler Development Guide

This directory contains development documentation for the Chronicler project.

## Key Files

- `architecture.md`: Overview of the pipeline-based architecture
- `backlog.md`: Development roadmap and known issues
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

1. Create feature branch
2. Write tests first (TDD)
3. Implement changes
4. Add operation logging
5. Run tests
6. Submit PR

## Key Components

- `pipeline/`: Core pipeline architecture
- `processors/`: Message processors
- `storage/`: Storage implementation
- `transports/`: I/O handlers

## Testing Strategy

- Unit tests: Test components in isolation
- Mock tests: Test integration with mocked services
- Live tests: Test with real external services 