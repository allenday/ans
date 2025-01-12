# Development Conventions

## Process Documentation

### PRD Format
1. All requirements MUST use numbered lists for referencing
2. Each section's numbering restarts at 1
3. Reference format: "section.number" (e.g., "2.1" for first item in New Features)
4. Checkbox format: `1. 🕔 Requirement description`

### Branch Naming
1. **Format**: `{type}/{description}`
   - Type must be one of: feature, fix, docs, refactor
   - Description must be kebab-case
   - Example: `feature/add-voice-messages`

2. **Branch Types**
   - `main`: Protected, requires PR
   - `feature/*`: New features and enhancements
   - `fix/*`: Bug fixes and corrections
   - `docs/*`: Documentation updates
   - `refactor/*`: Code cleanup without behavior changes

### Git Workflow
1. **Commits**
   - Use conventional commits
   - Include scope
   - Write clear messages

2. **Pull Requests**
   - Reference issues
   - Include tests
   - Update docs
   - Clean commits

### State Tracking
1. **Branch State**
   - Use branch-specific scratch directory
   - Track progress in PRD.md (🕔 -> ✅)
   - Document scope changes

2. **Documentation State**
   - Keep documentation in sync with code
   - Update related docs in same PR
   - Cross-reference related changes

## Technical Style Guide

### Code Style
1. **Python Standards**
   - Follow PEP 8
   - Use type hints
   - Write docstrings (Google style)
   - Maximum line length: 100 characters

2. **Naming**
   - Classes: `PascalCase`
   - Functions/methods: `snake_case`
   - Variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`

### Documentation Standards
1. **Module Documentation**
   - Module docstrings explain purpose
   - Class docstrings describe behavior
   - Method docstrings include:
     - Args
     - Returns
     - Raises
     - Examples (if complex)

2. **Code Organization**
   - Follow MECE principle:
     - Methods should be mutually exclusive (no overlapping functionality)
     - Class coverage should be collectively exhaustive (no missing cases)
     - Error handling should cover all cases
   - Keep methods focused and small
   - Organize by responsibility
   - Group related functionality

### Project Structure
1. **Directory Organization**
   ```
   src/chronicler/
   ├── pipeline/      # Core components
   ├── processors/    # Message processors
   ├── storage/       # Storage system
   └── transports/    # I/O handlers
   ```

2. **Test Organization**
   ```
   tests/
   ├── 00-unit/      # Unit tests
   ├── 01-mock/      # Mock integration tests
   └── 02-live/      # Live integration tests
   ``` 