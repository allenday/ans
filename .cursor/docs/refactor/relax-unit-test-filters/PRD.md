# Product Requirements: Relax Unit Test Filters

## Overview
Modify pytest configuration to allow all tests under `tests/00-unit` to run while maintaining strict separation from mock and live tests. Simultaneously raise the coverage requirement to 80% to ensure high code quality.

## Current State
1. Pytest configuration is split across multiple files:
   1.1. `pytest.ini`: Main test configuration
   1.2. `.coveragerc`: Coverage tool configuration
   1.3. `conftest.py`: Test fixtures and setup

2. Current coverage threshold is set to 30%

3. Test directories are structured as:
   3.1. `tests/00-unit/`: Unit tests
   3.2. `tests/01-mock/`: Mock integration tests
   3.3. `tests/02-live/`: Live integration tests

4. Current coverage status:
   4.1. Overall: 38%
   4.2. Storage components:
        4.2.1. Serializer: 100%
        4.2.2. Git storage: 77%
        4.2.3. Coordinator: 29%
        4.2.4. Filesystem: 27%
   4.3. Pipeline components:
        4.3.1. Frames: 0%
        4.3.2. Pipecat runner: 0%
        4.3.3. Storage processor: 15%
   4.4. Transport components:
        4.4.1. Telegram transport: 13%
        4.4.2. Events: 58%

## Requirements

1. Test Filter Modifications
   1.1. Remove any restrictive filters in pytest configuration that prevent unit tests from running
   1.2. Maintain strict separation between:
        1.2.1. Unit tests (00-unit)
        1.2.2. Mock tests (01-mock)
        1.2.3. Live tests (02-live)
   1.3. Ensure all tests under `tests/00-unit` can run by default

2. Coverage Requirements
   2.1. Raise minimum coverage threshold from 30% to 80%
   2.2. Update coverage configuration in:
        2.2.1. `pytest.ini`
        2.2.2. `.github/workflows/test-coverage.yml`
   2.3. Maintain existing coverage exclusions:
        2.3.1. Test files
        2.3.2. `__init__.py` files
        2.3.3. Pragma-excluded lines
   2.4. Improve coverage in key components:
        2.4.1. Storage components:
               2.4.1.1. Git storage: ✅ Added tests for file operations, metadata management, error handling, and git operations
               2.4.1.2. Coordinator: Add tests for message handling and attachment processing
               2.4.1.3. Filesystem: Add tests for file operations and error handling
        2.4.2. Pipeline components:
               2.4.2.1. Frames: Add tests for frame processing and validation
               2.4.2.2. Pipecat runner: Add tests for pipeline execution and error handling
               2.4.2.3. Storage processor: Add tests for message processing and storage operations
        2.4.3. Transport components:
               2.4.3.1. Telegram transport: Add tests for message handling and API interactions
               2.4.3.2. Events: Add tests for event processing and error handling

3. Test Discovery
   3.1. Ensure pytest can discover all test files under `tests/00-unit`
   3.2. Maintain existing test file patterns:
        3.2.1. `test_*.py`
        3.2.2. `Test*` classes
        3.2.3. `test_*` functions

4. CI/CD Integration
   4.1. Update GitHub Actions workflow to enforce new coverage threshold
   4.2. Maintain existing coverage reporting:
        4.2.1. Terminal output
        4.2.2. HTML reports
        4.2.3. Coverage artifacts

## Success Criteria
1. All tests under `tests/00-unit` run successfully
2. Coverage threshold enforced at 80%
3. Mock and live tests remain isolated
4. CI/CD pipeline passes with new requirements
5. All key components have adequate test coverage:
   5.1. Storage components: ≥80% each
   5.2. Pipeline components: ≥80% each
   5.3. Transport components: ≥80% each 