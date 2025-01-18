# Software Engineering Prompt

## Document Relationships
This document defines behaviors and success criteria for software engineering commands. See:
- [SWE Commands](./COMMANDS.md) - Command implementations
- [Base Commands](../base/COMMANDS.md) - Base command definitions
- [Base Prompt](../base/PROMPT.md) - Core capabilities

## Overview
Software engineering interpretation of base prompt capabilities, focused on systematic code improvement through:
- Code unit identification and analysis
- Implementation pattern recognition
- Quality metrics and validation
- Targeted improvement suggestions

## Base Extensions

### 1. Command Behavior
Extends base commands with code-focused interpretations:

#### Examine (/x)
- Analyzes code unit structure and patterns
- Validates against quality metrics
- Identifies improvement opportunities
- Maintains focus stack for navigation

#### Refine (/rr)
- Suggests targeted improvements
- Applies design patterns
- Optimizes performance
- Verifies implementation quality

#### Status (/s)
- Tracks code unit state
- Reports quality metrics
- Shows test coverage
- Identifies dependencies

### 2. Analysis Categories

#### Structure
- Function and class organization
- Interface contracts
- Design patterns
- Code relationships

#### Completeness
- Core functionality
- Error handling
- Documentation
- Test coverage

#### Consistency
- Naming conventions
- Code style
- Pattern usage
- Error handling

#### Context
- Dependencies
- Side effects
- Performance
- Memory usage

### 3. Success Criteria

#### Code Structure
- Functions have single responsibility
- Classes encapsulate related behavior
- Clear separation of concerns
- Consistent abstraction levels

#### Implementation Quality
- Cyclomatic complexity ≤ 3
- Function length ≤ 20 lines
- Clear naming and formatting
- Appropriate patterns used

#### Documentation
- Purpose and behavior
- Parameters and returns
- Time/space complexity
- Side effects noted

#### Error Handling
- Input validation
- Edge case coverage
- Clear error messages
- Recovery paths

#### Testing
- Core logic verified
- Edge cases covered
- Performance validated
- Side effects tested

### 4. Error Handling

#### Not Found
```
❌ Error: Unit 'fibonacci' not found in src.math.fib
Details: Check spelling and fully qualified path
```

#### Invalid Format
```
❌ Error: Invalid reference format
Details: Use module.class.method or module.function
```

#### Validation Failed
```
❌ Error: Failed complexity check (4 > 3)
Details: Consider breaking into smaller functions
```

## Example Verification
Example success criteria verification:
```
/x -v src.math.fib.fibonacci

Structure:
✅ Single responsibility
✅ Clear abstraction
✅ Appropriate patterns

Quality:
✅ Complexity: 2
✅ Length: 3 lines
✅ Clear naming
✅ Error handling

Documentation:
✅ Purpose clear
✅ Params documented
✅ Returns specified
✅ Complexity noted

Testing:
✅ Core logic
✅ Edge cases
✅ Performance
✅ Side effects
``` 