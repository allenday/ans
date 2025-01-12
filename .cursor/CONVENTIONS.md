# Development Conventions

## Process Control

### Development Patterns
1. **Scope Definition**
   ```
   📋 SCOPE DEFINITION
   GOAL: Clear one-sentence goal
   CONTEXT: Background information
   REQUIREMENTS:
   1. Requirement 1
   2. Requirement 2
   CONSTRAINTS:
   1. Constraint 1
   2. Constraint 2
   ACCEPTANCE:
   1. Criteria 1
   2. Criteria 2
   ```

2. **Scope Control**
   1. Deviation Detection:
      ```
      🛑 STOP: Scope deviation detected
      While implementing requirement X.Y (Description)
      Found: [What was discovered]
      Recommendation: Add to BACKLOG.md - [Reason]
      ```
   2. Change Request:
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
   1. 🕔 In progress/pending
   2. ✅ Completed/verified

2. **Branch State**
   1. Use branch-specific scratch directory
   2. Track progress in PRD.md
   3. Document scope changes

3. **Documentation State**
   1. Keep documentation in sync with code
   2. Update related docs in same PR
   3. Cross-reference related changes

4. **Status Updates**
   1. Automatic git operations:
      1. When status changes from 🕔 to ✅:
         1. Stage modified file
         2. Create commit with message: "✅ Complete: {item_description}"
      2. When status changes from ✅ to 🕔:
         1. Stage modified file
         2. Create commit with message: "🕔 Reopen: {item_description}"
   2. Commit message format:
      1. First line: Status change and item description
      2. Body: File path and item reference (e.g., "PRD.md item 3.1.2")
   3. Atomic commits:
      1. One commit per status change
      2. Include only the status change
      3. No other file modifications

### Branch Management
1. **Branch Naming**
   1. Format: `{type}/{description}`
   2. Type: feature, fix, docs, refactor
   3. Description: kebab-case
   4. Example: `feature/add-voice-messages`

2. **Branch Types**
   1. `main`: Protected, requires PR
   2. `feature/*`: New features
   3. `fix/*`: Bug fixes
   4. `docs/*`: Documentation
   5. `refactor/*`: Code cleanup

### Security Controls
1. **Credentials**
   1. Never commit secrets
   2. Use environment variables
   3. Document in .env.example

2. **Access Control**
   1. Protected branches
   2. Required reviews
   3. Signed commits

## Technical Standards

### Code Style
1. **Python Standards**
   1. Follow PEP 8
   2. Use type hints
   3. Write docstrings (Google style)
   4. Maximum line length: 100

2. **Naming**
   1. Classes: `PascalCase`
   2. Functions: `snake_case`
   3. Variables: `snake_case`
   4. Constants: `UPPER_SNAKE_CASE`

### Testing Requirements
1. **Test Coverage**
   1. Unit tests required
   2. Integration tests for APIs
   3. End-to-end for workflows

### Documentation Requirements
1. **Module Documentation**
   1. Purpose in docstrings
   2. Class behavior defined
   3. Method signatures complete
   4. Examples for complexity

2. **Code Organization**
   1. MECE principle
   2. Single responsibility
   3. Clear interfaces
   4. Complete error handling 