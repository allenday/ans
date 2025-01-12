# Development Conventions

## Process Control

### Development Patterns
1. **Scope Definition**
   ```
   📋 SCOPE DEFINITION
   GOAL: Clear one-sentence goal
   CONTEXT: Background information
   REQUIREMENTS:
   - Requirement 1
   - Requirement 2
   CONSTRAINTS:
   - Constraint 1
   - Constraint 2
   ACCEPTANCE:
   - Criteria 1
   - Criteria 2
   ```

2. **Scope Control**
   - Deviation Detection:
     ```
     🛑 STOP: Scope deviation detected
     While implementing requirement X.Y (Description)
     Found: [What was discovered]
     Recommendation: Add to BACKLOG.md - [Reason]
     ```
   - Change Request:
     ```
     🚨 SCOPE CHANGE REQUESTED
     Current: Requirement X.Y (Description)
     Change: [What needs to change]
     Impact: [What would change]
     Risks: [What could go wrong]
     Timeline: [How it affects delivery]
     Proceed? [y/n]
     ```

### State Management
1. **Status Indicators**
   - 🕔 In progress/pending
   - ✅ Completed/verified

2. **Branch State**
   - Use branch-specific scratch directory
   - Track progress in PRD.md
   - Document scope changes

3. **Documentation State**
   - Keep documentation in sync with code
   - Update related docs in same PR
   - Cross-reference related changes

### Branch Management
1. **Branch Naming**
   - Format: `{type}/{description}`
   - Type: feature, fix, docs, refactor
   - Description: kebab-case
   - Example: `feature/add-voice-messages`

2. **Branch Types**
   - `main`: Protected, requires PR
   - `feature/*`: New features
   - `fix/*`: Bug fixes
   - `docs/*`: Documentation
   - `refactor/*`: Code cleanup

3. **Branch Documentation**
   ```
   .cursor/scratch/{type}/{branch-name}/
   ├── PRD.md        # From PRD.template.md
   └── CHECKLIST.md  # From CHECKLIST.template.md
   ```

### Security Controls
1. **Credentials**
   - Never commit secrets
   - Use environment variables
   - Document in .env.example

2. **Access Control**
   - Protected branches
   - Required reviews
   - Signed commits

## Technical Standards

### Code Style
1. **Python Standards**
   - Follow PEP 8
   - Use type hints
   - Write docstrings (Google style)
   - Maximum line length: 100

2. **Naming**
   - Classes: `PascalCase`
   - Functions: `snake_case`
   - Variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`

### Testing Requirements
1. **Test Organization**
   ```
   tests/
   ├── 00-unit/      # Unit tests
   ├── 01-mock/      # Mock tests
   └── 02-live/      # Live tests
   ```

2. **Test Coverage**
   - Unit tests required
   - Integration tests for APIs
   - End-to-end for workflows

### Documentation Requirements
1. **Module Documentation**
   - Purpose in docstrings
   - Class behavior defined
   - Method signatures complete
   - Examples for complexity

2. **Code Organization**
   - MECE principle
   - Single responsibility
   - Clear interfaces
   - Complete error handling 