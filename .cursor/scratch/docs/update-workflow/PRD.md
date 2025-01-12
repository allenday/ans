# Workflow Update PRD

## Overview
Implement a branch-specific development workflow with clear state tracking in Chronicler's AI assistant. This update will standardize how features are developed by introducing a structured process using branch-specific scratch directories and explicit state tracking, while maintaining the AI's existing capabilities.

## Current State
0.1. prompt.md contains good content but lacks structured workflow guidance
0.2. No standardized process for branch-specific development tracking
0.3. No clear mechanism for tracking implementation progress
0.4. Development state is not persisted between sessions
0.5. Branch naming conventions exist but aren't enforced

## Requirements

### Core Updates
1.1. ✅ Rename prompt.md to PROMPT.md for consistency
1.2. ✅ Preserve existing AI role definition and core principles
1.3. ✅ Maintain current tool usage guidelines and restrictions
1.4. ✅ Keep existing communication and response formats
1.5. ✅ Update AI to understand and enforce branch naming conventions
1.6. ✅ Consolidate branch naming conventions in CONVENTIONS.md and reference from PROMPT.md
1.7. ✅ Reorganize CONVENTIONS.md into Process Documentation and Technical Style Guide sections

### New Features
2.1. ✅ Implement branch-specific workflow initialization
  ```
  .cursor/scratch/{type}/{branch-name}/
  ├── CHECKLIST.md  # Created from CHECKLIST.template.md, starts as 🕔
  └── PRD.md        # Created from PRD.template.md
  ```
2.2. ✅ Add state tracking system (🕔 -> ✅)
2.3. ✅ Create templates at .cursor/PRD.template.md and .cursor/CHECKLIST.template.md
2.4. ✅ Add workflow initialization commands
2.5. ✅ Implement scope-to-PRD conversion
2.6. ✅ Add branch state persistence

### Integration Points
3.1. ✅ Update .cursor/README.md to document new workflow
3.2. ✅ Update root README.md to reference .cursor documentation
3.3. ✅ Align with existing git-workflow.md conventions
3.4. ✅ Ensure compatibility with current development process
3.5. ✅ Integrate with existing test procedures
3.6. ✅ Update related .cursor documentation
3.7. ✅ Perform MECE review of all .cursor documentation
   - Audited all documents for completeness and overlap
   - Ensured clear boundaries between documents
   - Verified cross-references and naming consistency
   - Removed redundant docs.md file
   - Updated all emoji-based patterns for consistency
3.8. ✅ Rename .cursor/PRD.md to .cursor/PRD.template.md
3.9. ✅ Rename .cursor/CHECKLIST.md to .cursor/CHECKLIST.template.md
3.10. ✅ Update docs to reflect te renames in 3.8 and 3.9
3.11. ✅ Add SESSION.md template for tracking current task and progress between sessions
3.12. ✅ Update all docs to indicate that `git {mv,rm}` is to be used over `{mv,rm}` for maintaining proper git history

## Success Criteria
4.1. AI automatically initializes branch-specific scratch directory
4.2. AI maintains state tracking across sessions
4.3. AI enforces branch naming conventions
4.4. AI preserves all existing capabilities
4.5. Process is documented and easily followed
4.6. Branch state persists between sessions
