# Contributing to Chronicler

Thank you for your interest in contributing to Chronicler! This document provides guidelines and instructions for contributing.

## Development Process

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/ans.git
   cd ans
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Create a Branch**
   - Use descriptive branch names:
     - `feature/*` for new features
     - `fix/*` for bug fixes
     - `docs/*` for documentation
     - `refactor/*` for code refactoring

4. **Write Tests First**
   - Follow Test-Driven Development (TDD)
   - Write tests in the appropriate directory:
     - `tests/00-unit/` for unit tests
     - `tests/01-mock/` for mock integration tests
     - `tests/02-live/` for live integration tests

5. **Implement Changes**
   - Write clear, documented code
   - Follow existing code style
   - Keep changes focused and minimal

6. **Run Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test categories
   pytest tests/00-unit
   pytest tests/01-mock
   pytest tests/02-live
   ```

7. **Submit Pull Request**
   - Push changes to your fork
   - Create PR through GitHub interface
   - Provide clear description of changes
   - Reference any related issues

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for classes and functions
- Keep functions focused and small
- Use descriptive variable names

## Commit Messages

Follow conventional commits format:
```
type(scope): description

[optional body]
[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(telegram): add support for voice messages

- Implement voice message handling
- Add tests for voice messages
- Update documentation
```

## Testing

### Unit Tests
- Test individual components in isolation
- Mock all external dependencies
- Focus on edge cases and error handling

### Mock Tests
- Test component integration
- Mock external services
- Verify component interactions

### Live Tests
- Test with real external services
- Require proper environment setup
- May be slow and need special configuration

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new code
- Update CHANGELOG.md for significant changes
- Include example usage where appropriate

## Test Coverage

### Requirements
1. All new code must maintain minimum 80% test coverage
2. Both statement and branch coverage are measured
3. Coverage reports are generated for each test run

### Running Tests with Coverage
```bash
# Run tests with coverage reporting
pytest

# View detailed HTML coverage report
open coverage_html/index.html
```

### Coverage Configuration
1. Coverage settings are defined in:
   - .coveragerc: Tool configuration
   - pytest.ini: Test runner settings

2. Excluded patterns:
   - Test files
   - __init__.py files
   - Specific exclusions via "# pragma: no cover"

3. Coverage reports show:
   - Statement coverage percentage
   - Branch coverage percentage
   - Missing lines
   - Excluded lines

### Maintaining Coverage
1. Review coverage reports before submitting PRs
2. Add tests for any missing coverage
3. Document any intentionally excluded code
4. Update minimum coverage requirements as needed

## Questions?

Feel free to:
- Open an issue for questions
- Join our discussion forum
- Contact the maintainers

Thank you for contributing! 