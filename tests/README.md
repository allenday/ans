# Test Suite Documentation

## Overview
This document describes the test suite structure, requirements, and execution guidelines for the Chronicler project.

## Test Structure

### Unit Tests (`tests/00-unit/`)
- Located in: `tests/00-unit/`
- Purpose: Test individual components in isolation
- Dependencies: Mocked
- Execution: Fast, no external dependencies
- Coverage: Required for all new code

### Integration Tests (`tests/01-live/`)
- Located in: `tests/01-live/`
- Purpose: Test component interactions and real-world scenarios
- Dependencies: Real system components
- Execution: May be slower, requires external setup
- Coverage: Required for critical paths

### Mock Utilities (`tests/mocks/`)
- Located in: `tests/mocks/`
- Purpose: Shared mock objects and utilities
- Usage: Import in unit tests
- Maintenance: Keep in sync with real components

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock all external dependencies
- Fast execution (< 100ms per test)
- No filesystem or network access
- Examples: Frame validation, processor logic

### Integration Tests
- Test component interactions
- Use real dependencies where practical
- May be slower (timeout limits apply)
- May require external resources
- Examples: Storage operations, network communication

## Requirements

### Coverage Requirements
- Minimum coverage: 80%
- Branch coverage enabled
- Coverage measured across all test types
- Pre-push hook enforces coverage

### Performance Requirements
- Unit tests: < 100ms per test
- Integration tests: < 1s per test
- Full suite: < 5 minutes
- Memory growth: < 10MB per test

### Documentation Requirements
- All test modules must have docstrings
- Test functions must have clear purpose
- Complex test setups must be documented
- Fixtures must be documented

## Setup Requirements

### Environment Variables
Required for integration tests:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=your_phone_number
```

### External Dependencies
1. Git repository for storage tests
2. Telegram bot for transport tests
3. Sufficient disk space (>100MB)
4. Network access for API tests

## Test Execution

### Running All Tests
```bash
pytest tests/00-unit tests/01-live -v
```

### Running Unit Tests Only
```bash
pytest tests/00-unit -v
```

### Running Integration Tests Only
```bash
pytest tests/01-live -v
```

### Running with Coverage
```bash
pytest --cov=chronicler --cov-report=html
```

## Test Development Guidelines

### Writing New Tests
1. Place in appropriate directory
2. Follow naming conventions
3. Include docstrings
4. Mock external dependencies
5. Set appropriate markers

### Test Structure
```python
"""Module docstring explaining test purpose."""

import pytest
from unittest.mock import Mock

@pytest.mark.unit  # or @pytest.mark.integration
def test_specific_functionality():
    """Test docstring explaining what is being tested."""
    # Arrange
    test_data = ...
    
    # Act
    result = ...
    
    # Assert
    assert result == expected

```

### Fixtures
- Place common fixtures in conftest.py
- Document fixture purpose and usage
- Clean up resources in fixture teardown
- Consider fixture scope carefully

### Error Testing
- Test both success and failure paths
- Verify error messages
- Test boundary conditions
- Test resource cleanup

## Continuous Integration

### Pre-push Hook
- Runs all tests
- Verifies coverage requirements
- Blocks push on failure
- Reports detailed results

### Coverage Reports
- HTML report in coverage_html/
- XML report in coverage.xml
- Console summary with missing lines
- Branch coverage included

## Troubleshooting

### Common Issues
1. Missing environment variables
2. Network connectivity problems
3. Resource cleanup failures
4. Timing-sensitive tests

### Solutions
1. Check environment setup
2. Use pytest -v for verbose output
3. Check test logs
4. Review resource cleanup

## Maintenance

### Regular Tasks
1. Update mock objects
2. Review coverage reports
3. Optimize slow tests
4. Update documentation

### Best Practices
1. Keep tests focused
2. Clean up resources
3. Avoid test interdependence
4. Maintain documentation 