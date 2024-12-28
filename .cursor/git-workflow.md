# Git Workflow

## Branch Naming

All feature branches should follow the pattern:
- `feature/descriptive-name` for new features
- `fix/descriptive-name` for bug fixes
- `docs/descriptive-name` for documentation
- `chore/descriptive-name` for maintenance tasks

## Workflow

1. Always start by creating a properly named branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit with conventional commits:
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

3. Push to GitHub and create a PR:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Never commit directly to main 