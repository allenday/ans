# Development Conventions

## Process Control

### Development Patterns
1. **PRD Structure**
   ```
   # {Feature Name} PRD
   
   ## 1. Overview
   High-level goal and alignment with Mission
   
   ## 2. Mission
   2.1. Current State
   2.2. Required Changes
   2.3. Acceptance Criteria
   
   ## 3. Implementation Plan
   3.1. Plan Development
   3.2. Development Steps (recursively refined)
   
   ## 4. Technical Verification
   Final quality checks and validation
   ```

2. **Development Cycle**
   Each implementation step follows:
   1. Test First: Write failing tests (red)
   2. Implement: Minimal code to pass tests (green)
   3. Verify: Run tests and ensure coverage
   4. Document: Update docs and docstrings
   5. Review: Check changes and group by PRD item
   6. Commit: Stage and commit with proper references

3. **Recursive Refinement**
   1. Start with high-level mission in PRD
   2. Break down into implementation steps
   3. Refine steps until actionable
   4. Use CHECKLIST.md for execution

### Development Loop
1. **Mission Definition**
   ```
   🔒 MISSION PHASE
   - Define current state
   - Specify required changes
   - Set acceptance criteria
   VIOLATION -> STOP 🛑
   ```

2. **Implementation Plan**
   ```
   🔒 PLAN PHASE
   - Break down into steps
   - Recursively refine
   - Reference CHECKLIST.md
   VIOLATION -> STOP 🛑
   ```

3. **Development Cycle**
   ```
   🔒 DEV PHASE
   - Test First (red)
   - Implement (green)
   - Document
   - Verify
   VIOLATION -> STOP 🛑
   ```

### Exception Handling
1. **Scope STOP** 🛑
   ```
   IF scope exceeds PRD item:
   - Pause development
   - Choose: new branch OR backlog
   - Document in BACKLOG.md
   ```

2. **Process STOP** 🛑
   ```
   IF process broken:
   - Steps out of order
   - State tracking lost
   - Realign with checklist
   ```

3. **Feedback Loop**
   1. Use BACKLOG.md for:
      - Capturing scope changes
      - Recording discovered improvements
      - Tracking technical debt
   2. Each entry must reference:
      - Source PRD item
      - Reason for deferral
      - Priority assessment

### State Management
1. **Status Indicators**
   1. 🕔 Pending/Not started
   2. 👷 In progress/Active development
   3. ✅ Completed/Verified

2. **Status Transitions**
   1. New items start as 🕔
   2. Update to 👷 when work begins
   3. Mark as ✅ when verified complete
   4. Commit each status change separately

3. **Documentation State**
   1. PRD.md tracks overall progress
   2. CHECKLIST.md governs implementation
   3. Cross-reference between documents

4. **Status Updates**
   1. Commit message format:
      ```
      {emoji} {action}: {description} (PRD item {X.Y.Z})
      ```
   2. Examples:
      ```
      👷 Start: Implement logging system (PRD item 3.2.1)
      ✅ Complete: Add error handling (PRD item 3.2.4)
      ```
   3. Atomic commits:
      1. One status change per commit
      2. Include PRD item reference
      3. Group related files

### Branch Management
1. **Branch Naming**
   1. Format: `{type}/{description}`
   2. Type: feature, fix, docs, refactor
   3. Description: kebab-case
   4. Example: `feature/add-voice-messages` 