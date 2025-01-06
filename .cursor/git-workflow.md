# Git Workflow

## Branch Strategy

1. **Main Branch**
   - Protected branch
   - Requires pull request
   - Must pass CI checks
   - Must have review approval

2. **Feature Branches**
   - Branch from main
   - Format: `feature/description`
   - Example: `feature/add-voice-messages`

3. **Fix Branches**
   - Branch from main
   - Format: `fix/description`
   - Example: `fix/handle-null-content`

4. **Documentation Branches**
   - Branch from main
   - Format: `docs/description`
   - Example: `docs/update-readme`

5. **Refactor Branches**
   - Branch from main
   - Format: `refactor/description`
   - Example: `refactor/cleanup-pipeline`

## Commit Messages

Follow conventional commits:
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
feat(telegram): add voice message support

- Implement voice message handling in TelegramTransport
- Add voice message tests
- Update documentation
```

## Pull Request Process

1. **Create PR**
   - Clear title using conventional commits
   - Detailed description
   - Reference related issues

2. **Review Process**
   - CI checks must pass
   - Code review required
   - Documentation updated
   - Tests included

3. **Merge Strategy**
   - Squash and merge
   - Clean commit history
   - Delete branch after merge 