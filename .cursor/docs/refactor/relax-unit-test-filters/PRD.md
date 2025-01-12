# Product Requirements: Relax Unit Test Filters

## Overview
Modify pytest configuration to allow all tests under `tests/00-unit` to run while maintaining strict separation from mock and live tests. Simultaneously raise the coverage requirement to 80% to ensure high code quality.

## Current State
1. Pytest configuration is split across multiple files:
   - `pytest.ini`: Main test configuration
   - `.coveragerc`: Coverage tool configuration
   - `conftest.py`: Test fixtures and setup
2. Current coverage threshold is set to 30%
3. Test directories are structured as:
   - `tests/00-unit/`: Unit tests
   - `tests/01-mock/`: Mock integration tests
   - `tests/02-live/`: Live integration tests

## Requirements

### 1. Test Filter Modifications
1.1. Remove any restrictive filters in pytest configuration that prevent unit tests from running
1.2. Maintain strict separation between:
    - Unit tests (00-unit)
    - Mock tests (01-mock)
    - Live tests (02-live)
1.3. Ensure all tests under `tests/00-unit` can run by default

### 2. Coverage Requirements
2.1. Raise minimum coverage threshold from 30% to 80%
2.2. Update coverage configuration in:
    - `pytest.ini`
    - `.github/workflows/test-coverage.yml`
2.3. Maintain existing coverage exclusions:
    - Test files
    - `__init__.py` files
    - Pragma-excluded lines

### 3. Test Discovery
3.1. Ensure pytest can discover all test files under `tests/00-unit`
3.2. Maintain existing test file patterns:
    - `test_*.py`
    - `Test*` classes
    - `test_*` functions

### 4. CI/CD Integration
4.1. Update GitHub Actions workflow to enforce new coverage threshold
4.2. Maintain existing coverage reporting:
    - Terminal output
    - HTML reports
    - Coverage artifacts

## Success Criteria
1. All tests under `tests/00-unit` run successfully
2. Coverage threshold enforced at 80%
3. Mock and live tests remain isolated
4. CI/CD pipeline passes with new requirements 