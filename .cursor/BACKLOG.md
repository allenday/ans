# Development Backlog  
  
> This document tracks planned development work. For completed work, see CHANGELOG.md.  
> For architectural details, see ARCHITECTURE.md.  
> For contribution guidelines, see CONTRIBUTING.md.  
  
## Current Sprint  
  
### In Progress  
- None  
  
### Next Up  
1. Implement asynchronous git operations  
   - Requirements:  
     - Commit messages on branch-specific schedule  
     - Decouple message receipt from git pushes  
     - Provide operation status  
   - Components:  
     - GitOperationQueue with branch awareness  
     - StatusReporter  
   - Constraints:  
     - Memory-efficient queuing  
     - Performance optimization  
     - Basic retry mechanism for failures  
  
## Future Work  
  
### Features  
- [ ] Add multi-tenant support for group chats  
  - Requirements:  
    - Bot configuration via slash commands  
    - Per-group chat configuration  
    - Branch-specific git repository support  
    - User authorization management  
  
### Technical Debt  
- [ ] Clean up old implementation files  
- [ ] Add performance metrics  
- [ ] Add monitoring hooks  
- [ ] Enhance operational logging  
  - Requirements:  
    - Add structured logging with consistent metadata  
    - Implement correlation IDs for message tracking  
    - Add performance metrics in logs  
    - Standardize log levels across components  
    - Add component tracing  
  
### Documentation  
> See DOCUMENTATION.md for full documentation plan and status  
  
- [ ] Update technical documentation to reflect branch-based workflow  
- [ ] Add deployment guide with branch configuration  
- [ ] Add troubleshooting guide  
- [ ] Add message format specification  
- [ ] Add storage format specification  
- [ ] Add configuration guide  
  
## Known Issues  
- [ ] Voice messages saved with incorrect extension  
- [ ] Large files cause memory pressure
