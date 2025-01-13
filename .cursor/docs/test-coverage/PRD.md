# Product Requirements: Test Coverage Improvements

## Overview
Improve test coverage across the codebase to ensure reliability and maintainability. The goal is to achieve 80% coverage for critical components while ensuring proper test isolation and meaningful assertions.

## Current State
- Multiple test directories: `tests/00-unit/`, `tests/01-mock/`, and `tests/02-live/`
- Overall coverage at 31%
- Critical modules with low coverage:
  - `git.py` (8% coverage, 316 lines)
  - `storage_processor.py` (15% coverage, 140 lines)
  - `serializer.py` (22% coverage, 71 lines)
  - `filesystem.py` (27% coverage, 52 lines)
  - `telegram.py` (26% coverage, 60 lines)

## Completed Work
1. Storage Coordinator Improvements
   - Added id field to Message class
   - Fixed attachment handling in save_message
   - Added comprehensive tests for all methods
   - Achieved 100% coverage for coordinator module

2. Test Configuration Updates
   - Relaxed filters to allow all tests in `tests/00-unit`
   - Raised coverage threshold to 80%
   - Updated CI/CD workflow for new coverage requirements

## Next Steps
1. Git Storage Testing
   - Create comprehensive test suite for GitStorageAdapter
   - Focus on core operations: init, topic creation, message saving
   - Test GitHub integration and sync functionality
   - Target 80% coverage for this critical module

2. Additional Module Coverage
   - Improve storage processor tests
   - Add serializer tests
   - Enhance filesystem storage tests
   - Test Telegram attachment handling

## Success Criteria
1. ✅ Storage coordinator tests complete and passing
2. ✅ Test configuration updated for proper discovery
3. ✅ Coverage threshold raised to 80%
4. 🕔 Git storage adapter tests with 80% coverage
5. 🕔 Overall improvement in critical module coverage 