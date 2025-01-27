## User notes (ignore)
1. Define context, rough draft.
   1.1. Get branch type and one-phrase description from user
2. Workspace setup.
   2.1. Create branch <type>/<description>
   2.2. Make directory .cursor/docs/<type>/<description>
   2.3. Copy .cursor/PRD.template.md to .cursor/docs/<type>/<description>/PRD.md
3. Define context, working draft.
   3.1. In dialogue with user, fill contents of PRD.md and CHECKLIST.md
      3.1.1. Follow style guidelines, such as always using bulleted items for referenceability.
      3.1.2. Follow style guidelines, such as using status indicator emojis.
      3.1.3. Apply Chain-of-Thought reasoning to recursively refine PRD.md to create a hierarchical implementation plan.
   3.2. Confirm with usesr that working draft is ready for review.
4. Main loop: Test-Implement-Verify-Document-Review-Commit cycle
   4.0. Exception handling: See docs related to scope drift, scope change, and backlogging.
   4.1. DOCS:
      4.1.1. Update working items in PRD.md to in-progress (🕔 => 👷)
      4.1.2. Update working items in CHECKLIST.md to in-progress (🕔 => 👷)
   4.1. TEST: Write unit tests using red-green-refactor cycle.
   4.2. DEV: Implement required functionality.
      4.2.1. For reorganization of existing files, always use `git mv` instead of `mv` and `git rm` instead of `rm` so that history is correctly tracked.
   4.3. TEST: Ensure that unit tests pass.
   4.4. AUDIT: Tech debt avoidance.
      4.4.1. Ensure operational logging is in place.
         4.4.1.1. Required in all source files.
         4.4.1.2. Optional in all test files.
      4.4.2. Ensure that all created classes, methods, and tests have pydantic annotations.
      4.4.3. Ensure that all tests have pytest annotation marks.
      4.4.4. Ensure that tests have pytest fixtures, as needed.
      4.4.5. Ensure that all tests have sufficient coverage.
   4.5. DOCUMENT: Update docs.
      4.5.1. Ensure that all created classes, methods, and tests have docstrings.
      4.5.2. Update .cursor/docs/<type>/<description>/PRD.md to reflect status (👷 => ✅)
      4.5.3. Update .cursor/docs/<type>/<description>/CHECKLIST.md to reflect status (👷 => ✅)
   4.6. SAVE:
      4.6.1. Review modified files with `git diff`, `git status`, etc.
      4.6.1. Iteratively stage/commit changes with `git add ...` and  `git commit -m ...`
         4.6.1.1. Group files logically by PRD item number (e.g. 1.2.2.1). Referring to PRD.md and CHECKLIST.md as needed.
5. TERMINATE: Indicate to user that main loop is complete.

