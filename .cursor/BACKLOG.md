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
  
## Test Coverage Metrics  
  
### 1. Unit Test Coverage  
1.1. Configuration:  
    1.1.1. Tool: pytest-cov  
    1.1.2. Minimum coverage: 80%  
    1.1.3. Branch coverage: enabled  
    1.1.4. Configuration files:  
       - .coveragerc: Coverage tool configuration  
       - pytest.ini: Test runner configuration  
  
1.2. Metrics Tracked:  
    1.2.1. Statement coverage  
    1.2.2. Branch coverage  
    1.2.3. Missing lines  
    1.2.4. Excluded patterns  
  
1.3. Reports:  
    1.3.1. Terminal output (--cov-report=term-missing)  
    1.3.2. HTML report (--cov-report=html)  
    1.3.3. Location: coverage_html/  
  
1.4. Usage:  
    1.4.1. Run tests with coverage:  
       ```bash  
       pytest  
       ```  
    1.4.2. View HTML report:  
       ```bash  
       open coverage_html/index.html  
       ```  
  
1.5. Maintenance:  
    1.5.1. Update minimum coverage in pytest.ini  
    1.5.2. Adjust exclusions in .coveragerc  
    1.5.3. Review coverage reports in CI/CD
