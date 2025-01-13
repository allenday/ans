# Implementation Checklist: Relax Unit Test Filters

1. Configuration Updates
   1.1. Update pytest.ini
        1.1.1. ✅ Remove restrictive testpaths setting
        1.1.2. ✅ Update coverage threshold to 80%
        1.1.3. ✅ Verify test pattern configurations
        1.1.4. ✅ Ensure marker definitions are complete

   1.2. Update .coveragerc
        1.2.1. ✅ Verify source paths are correct
        1.2.2. ✅ Confirm exclusion patterns
        1.2.3. ✅ Check branch coverage settings
        1.2.4. ✅ Validate report configurations

   1.3. Update CI/CD Configuration
        1.3.1. ✅ Modify coverage threshold in test-coverage.yml
        1.3.2. ✅ Verify coverage artifact upload
        1.3.3. ✅ Update coverage check command
        1.3.4. 🕔 Test workflow locally

2. Test Structure Verification
   2.1. Unit Test Discovery
        2.1.1. ✅ Verify all tests under tests/00-unit are discovered (79 tests found)
        2.1.2. ✅ Check test file naming patterns
        2.1.3. ✅ Validate test class naming
        2.1.4. ✅ Confirm test function naming

   2.2. Test Isolation
        2.2.1. ✅ Ensure mock tests remain separate
        2.2.2. ✅ Verify live tests are not included
        2.2.3. ✅ Check fixture isolation
        2.2.4. ✅ Validate import paths

3. Coverage Validation
   3.1. Coverage Reports
        3.1.1. ✅ Generate baseline coverage report
        3.1.2. ✅ Identify areas needing additional coverage:
               3.1.2.1. pipeline/frames.py (0%)
               3.1.2.2. pipeline/pipecat_runner.py (0%)
               3.1.2.3. storage_processor.py (15%)
               3.1.2.4. git.py (7%)
               3.1.2.5. telegram_transport.py (13%)
        3.1.3. ✅ Document coverage gaps
        3.1.4. 🕔 Plan coverage improvements

   3.2. Coverage Tools
        3.2.1. ✅ Verify pytest-cov installation
        3.2.2. ✅ Check coverage report generation
        3.2.3. ✅ Test HTML report creation
        3.2.4. ✅ Validate branch coverage reporting

4. Testing and Verification
   4.1. Local Testing
        4.1.1. ✅ Run complete test suite (79 tests passing)
        4.1.2. ✅ Verify coverage reports (28% current coverage)
        4.1.3. ✅ Check HTML output
        4.1.4. ✅ Validate branch coverage

   4.2. CI/CD Testing
        4.2.1. 🕔 Push changes to test branch
        4.2.2. 🕔 Verify GitHub Actions workflow
        4.2.3. 🕔 Check coverage reports in CI
        4.2.4. 🕔 Validate artifact generation

5. Coverage Improvements
   5.1. Storage Components
        5.1.1. ✅ Fix serializer tests (100% coverage)
        5.1.2. 🕔 Fix git storage tests (77% -> target 80%)
               5.1.2.1. ✅ Fix initialization tests
               5.1.2.2. ✅ Fix topic creation tests
               5.1.2.3. ✅ Add metadata management tests
               5.1.2.4. ✅ Add error handling tests
               5.1.2.5. ✅ Add git operations tests
               5.1.2.6. 🕔 Add remaining coverage:
                       5.1.2.6.1. Improve sync operation coverage
                       5.1.2.6.2. Add edge case tests for attachments
                       5.1.2.6.3. Add tests for remaining error conditions
        5.1.3. 🕔 Add coordinator tests (29% -> target 80%)
               5.1.3.1. Add message handling tests
               5.1.3.2. Add attachment processing tests
               5.1.3.3. Add error handling tests
        5.1.4. 🕔 Add filesystem tests (27% -> target 80%)
               5.1.4.1. Add file operations tests
               5.1.4.2. Add error handling tests
               5.1.4.3. Add path management tests

   5.2. Pipeline Components
        5.2.1. 🕔 Add frames tests (0% -> target 80%)
               5.2.1.1. Add frame processing tests
               5.2.1.2. Add validation tests
               5.2.1.3. Add error handling tests
        5.2.2. 🕔 Add pipecat_runner tests (0% -> target 80%)
               5.2.2.1. Add pipeline execution tests
               5.2.2.2. Add error handling tests
               5.2.2.3. Add state management tests
        5.2.3. 🕔 Add storage_processor tests (15% -> target 80%)
               5.2.3.1. Add message processing tests
               5.2.3.2. Add storage operations tests
               5.2.3.3. Add error handling tests

   5.3. Transport Components
        5.3.1. 🕔 Add telegram_transport tests (13% -> target 80%)
               5.3.1.1. Add message handling tests
               5.3.1.2. Add API interaction tests
               5.3.1.3. Add error handling tests
        5.3.2. 🕔 Add events tests (58% -> target 80%)
               5.3.2.1. Add event processing tests
               5.3.2.2. Add error handling tests
               5.3.2.3. Add state management tests 