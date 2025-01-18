# Product Management Commands

## Overview
Product management interpretation of base commands, focusing on requirements, specifications, and product articulation.

## Focus Stack
Commands maintain a focus stack for requirement navigation:
- Examining a requirement pushes it onto the focus stack
- Pop operations return to previous requirement focus
- Stack preserves context during requirement breakdown

## Commands

### 1. Examine (/x)
Analyzes requirements and specifications from a product perspective.

#### Usage
```
/x [item]                    # Examine requirement (pushes to focus stack)
/x -x                       # Pop focus stack
/xx                        # Alias for /x -x
```

#### Options
- `-d`: Detailed analysis
- `-s`: Summary only
- `-v`: Validation focus
- `-x`: Pop focus stack

#### Examples
```
/x 3.2.1.8                  # Examine and focus on feature
✅ Structure: Clear user story and acceptance criteria
❌ Completeness: Missing edge case handling
✅ Consistency: Follows product terminology
❌ Context: Unclear user journey placement

/x 3.2.1.9                  # Focus moves to related feature
✅ Structure: Well-defined requirements
✅ Completeness: All scenarios covered
✅ Consistency: Matches user expectations
✅ Context: Clear workflow integration

/xx                         # Return focus to 3.2.1.8
```

### Refine Command (/rr)
Usage:
  /rr                 # Refine current focus item
  /rr ITEM            # Refine specific item

Options:
  -j, --json          Output in JSON format

Examples:
  /rr                # "Refining 3.2.1.8 requirements:"
                    # "1. User Story:"
                    # "   As a PM, I need systematic validation"
                    # "   So that requirements achieve clarity"
                    # 
                    # "2. Acceptance Criteria:"
                    # "   - Must verify requirement completeness"
                    # "   - Must validate structural integrity"
                    # "   - Must ensure pattern consistency"
                    # 
                    # "3. Implementation Context:"
                    # "   - Core validation engine"
                    # "   - Pattern verification system"
                    # "   - Integration framework"

  /rr 2.1.3         # "Requirements complete and ready for implementation"
                    # "Proceeding to engineering handoff"

Behavior:
  - Breaks down requirements:
    * Decomposes features into components
    * Establishes clear value propositions
    * Maps dependencies
  - Develops specifications:
    * Defines measurable criteria
    * Establishes verification methods
    * Ensures completeness
  - Maintains focus on user/business value
  - No side effects beyond documentation updates

### 3. Handoff (/h)
Manages transitions between PM and SWE aspects.

#### Usage
```
/h swe                       # Handoff to SWE aspect
```

#### Validation
Before SWE handoff, verifies:
1. Requirements completeness
   ```
   ✅ User stories defined
   ✅ Acceptance criteria specified
   ✅ Edge cases documented
   ```

2. Technical readiness
   ```
   ✅ Implementation constraints defined
   ✅ Performance requirements specified
   ✅ Integration points documented
   ```

3. Documentation state
   ```
   ✅ All sections complete
   ✅ Cross-references resolved
   ✅ Terminology consistent
   ```

#### Examples
```
# Successful handoff
/h swe
Verifying requirements...
✅ Requirements complete
✅ Technical constraints defined
✅ Documentation ready
Initiating SWE handoff...

# Failed handoff
/h swe
Verifying requirements...
❌ Requirements incomplete:
   - Missing performance criteria
   - Undefined error scenarios
Handoff blocked
```

#### Recovery
If handoff fails:
1. Use `/x -v` to identify gaps
2. Use `/rr` to address issues
3. Retry handoff with `/h`

## Typical Workflows

### New Feature Development
1. `/x` to assess current state
2. `/rr` to break down requirements
3. `/x` to verify completeness
4. Repeat until implementation-ready

### Requirement Validation
1. `/x` to analyze current state
2. `/rr` to address gaps
3. `/x` to confirm improvements

### Dependency Management
1. `/x` parent to understand context
2. `/rr` parent to define relationships
3. `/x` children to verify alignment
4. `/rr` children to maintain consistency
