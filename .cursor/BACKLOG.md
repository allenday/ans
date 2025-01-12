# Development Backlog  
  
> This document tracks planned development work. For completed work, see CHANGELOG.md.  
> For architectural details, see ARCHITECTURE.md.  
> For contribution guidelines, see CONTRIBUTING.md.  
  
## Current Sprint  
  
### In Progress  
1. None  
  
### Next Up  
1. Implement asynchronous git operations  
   1. Requirements:  
      1. Commit messages on branch-specific schedule  
      2. Decouple message receipt from git pushes  
      3. Provide operation status  
   2. Components:  
      1. GitOperationQueue with branch awareness  
      2. StatusReporter  
   3. Constraints:  
      1. Memory-efficient queuing  
      2. Performance optimization  
      3. Basic retry mechanism for failures  
  
## Future Work  
  
### Features  
1. Add multi-tenant support for group chats  
   1. Requirements:  
      1. Bot configuration via slash commands  
      2. Per-group chat configuration  
      3. Branch-specific git repository support  
      4. User authorization management  
  
### Technical Debt  
1. Clean up old implementation files  
2. Add performance metrics  
3. Add monitoring hooks  
4. Enhance operational logging  
   1. Requirements:  
      1. Add structured logging with consistent metadata  
      2. Implement correlation IDs for message tracking  
      3. Add performance metrics in logs  
      4. Standardize log levels across components  
      5. Add component tracing  
  
### Documentation  
> See DOCUMENTATION.md for full documentation plan and status  
  
1. Update technical documentation to reflect branch-based workflow  
2. Add deployment guide with branch configuration  
3. Add troubleshooting guide  
4. Add message format specification  
5. Add storage format specification  
6. Add configuration guide  
  
## Known Issues  
1. Voice messages saved with incorrect extension  
2. Large files cause memory pressure
