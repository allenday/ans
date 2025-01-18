# Base Commands

## Document Relationships
This document defines the core command set that all aspects extend:
- Provides base command structure and options
- Defines standard command patterns
- Establishes common workflows
- Sets error handling patterns

Extended by:
- [SWE Commands](../swe/COMMANDS.md) - Software engineering commands
- [PM Commands](../pm/COMMANDS.md) - Product management commands

See also:
- [Base Prompt](./PROMPT.md) - Base prompt capabilities

## Extension Points
Aspects must implement the following:

### 1. Command Behavior
Base commands that aspects must implement:
- `/x` - Examine item
- `/rr` - Recursively refine item
- `/s` - Show/set item status

### 2. Analysis Categories
- Structure
- Completeness
- Consistency
- Context

### 3. Success Criteria
- Quality gates
- Metrics
- Standards
- Validation

### 4. Error Handling
Standard error messages:
- Not found: "Item {id} not found"
- Invalid format: "Invalid {field} format"
- Validation failed: "Failed to meet {aspect-specific criteria}"

## Commands

### 1. Aspect (/a)
Controls aspect switching and initialization.

#### Usage
```
/a [aspect]                   # Switch to aspect
/a                           # Show current aspect
/a [aspect] -i               # Initialize new aspect
```

#### Options
- `-l`: List available aspects
- `-s`: Show aspect status
- `-f`: Force switch without validation
- `-i`: Initialize new aspect

#### Examples
```
# Development switch
/a swe                      # Quick switch
✅ Basic state preserved

# Aspect initialization
/a custom -i                # New aspect
✅ Structure created
✅ Templates copied

# List aspects
/a -l
Available:
- pm   (Product Management)
- swe  (Software Engineering)
```

### 2. Rehash (/r)
Reloads aspect configuration.

#### Usage
```
/r                          # Reload current aspect
/r [aspect]                 # Reload specific aspect
```

#### Options
- `-f`: Force full reload
- `-v`: Verbose output

#### Examples
```
# Reload current
/r
✅ Configuration reloaded
✅ Commands refreshed

# Reload specific
/r swe
✅ SWE aspect reloaded
```

### 3. Handoff (/h)
Initiates validated aspect transition.
See [Base Prompt - Transitions](./PROMPT.md#2-transitions) for details.

#### Usage
```
/h [aspect]                 # Validated transition
```

#### Options
- `-f`: Force without validation
- `-v`: Verbose validation

### 4. Status (/s)
Controls item status tracking and focus.

#### Usage
```
/s                   # Show current focus
/s ITEM              # Show status of ITEM and focus on it
/s -l [ITEM]         # List all items
/s -s ITEM [STATUS]  # Set status (uses ⚡ if STATUS omitted)
/ss ITEM [STATUS]    # Alias for /s -s
/sl [ITEM]           # Alias for /s -l
/sv                  # Alias for /s -v
```

#### Options
- `-l, --list`: List items (all or matching pattern)
- `-s, --set ITEM`: Set item status (⚡ if no status given, implies -m)
- `-v, --verify`: Verify requirements
- `-r, --recursive`: Include related items (never implied)
- `-m, --commit`: Auto-git add files and auto-git commit changes
- `-j, --json`: Output in JSON format

#### Status Values
- 🕔 Pending (0, "pending", "p")
- ⚡ In Progress (1, "start", "s")
- ✅ Complete/Done (2, "done", "d")
- ❌ Failed/Blocked (3, "block", "b")

#### Examples
```
/s                   # "Current focus: 3.1.9"
/ss 3.2.1           # Set 3.2.1 to ⚡
/sl 3.2             # List all items under 3.2
/sv                  # Verify current focus item
```

#### Behavior
- Maintains focus on last referenced item
- Updates relevant aspect files
- Generates conventional commits
- Enforces valid transitions
- Updates related items only with explicit -r

##### Hierarchical Status Rules
- Parent completion requires all children complete
- Child status changes don't auto-update parent
- Recursive operations (-r):
  - Must be explicitly requested
  - Changes propagate to all children when used
  - Example: `/ss 3.2.1 done -mr` (marks parent and children)
  - Example: `/ss 3.2.1 done -m` (marks only parent, fails if children incomplete)

### 5. Branch (/b)
Controls branch operations and context.

#### Usage
```
/b                  # Show current branch
/b -n NAME          # Create new branch
/b -l              # List branches
/b -s NAME         # Switch to branch
/b -d NAME         # Delete branch
/b -b NAME         # Set base branch for new branch
/bn NAME           # Alias for /b -n
/bs NAME           # Alias for /b -s
/bd NAME           # Alias for /b -d
```

#### Options
- `-n, --new=NAME`: Create new branch from current base
- `-l, --list`: List all branches
- `-c, --current`: Show current branch (default)
- `-s, --switch=NAME`: Switch to branch
- `-d, --delete=NAME`: Delete branch
- `-b, --base=NAME`: Set base branch for new branch
- `-j, --json`: Output in JSON format

#### Examples
```
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
```

#### Behavior
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

### 6. Done (/d)
Controls item completion workflow.

#### Usage
```
/d [ITEM]          # Complete specific item, defaults to current focus
/d -p              # Complete and push changes
/d -n              # Skip verification checks
```

#### Options
- `-p, --push`: Push changes after commit
- `-n, --no-verify`: Skip verification
- `-j, --json`: Output in JSON format

#### Examples
```
/d                # "Completing 3.1.9 in feature/meta-commands..."
                  # "✅ All requirements met"
                  # "Staged: PRD.md, CHECKLIST.md"
                  # "[feature/meta-commands abc123] docs: complete item 3.1.9 ✅"

/d 3.2.1          # "Completing 3.2.1 in feature/meta-commands..."
                  # "❌ Error: Children incomplete (3.2.1.3, 3.2.1.4)"
```

#### Behavior
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

### 7. Continue (/c)
Controls response to companion proposals.

#### Usage
```
/c                  # Accept first/default proposal (usually completion)
/c N                # Accept proposal number N
/c ?                # Request more specific proposals
```

#### Options
- `-j, --json`: Output proposal set in JSON format

#### Examples
```
Companion: "Would you like me to:
1. Mark this as complete
2. Further refine aspects
3. Something else?"

/c                 # Same as /c 1 (mark as complete)
/c 2               # Begin refinement process
/c ?               # "Please propose specific refinements"
```

#### Behavior
- Responds to companion's most recent proposal set
- No args implies accepting first/primary proposal
- Numbers select specific proposals (1-based)
- Question mark or "something else" option requests elaboration
- Invalid numbers show error and restate proposals
- Maintains conversation context for proposal chains
- Can trigger automatic actions (like completion)
- Error handling:
  - "Invalid option N, valid options are 1-K"
  - "No active proposals, try /x first"

### 8. Git (/g)
Controls git operations and workflow.

#### Usage
```
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
```

#### Options
- `-a, --add [FILES]`: Stage files (all if no FILES given)
- `-c, --commit [MSG]`: Commit changes (uses conventional format if no MSG)
- `-p, --push`: Push to current branch
- `-d, --diff`: Show changes
- `-l, --log`: Show commit history
- `-j, --json`: Output in JSON format
- `-v, --verify`: Verify commit message format

#### Examples
```
/g                 # "On branch feature/meta-commands"
                   # "Changes not staged for commit:"
                   # "  modified: .cursor/docs/meta_commands/PRD.md"

/ga PRD.md        # "Staged .cursor/docs/meta_commands/PRD.md"

/gc               # "Commit message (conventional format):"
                   # "docs(meta-commands): update git command section ✨"
                   # "[feature/meta-commands abc123] 1 file changed"

/gp               # "Pushing to origin/feature/meta-commands..."
                   # "Done: abc123..def456"
```

#### Behavior
- Integrates with git workflow in current branch
- Maintains conventional commit format
- Coordinates with status tracking system
- Auto-formats commit messages when no message given
- Verifies staged files match current focus
- Reports all operations with clear status
- Error handling:
  - "Nothing to commit" when no changes staged
  - "Invalid commit message format" with format guide
  - "Push failed" with fetch/merge suggestion
- No side effects beyond git operations
- Sets basis for subsequent commands

## State Management

### Focus Stack
- Preserved during aspect switches when possible
- Cleared on forced switches (`-f`)
- Validated during handoffs

### Active Operations
- Blocked during aspect changes
- Must be completed or forced
- State preserved when possible

### Configuration
- Loaded on aspect switch
- Reloaded on rehash
- Validated during operations

### Error Recovery
1. **Invalid Aspect**
   - Check available aspects
   - Verify aspect name
   - Try again

2. **Active Operation**
   - Complete current operation
   - Use force flag if needed
   - Verify state after switch

3. **Failed Validation**
   - Address validation errors
   - Re-verify with `/x -v`
   - Attempt handoff again

4. **Configuration Issues**
   - Check configuration files
   - Force reload if needed
   - Restore from backup

## Command Workflows

### Development Flow
```
/a swe                      # Quick switch for development
/r                         # Refresh if needed
... development work ...
/a pm                      # Switch back to PM
```

### Formal Handoff Flow
```
/x -v                      # Verify current state
/h swe                    # Initiate handoff
... validation ...
✅ Handoff complete
```

### Recovery Flow
```
/x -v                      # Check issues
/rr                       # Fix problems
/h swe                    # Retry handoff
```

## Command Relationships
- Examine provides analysis foundation
- Refine builds on examination results
- Commands maintain consistent patterns while adapting to aspect focus

## Success Criteria
1. Clear, actionable feedback
2. Measurable improvements
3. Consistent behavior patterns
4. Effective aspect adaptation
