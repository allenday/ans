# Implementation Checklist: Relax Unit Test Filters

1. 🔒 Configuration Updates
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

2. 🔒 Test Structure Verification
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

3. 🔒 Coverage Validation
3.1. Coverage Reports
3.1.1. ✅ Generate baseline coverage report
3.1.2. ✅ Identify areas needing additional coverage:
3.1.2.1. pipeline/frames.py (0%)
3.1.2.2. pipeline/pipecat_runner.py (0%)
3.1.2.3. storage_processor.py (0%)
3.1.2.4. git.py (8%)
3.1.2.5. telegram_transport.py (11%)
3.1.3. 🛑 Document coverage gaps
3.1.4. 🛑 Plan coverage improvements

3.2. Coverage Tools
3.2.1. ✅ Verify pytest-cov installation
3.2.2. ✅ Check coverage report generation
3.2.3. ✅ Test HTML report creation
3.2.4. ✅ Validate branch coverage reporting

4. 🔒 Testing and Verification
4.1. Local Testing
4.1.1. ✅ Run complete test suite (79 tests passing)
4.1.2. ✅ Verify coverage reports (39% current coverage)
4.1.3. ✅ Check HTML output
4.1.4. ✅ Validate branch coverage

4.2. CI/CD Testing
4.2.1. 🕔 Push changes to test branch
4.2.2. 🕔 Verify GitHub Actions workflow
4.2.3. 🕔 Check coverage reports in CI
4.2.4. 🕔 Validate artifact generation 