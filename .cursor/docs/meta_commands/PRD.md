# Meta-Level Command Interface PRD

## 1. Overview
Implement a powerful meta-level command interface with getopt-style argument parsing to enable efficient AI-PM interaction. This system provides single-letter aliases and standardized argument handling for streamlined development workflow control.

## 2. Mission

### 2.1. Current State
2.1.1. 🕔 Commands are currently free-form text requests
2.1.2. 🕔 No standardized command syntax or argument parsing
2.1.3. 🕔 Interaction efficiency limited by natural language overhead

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
         - --new=NAME, -n: Create new branch
         - --list, -l: List branches
         - --current, -c: Show current branch
         - --switch=NAME, -s: Switch to branch
         - --delete=NAME, -d: Delete branch
         - --base=NAME, -b: Set base branch for new branch

      3.2.1.4. 🕔 /search, /f - Find/search operations
         - --path=PATH, -p: Search path
         - --type=TYPE, -t: File type filter
         - --regex, -r: Use regex pattern

      3.2.1.5. 🕔 /debug, /g - Debug mode
         - --verbose, -v: Verbose debug output
         - --trace, -t: Enable tracing

      3.2.1.6. 🕔 /done, /d - Completion workflow
         - No args: Complete current focused item
         - --item=ITEM, -i: Item to mark as complete
         - --files=GLOB, -f: Additional files to stage
         - --push, -p: Push changes after commit
         - --no-verify, -n: Skip verification
         - Behavior:
           - Uses current focused item if no item specified
           - Verifies item requirements are met
           - Updates status in PRD and CHECKLIST
           - Stages specified files
           - Generates conventional commit
           - Optionally pushes changes
           - Example usage:
             /s              # Shows "3.1.9"
             /d             # Completes 3.1.9
             
             # Or with explicit item:
             /d -i 3.1.9
      3.2.1.7. 🕔 /continue, /c - Response to companion proposals
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

      3.2.1.8. ✅ /examine, /x - Examine item
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

      3.2.1.9. 🕔 /refine, /rr - Recursively refine item

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