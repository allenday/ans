# Scribe Commands

## User Commands
- `/start` - Initialize scribe and show welcome message
- `/help` - Show available commands and usage
- `/status` - Show your current GitHub config and monitored groups
- `/setup` - Configure your GitHub repository
  1. Request GitHub token
  2. Request repository name
- `/monitor` - Start monitoring current group to your GitHub repo
  - Usage: `/monitor [topic_name]`
  - Only works in groups where scribe is present
  - Requires GitHub to be configured first
- `/unmonitor` - Stop monitoring current group to your repo
- `/filters` - Configure message filters for your monitoring
  - Usage: `/filters media_only=true min_length=10`
- `/sync` - Force sync to your GitHub repository
- `/list` - Show your monitored groups and their configs

## Admin Commands (Scribe Owner)
- `/debug` - Show system debug information
- `/reset` - Reset user session state if stuck 

# Planned GitOps Features
These features will be implemented as GitHub Actions workflows that users can enable in their repos:

## Automated Processing
- Sessionize conversations by time gaps or topic shifts
- Generate summaries of conversations using LLMs
- Extract key topics and create indexes
- Convert chat logs to different formats (MD, PDF, etc)

## Trigger Methods
- On schedule (daily/weekly summaries)
- On PR (process new logs)
- Manual trigger (process specific timeframes)
- Via labels (mark conversations for specific processing)

## Example Workflows
- Daily summary of all conversations
- Topic-based clustering of messages
- Extract action items and decisions
- Generate meeting minutes from chat logs
- Create searchable knowledge base from discussions

Note: These features will be implemented in a future sprint as separate GitHub Actions that work with the chat logs stored by the scribe. 