# Meta-Level Command Interface PRD

## 1. Overview
Implement a powerful meta-level command interface with getopt-style argument parsing to enable efficient AI-PM interaction. This system provides single-letter aliases and standardized argument handling for streamlined development workflow control.

## 2. Mission

### 2.1. ✅ Current State
2.1.1. ✅ Commands are currently free-form text requests
2.1.2. ✅ No standardized command syntax or argument parsing
2.1.3. ✅ Interaction efficiency limited by natural language overhead

### 2.2. Required Changes
2.2.1. 🕔 Implement slash command processor with aliases
2.2.2. 🕔 Add getopt-style argument parsing
2.2.3. 🕔 Create command-specific argument sets
2.2.4. 🕔 Integrate with existing development workflow
2.2.5. 🕔 Support implicit command chaining with escaped slashes

### 2.3. Acceptance Criteria
2.3.1. 🕔 All commands work with both full names and aliases
2.3.2. 🕔 Getopt-style arguments parse correctly
2.3.3. 🕔 Command help shows all available options
2.3.4. 🕔 Invalid syntax produces helpful error messages
2.3.5. 🕔 Commands maintain development context
2.3.6. 🕔 Command chains execute in sequence with proper escaping

## 3. Implementation Plan

3.1. 🕔 Plan Development
   3.1.1. 🕔 Document command syntax specification
   3.1.2. 🕔 Define command parser behavior
   3.1.3. 🕔 Map implementation steps

3.2. Development Steps
   3.2.1. Core Commands Implementation
      3.2.1.1. ✅ /status, /s - Status tracking
         Usage:
           /s                   # Show current focus
           /s ITEM              # Show status of ITEM and focus on it
           /s -l [ITEM]         # List all items
           /s -s ITEM [STATUS]  # Set status (uses ⚡ if STATUS omitted)
           /ss ITEM [STATUS]    # Alias for /s -s
           /sl [ITEM]           # Alias for /s -l
           /sv                  # Alias for /s -v
                  
         Options:
           -l, --list           List items (all or matching pattern)
           -s, --set ITEM       Set item status (⚡ if no status given, implies -m)
           -v, --verify         Verify requirements
           -r, --recursive      Include related items (never implied)
           -m, --commit         Auto-git add files and auto-git commit changes
           -j, --json           Output in JSON format
         
         Status Values:
           🕔  Pending (0, "pending", "p")
           ⚡  In Progress (1, "start", "s")
           ✅  Complete/Done (2, "done", "d")
           ❌  Failed/Blocked (3, "block", "b")

         Examples:
           /s                   # "Current focus: 3.1.9"
           /ss 3.2.1           # Set 3.2.1 to ⚡
           /sl 3.2             # List all items under 3.2
           /sv                  # Verify current focus item
         
         Behavior:
           - Maintains focus on last referenced item
           - Updates both PRD.md and CHECKLIST.md
           - Generates conventional commits
           - Enforces valid transitions
           - Updates related items only with explicit -r
           - Hierarchical Status Rules:
             - Parent completion requires all children complete
             - Child status changes don't auto-update parent
             - Recursive operations (-r):
               - Must be explicitly requested
               - Changes propagate to all children when used
               - Example: /ss 3.2.1 done -mr (marks parent and children)
               - Example: /ss 3.2.1 done -m (marks only parent, fails if children incomplete)

      3.2.1.2. ✅ /rehash, /r - Documentation context refresh
         Usage:
           /r                  # Refresh with confirmation
           /r -q              # Quiet refresh
           /rv                # Verify docs consistency

         Options:
           -q, --quiet         Suppress reload confirmation
           -v, --verify        Verify documentation consistency
           -j, --json          Output in JSON format

         Examples:
           /r                 # "Refreshing docs in feature/meta-commands..."
                             # "Done: README.md, PRD.md updated"
           
           /r -q              # (silently refreshes)
           
           /rv                # "Verifying docs in feature/meta-commands..."
                             # "✅ All checks pass"

         Behavior:
           - Refreshes documentation context in current branch
           - Reads all .cursor/*.md files
           - Reads branch-specific PRD.md
           - Updates internal command context
           - Maintains cached state between reloads
           - Reports inconsistencies if found
           - Sets basis for subsequent commands
           - No side effects beyond context update

      3.2.1.3. 🕔 /branch, /b - Branch operations
         Usage:
           /b                  # Show current branch
           /b -n NAME          # Create new branch
           /b -l              # List branches
           /b -s NAME         # Switch to branch
           /b -d NAME         # Delete branch
           /b -b NAME         # Set base branch for new branch
           /bn NAME           # Alias for /b -n
           /bs NAME           # Alias for /b -s
           /bd NAME           # Alias for /b -d

         Options:
           -n, --new=NAME      Create new branch from current base
           -l, --list          List all branches
           -c, --current       Show current branch (default)
           -s, --switch=NAME   Switch to branch
           -d, --delete=NAME   Delete branch
           -b, --base=NAME     Set base branch for new branch
           -j, --json          Output in JSON format

         Examples:
           /b                 # "On branch feature/meta-commands"
                             # "Base: main"

           /b -l             # "Branches:"
                             # "* feature/meta-commands"
                             # "  main"
                             # "  feature/logging"

           /bn auth          # "Creating branch feature/auth from main..."
                             # "Switched to branch 'feature/auth'"

           /bs main          # "Switched to branch 'main'"
                             # "Your branch is up to date with 'origin/main'"

         Behavior:
           - Manages git branches with documentation context
           - Maintains branch naming conventions:
             - feature/* for feature branches
             - fix/* for bug fixes
             - docs/* for documentation
           - Coordinates with git operations:
             - Verifies clean working tree before switch
             - Updates documentation context after switch
             - Preserves uncommitted changes if possible
           - Error handling:
             - "Dirty working tree" with save/stash suggestion
             - "Branch exists" with switch suggestion
             - "Protected branch" for delete operations
             - "Invalid branch name" with naming guide
           - Sets context for subsequent commands
           - No side effects beyond git/doc operations

      3.2.1.5. ✅ /done, /d - Completion workflow
         Usage:
           /d [ITEM]          # Complete specific item, defaults to current focus
           /d -p              # Complete and push changes
           /d -n              # Skip verification checks

         Options:
           -p, --push          Push changes after commit
           -n, --no-verify     Skip verification
           -j, --json          Output in JSON format

         Examples:
           /d                # "Completing 3.1.9 in feature/meta-commands..."
                             # "✅ All requirements met"
                             # "Staged: PRD.md, CHECKLIST.md"
                             # "[feature/meta-commands abc123] docs: complete item 3.1.9 ✅"

           /d 3.2.1          # "Completing 3.2.1 in feature/meta-commands..."
                             # "❌ Error: Children incomplete (3.2.1.3, 3.2.1.4)"
           

         Behavior:
           - Uses current focused item if no item specified
           - Verifies all requirements are met:
             - All child items complete (if any)
             - Required files exist and are valid
             - No pending changes in required files
           - Updates status in PRD and CHECKLIST
           - Stages specified files or defaults
           - Generates conventional commit
           - Optionally pushes changes
           - Error handling:
             - "No focus item" when no item specified/focused
             - "Requirements not met" with specific failures
             - "Invalid files" when glob matches nothing
             - "Push failed" with fetch/merge suggestion
           - Sets focus for subsequent commands
           - No side effects beyond git operations

      3.2.1.6. ✅ /continue, /c - Response to companion proposals
         Usage:
           /c                  # Accept first/default proposal (usually completion)
           /c N                # Accept proposal number N
           /c ?                # Request more specific proposals

         Options:
           -j, --json          Output proposal set in JSON format

         Examples:
           Companion: "Would you like me to:
           1. Mark this as complete
           2. Further refine aspects
           3. Something else?"

           /c                 # Same as /c 1 (mark as complete)
           /c 2               # Begin refinement process
           /c ?               # "Please propose specific refinements"

         Behavior:
           - Responds to companion's most recent proposal set
           - No args implies accepting first/primary proposal
           - Numbers select specific proposals (1-based)
           - Question mark or "something else" option requests elaboration
           - Invalid numbers show error and restate proposals
           - Maintains conversation context for proposal chains
           - Can trigger automatic actions (like completion)
           - Error messages:
             - "Invalid option N, valid options are 1-K"
             - "No active proposals, try /x first"

      3.2.1.7. ✅ /examine, /x - Examine item
         Usage:
           /x                  # Examine current focus
           /x ITEM             # Examine specific item

         Options:
           -j, --json          Output in JSON format

         Examples:
           /x                 # "Examining 3.2.1.8 in feature/meta-commands:"
                             # "❌ Structure: Component relationships unclear"
                             # "❌ Completeness: Missing required elements"
                             # "✅ Consistency"
                             # "❌ Context: External dependencies undefined"
           
           /x 3.2.1         # "Examining 3.2.1 in feature/meta-commands:"
                             # "✅ All categories pass"
           
           /x invalid        # "❌ Item 'invalid' not found in feature/meta-commands"

         Behavior:
           - Examines single item in current branch scope
           - Analyzes and reports in order:
             1. structure
             2. completeness
             3. consistency 
             4. context
           - Reports pass/fail with explanations
           - Sets focus for subsequent commands
           - Provides basis for /c proposals
           - No side effects

      3.2.1.8. 🕔 /refine, /rr - Recursively refine item
      3.2.1.9. ✅ /git, /g - Git operations
         Usage:
           /g                  # Show git status
           /g -a [FILES]       # Stage files (all if no FILES given)
           /g -c [MSG]         # Commit (uses conventional format if no MSG)
           /g -p              # Push to current branch
           /g -d              # Show diff
           /g -l              # Show log
           /g -s              # Show status
           /ga [FILES]        # Alias for /g -a
           /gc [MSG]          # Alias for /g -c
           /gp                # Alias for /g -p

         Options:
           -a, --add [FILES]   Stage files (all if no FILES given)
           -c, --commit [MSG]  Commit changes (uses conventional format if no MSG)
           -p, --push         Push to current branch
           -d, --diff         Show changes
           -l, --log          Show commit history
           -j, --json         Output in JSON format
           -v, --verify       Verify commit message format

         Examples:
           /g                 # "On branch feature/meta-commands"
                             # "Changes not staged for commit:"
                             # "  modified: .cursor/docs/meta_commands/PRD.md"

           /ga PRD.md        # "Staged .cursor/docs/meta_commands/PRD.md"
           
           /gc               # "Commit message (conventional format):"
                             # "docs(meta-commands): update git command section ✨"
                             # "[feature/meta-commands abc123] 1 file changed"

           /gp               # "Pushing to origin/feature/meta-commands..."
                             # "Done: abc123..def456"

         Behavior:
           - Integrates with git workflow in current branch
           - Maintains conventional commit format
           - Coordinates with status tracking system
           - Auto-formats commit messages when no message given
           - Verifies staged files match current focus
           - Reports all operations with clear status
           - Handles errors with helpful messages:
             - "Nothing to commit" when no changes staged
             - "Invalid commit message format" with format guide
             - "Push failed" with fetch/merge suggestion
           - No side effects beyond git operations
           - Sets basis for subsequent commands

   3.2.2. 🕔 Command Parser Implementation
      3.2.2.1. 🕔 Implement getopt-style parser
      3.2.2.2. 🕔 Add combined short options support
      3.2.2.3. 🕔 Handle quoted arguments
      3.2.2.4. 🕔 Support -- terminator
      3.2.2.5. 🕔 Support command chaining
         - Space-separated commands
         - Leading slash (/) indicates new command in chain
         - Forward slashes in arguments must be escaped
         - Examples:
           Single command with path arguments:
             /status-track --file=.cursor\/docs\/meta_commands\/PRD.md
           Command chain:
             /rehash -v /status-track -g 2.1.1 /status-track -s 2.1.1 1 -m
         - Maintains execution context between commands
         - Handles errors gracefully
         - Reports chain execution status

   3.2.3. 🕔 Integration
      3.2.3.1. 🕔 Hook into development workflow
      3.2.3.2. 🕔 Add command context management
      3.2.3.3. 🕔 Implement help system

## 4. Technical Verification
4.1. 🕔 Command parser handles all syntax cases correctly
4.2. 🕔 All commands function as specified
4.3. 🕔 Help system provides clear documentation
4.4. 🕔 Error handling produces useful messages 