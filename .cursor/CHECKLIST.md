# Development Checklist

## Scope Validation
- [ ] Verify scope has clear goal
- [ ] Verify requirements are specific
- [ ] Verify constraints are understood
- [ ] Verify acceptance criteria are testable
- [ ] Check alignment with architecture
- [ ] Check for similar implementations

## Scope Control
- [ ] Document initial scope hash (requirements + acceptance)
- [ ] Flag any deviations from initial scope
- [ ] Push new requirements to backlog.md
- [ ] Maintain focus on original acceptance criteria
- [ ] Get explicit approval for scope changes

## Pre-Implementation
- [ ] Create feature branch
- [ ] Write unit tests first
- [ ] Write mock tests if external dependencies
- [ ] Write live tests if applicable
- [ ] Run tests to verify they fail (TDD)

## Implementation
- [ ] Add debug logging for all operations
  - Entry/exit of key methods
  - Important state changes
  - Data transformations
  - Error conditions
- [ ] Add exception handling
  - Specific exception types
  - Meaningful error messages
  - Proper error propagation
  - Recovery strategies
- [ ] Add type hints
- [ ] Add docstrings

## Testing
- [ ] Run unit tests
- [ ] Run mock tests
- [ ] Run live tests
- [ ] Add missing test cases
- [ ] Test error conditions
- [ ] Test edge cases

## Review
- [ ] Update documentation
- [ ] Check log coverage
- [ ] Check error handling
- [ ] Check test coverage
- [ ] Run linter
- [ ] Self-review code

## Example Implementation

### 1. Test First (TDD)
```python
def test_process_voice_message():
    """Test processing a voice message."""
    # Arrange
    processor = VoiceProcessor()
    voice_data = b"test_data"
    
    # Act
    result = processor.process(voice_data)
    
    # Assert
    assert result.format == "ogg"
    assert result.duration > 0
```

### 2. Add Logging
```python
logger = logging.getLogger(__name__)

class VoiceProcessor:
    def process(self, data: bytes) -> VoiceResult:
        """Process voice message data."""
        logger.debug("Starting voice processing", extra={"data_size": len(data)})
        try:
            result = self._process_internal(data)
            logger.info("Voice processing successful", 
                       extra={"format": result.format, "duration": result.duration})
            return result
        except Exception as e:
            logger.error("Voice processing failed", exc_info=True)
            raise VoiceProcessingError("Failed to process voice message") from e
```

### 3. Error Handling
```python
class VoiceProcessingError(Exception):
    """Raised when voice processing fails."""
    pass

def _process_internal(self, data: bytes) -> VoiceResult:
    """Internal processing with error handling."""
    if not data:
        raise ValueError("Empty voice data")
    
    try:
        # Process voice data
        format = self._detect_format(data)
        duration = self._get_duration(data)
        return VoiceResult(format=format, duration=duration)
    except FormatError as e:
        raise VoiceProcessingError("Invalid voice format") from e
    except DurationError as e:
        raise VoiceProcessingError("Could not determine duration") from e
```

### 4. Complete Tests
```python
class TestVoiceProcessor:
    """Test suite for VoiceProcessor."""
    
    def test_empty_data(self):
        """Test handling of empty data."""
        processor = VoiceProcessor()
        with pytest.raises(ValueError):
            processor.process(b"")
    
    def test_invalid_format(self):
        """Test handling of invalid format."""
        processor = VoiceProcessor()
        with pytest.raises(VoiceProcessingError):
            processor.process(b"invalid_data")
    
    def test_successful_processing(self):
        """Test successful voice processing."""
        processor = VoiceProcessor()
        result = processor.process(VALID_VOICE_DATA)
        assert result.format == "ogg"
        assert result.duration == 10.5
``` 