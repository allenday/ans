# Cursor AI Configuration

This directory contains configuration and context files for Cursor AI assistance.

## Project Context Files
- `docs.md` - Comprehensive documentation of repository structure, implementation details, and conventions
- `architecture.md` - Key architectural decisions and constraints
- `conventions.md` - Coding and development conventions

## Project Overview

Chronicler is a Telegram bot that archives messages and media from group chats into a Git repository. Key features:

1. Storage System
   - Git-based storage implementation
   - Numerical ID-based directory structure
   - JSONL format for messages
   - Efficient attachment handling
   - GitHub integration

2. Message Organization
   - Group-based structure using chat_ids
   - Topic-based organization using topic_ids
   - Type-specific media directories
   - Human-readable name mappings

3. Implementation Details
   - See `docs.md` for complete documentation
   - Unit, integration, and mock tests
   - Comprehensive test coverage
   - Clean architecture design

## Development Guidelines

1. Code Structure
   - Follow Python best practices
   - Use type hints and docstrings
   - Maintain test coverage
   - Document architectural decisions

2. Git Workflow
   - Feature branches for new work
   - Pull requests for review
   - Comprehensive testing before merge
   - Keep documentation updated

3. Testing Strategy
   - Unit tests for core functionality
   - Integration tests for system behavior
   - Mock tests for external dependencies
   - Live tests for GitHub integration 