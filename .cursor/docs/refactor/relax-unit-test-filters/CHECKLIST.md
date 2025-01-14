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
        1.3.4. ✅ Test workflow locally

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
               3.1.2.1. ✅ pipeline/frames.py (100%)
               3.1.2.2. 🕔 pipeline/pipecat_runner.py (23%)
               3.1.2.3. ✅ storage_processor.py (87%)
               3.1.2.4. ✅ git.py (77%)
               3.1.2.5. ✅ telegram_transport.py (56%)
        3.1.3. ✅ Document coverage gaps
        3.1.4. ✅ Plan coverage improvements

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
        4.2.1. ✅ Push changes to test branch
        4.2.2. ✅ Verify GitHub Actions workflow
        4.2.3. ✅ Check coverage reports in CI
        4.2.4. ✅ Validate artifact generation

5. Coverage Improvements
   5.1. Storage Components
        5.1.1. ✅ Fix serializer tests (100% coverage)
        5.1.2. ✅ Fix git storage tests (90% coverage achieved)
               5.1.2.1. ✅ Fix initialization tests
               5.1.2.2. ✅ Fix topic creation tests
               5.1.2.3. ✅ Add metadata management tests
               5.1.2.4. ✅ Add error handling tests
               5.1.2.5. ✅ Add git operations tests
               5.1.2.6. ✅ Add remaining coverage:
                       5.1.2.6.1. ✅ Improve sync operation coverage
                       5.1.2.6.2. ✅ Add edge case tests for attachments
                       5.1.2.6.3. ✅ Add tests for remaining error conditions
        5.1.3. ✅ Add coordinator tests (100% coverage achieved)
               5.1.3.1. ✅ Add message handling tests
               5.1.3.2. ✅ Add attachment processing tests
               5.1.3.3. ✅ Add error handling tests
        5.1.4. ✅ Add filesystem tests (100% coverage achieved)
               5.1.4.1. ✅ Add file operations tests
               5.1.4.2. ✅ Add error handling tests
               5.1.4.3. ✅ Add path management tests

   5.2. Pipeline Components
        5.2.1. ✅ Add frames tests (0% -> 100%)
               5.2.1.1. ✅ Base Frame Tests
                       5.2.1.1.1. ✅ Test metadata handling
                       5.2.1.1.2. ✅ Test optional text field
                       5.2.1.1.3. ✅ Test logging functionality
               5.2.1.2. ✅ TextFrame Tests
                       5.2.1.2.1. ✅ Test valid string content
                       5.2.1.2.2. ✅ Test invalid content types
                       5.2.1.2.3. ✅ Test empty string handling
               5.2.1.3. ✅ ImageFrame Tests
                       5.2.1.3.1. ✅ Test valid image data
                       5.2.1.3.2. ✅ Test size validation
                       5.2.1.3.3. ✅ Test format handling
                       5.2.1.3.4. ✅ Test caption handling
               5.2.1.4. ✅ DocumentFrame Tests
                       5.2.1.4.1. ✅ Test valid document data
                       5.2.1.4.2. ✅ Test filename validation
                       5.2.1.4.3. ✅ Test MIME type handling
                       5.2.1.4.4. ✅ Test caption propagation
               5.2.1.5. ✅ AudioFrame Tests
                       5.2.1.5.1. ✅ Test valid audio data
                       5.2.1.5.2. ✅ Test duration validation
                       5.2.1.5.3. ✅ Test MIME type handling
               5.2.1.6. ✅ VoiceFrame Tests
                       5.2.1.6.1. ✅ Test valid voice data
                       5.2.1.6.2. ✅ Test duration validation
                       5.2.1.6.3. ✅ Test MIME type handling
               5.2.1.7. ✅ StickerFrame Tests
                       5.2.1.7.1. ✅ Test valid sticker data
                       5.2.1.7.2. ✅ Test emoji validation
                       5.2.1.7.3. ✅ Test set name handling
               5.2.1.8. ✅ CommandFrame Tests
                       5.2.1.8.1. ✅ Test command validation
                       5.2.1.8.2. ✅ Test argument handling
                       5.2.1.8.3. ✅ Test command normalization
        5.2.2. 🕔 Add pipecat_runner tests (23% -> target 80%)
               5.2.2.1. 🕔 Add pipeline execution tests
               5.2.2.2. 🕔 Add error handling tests
               5.2.2.3. 🕔 Add state management tests
        5.2.3. ✅ Add storage_processor tests (87% -> target 80%)
               5.2.3.1. ✅ Add metadata validation tests:
                       5.2.3.1.1. ✅ Test missing required metadata fields
                       5.2.3.1.2. ✅ Test invalid metadata values
                       5.2.3.1.3. ✅ Test metadata field propagation
                       5.2.3.1.4. ✅ Test error handling for invalid metadata
               5.2.3.2. ✅ Add topic creation tests:
                       5.2.3.2.1. ✅ Test duplicate topic handling
                       5.2.3.2.2. ✅ Test invalid topic names
                       5.2.3.2.3. ✅ Test missing chat title
                       5.2.3.2.4. ✅ Test topic metadata validation
               5.2.3.3. ✅ Add frame processing tests:
                       5.2.3.3.1. ✅ Test unsupported frame types
                       5.2.3.3.2. ✅ Test frame content validation
                       5.2.3.3.3. ✅ Test frame processing errors
                       5.2.3.3.4. ✅ Test concurrent frame processing
               5.2.3.4. ✅ Add attachment tests:
                       5.2.3.4.1. ✅ Test missing attachment data
                       5.2.3.4.2. ✅ Test invalid MIME types
                       5.2.3.4.3. ✅ Test large attachments
                       5.2.3.4.4. ✅ Test multiple attachments
               5.2.3.5. ✅ Add logging tests:
                       5.2.3.5.1. ✅ Test error logging
                       5.2.3.5.2. ✅ Test debug logging
                       5.2.3.5.3. ✅ Test info logging
                       5.2.3.5.4. ✅ Test log context data

   5.3. Transport Components
        5.3.1. 🕔 Add telegram_transport tests (56% -> target 80%)
               5.3.1.1. ✅ Add message type handling tests
                       5.3.1.1.1. ✅ Test text message processing
                       5.3.1.1.2. ✅ Test photo message processing
                       5.3.1.1.3. ✅ Test sticker message processing
                       5.3.1.1.4. ✅ Test document message processing
                       5.3.1.1.5. ✅ Test audio message processing
                       5.3.1.1.6. ✅ Test voice message processing
               5.3.1.2. ✅ Add metadata handling tests
                       5.3.1.2.1. ✅ Test chat metadata extraction
                       5.3.1.2.2. ✅ Test user metadata extraction
                       5.3.1.2.3. ✅ Test message metadata extraction
               5.3.1.3. ✅ Add forum support tests
                       5.3.1.3.1. ✅ Test topic creation handling
                       5.3.1.3.2. ✅ Test thread ID management
                       5.3.1.3.3. ✅ Test topic name extraction
               5.3.1.4. ✅ Add forward message tests
                       5.3.1.4.1. ✅ Test forward origin extraction
                       5.3.1.4.2. ✅ Test forward metadata handling
                       5.3.1.4.3. ✅ Test forward date handling
               5.3.1.5. ✅ Add web page preview tests
                       5.3.1.5.1. ✅ Test URL extraction
                       5.3.1.5.2. ✅ Test preview metadata handling
                       5.3.1.5.3. ✅ Test thumbnail handling
               5.3.1.6. ✅ Add command processing tests
                       5.3.1.6.1. ✅ Test command recognition
                       5.3.1.6.2. ✅ Test command argument parsing
                       5.3.1.6.3. ✅ Test command frame creation
               5.3.1.7. ✅ Add frame processing tests
                       5.3.1.7.1. ✅ Test frame creation
                       5.3.1.7.2. ✅ Test frame validation
                       5.3.1.7.3. ✅ Test frame sending
        5.3.2. ✅ Add events tests (95% -> target 80%)
               5.3.2.1. ✅ Add event processing tests
               5.3.2.2. ✅ Add error handling tests
               5.3.2.3. ✅ Add state management tests 