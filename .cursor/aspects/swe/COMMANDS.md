# Software Engineering Commands

## Document Relationships
This document implements software engineering commands. See:
- [SWE Prompt](./PROMPT.md) - Behaviors and success criteria
- [Base Commands](../base/COMMANDS.md) - Base command definitions
- [Base Prompt](../base/PROMPT.md) - Core capabilities

## Overview
Engineering interpretation of base commands for code-level analysis and implementation. Each command operates on specific code units: functions, classes, modules, or interfaces.

These commands enable systematic code improvement through:
- Identifying and focusing on specific code units
- Analyzing implementation details and patterns
- Suggesting targeted improvements
- Measuring quality improvements

## Code Units

### Identification
- Function: `src.math.fib.fibonacci`
- Class method: `src.math.fib.Fibonacci.iterative`
- Module: `src.math.fib`

### Resolution
- Relative to current file: `..fibonacci` (from another function in fib.py)
- From project root: `src.math.fib.fibonacci`
- Fully qualified: `org.example.src.math.fib.fibonacci`

### Context
- Focus stack for code navigation:
```
/x src.math.fib.fibonacci              # Push recursive version
/x src.math.fib.Fibonacci.iterative    # Push iterative
/xx                                    # Pop back to recursive
/s src.math.fib                       # Set focus to module
```
- Workspace root is the parent directory of .git
- Cross-file references use language-specific import mechanisms
- Resolution uses IDE's built-in caching and indexing

### Scope
- Single unit: `src.math.fib.fibonacci`
- Class method: `src.math.fib.Fibonacci.iterative`
- Multiple units: Not supported (use multiple commands)

## Commands

### 1. Examine (/x)
Analyzes implementation details of a specific code unit.

#### Usage
```
/x                                    # Examine current focus
/x src.math.fib.fibonacci            # Push to focus stack
/x -x                                # Pop focus stack
/xx                                  # Pop focus stack (alias)
```

#### Options
- `-d`: Show detailed analysis including:
```
/x -d src.math.fib.fibonacci
Cyclomatic complexity: 2
Dependencies: None
Memory: O(n) stack frames
Call pattern: Recursive, exponential calls
```
- `-s`: Show only structure:
```
/x -s src.math.fib.fibonacci
def fibonacci(n): int
```
- `-v`: Validate implementation:
```
/x -v src.math.fib.fibonacci
❌ Type safety: Missing type hints
❌ Error handling: No input validation
✅ Memory safety: No explicit allocation
❌ Test coverage: No tests found
```

### 2. Refine (/rr)
Improves implementation of a specific code unit through targeted changes.

#### Usage
```
/rr                                  # Refine current focus
/rr src.math.fib.fibonacci          # Push to focus stack and refine
```

#### Options
- `-p`: Optimize performance:
```
/rr -p src.math.fib.fibonacci
Analyzing performance...
- Time complexity: O(2^n)
- Space complexity: O(n)
Suggestions:
- Consider memoization
- Switch to iterative approach
```
- `-d`: Apply design patterns:
```
/rr -d src.math.fib.fibonacci
Suggested patterns:
- Strategy (for multiple implementations)
- Memoization (for performance)
```
- `-v`: Verify changes:
```
/rr -v src.math.fib.fibonacci
Verifying implementation...
❌ Type hints needed
❌ Input validation missing
❌ Performance warning needed
```

### 3. Handoff (/h)
Manages transitions between SWE and PM aspects.

#### Usage
```
/h pm                       # Handoff to PM aspect
```

#### Validation
Before PM handoff, verifies:
1. Implementation quality
   ```
   ✅ All quality metrics pass
   ✅ Performance requirements met
   ✅ Error handling complete
   ```

2. Test coverage
   ```
   ✅ Core logic tested
   ✅ Edge cases covered
   ✅ Performance validated
   ```

3. Documentation state
   ```
   ✅ Implementation details noted
   ✅ Known limitations documented
   ✅ Performance characteristics specified
   ```

#### Examples
```
# Successful handoff
/h pm
Verifying implementation...
✅ Quality metrics pass
✅ Tests complete
✅ Documentation ready
Initiating PM handoff...

# Failed handoff
/h pm
Verifying implementation...
❌ Implementation incomplete:
   - Failed quality metrics
   - Missing test coverage
Handoff blocked
```

#### Recovery
If handoff fails:
1. Use `/x -v` to identify issues
2. Use `/rr` to fix problems
3. Retry handoff with `/h`

## Error Handling

### Not Found
```
/x src.math.fib.missing
❌ Error: Unit 'missing' not found in src.math.fib
```

### Invalid Format
```
/x src.math.fib..
❌ Error: Invalid reference format
```

### Stack Underflow
```
/xx
❌ Error: No previous focus (stack empty)
```

### Ambiguous Reference
```
/x src.math.fib
❌ Error: Multiple units found:
- src.math.fib.fibonacci
- src.math.fib.Fibonacci.iterative
```

## Command Workflow
Example improvement workflow:
```
# 1. Initial Analysis
/x src.math.fib.fibonacci
❌ Structure: Missing type hints
❌ Quality: No input validation
❌ Docs: No complexity note
❌ Tests: No coverage

# 2. Detailed Examination
/x -d src.math.fib.fibonacci
- Cyclomatic complexity: 2 (meets criteria ≤ 3)
- Function length: 3 lines (meets criteria ≤ 20)
- Time complexity: O(2^n) (needs documentation)
- Space complexity: O(n) (needs documentation)

# 3. Systematic Improvement
/rr src.math.fib.fibonacci
Adding type hints:
def fibonacci(n: int) -> int:
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)

# 4. Progress Check
/rr -v
✅ Structure: Type hints added
❌ Quality: Still needs validation
❌ Docs: Still needs complexity note
❌ Tests: Still needs coverage

# 5. Final Verification
/rr -v src.math.fib.fibonacci
✅ All criteria met
```
