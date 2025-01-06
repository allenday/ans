# Development Conventions

## Code Style

1. **Python Standards**
   - Follow PEP 8
   - Use type hints
   - Write docstrings (Google style)
   - Maximum line length: 100 characters

2. **Naming**
   - Classes: `PascalCase`
   - Functions/methods: `snake_case`
   - Variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`

3. **Documentation**
   - Module docstrings explain purpose
   - Class docstrings describe behavior
   - Method docstrings include:
     - Args
     - Returns
     - Raises
     - Examples (if complex)

## Project Structure

1. **Directory Organization**
   ```
   src/chronicler/
   ├── pipeline/      # Core components
   ├── processors/    # Message processors
   ├── storage/       # Storage system
   └── transports/    # I/O handlers
   ```

2. **Test Organization**
   ```
   tests/
   ├── 00-unit/      # Unit tests
   ├── 01-mock/      # Mock integration tests
   └── 02-live/      # Live integration tests
   ```

## Git Practices

1. **Branches**
   - `main`: Protected, requires PR
   - `feature/*`: New features
   - `fix/*`: Bug fixes
   - `docs/*`: Documentation
   - `refactor/*`: Code cleanup

2. **Commits**
   - Use conventional commits
   - Include scope
   - Write clear messages

3. **Pull Requests**
   - Reference issues
   - Include tests
   - Update docs
   - Clean commits 