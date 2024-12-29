import pytest
import logging

@pytest.fixture
def test_log_level(request):
    """Get log level from pytest configuration"""
    level = request.config.getoption("--log-cli-level", default="WARNING")
    if level is None:
        return logging.WARNING
    
    # Convert string level to logging constant
    level_map = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG
    }
    
    return level_map.get(str(level).upper(), logging.WARNING)

def pytest_configure(config):
    """Configure logging for tests"""
    log_level = config.getoption("--log-cli-level", default="WARNING")
    if log_level is None:
        log_level = logging.WARNING
    else:
        # Convert string level to logging constant
        level_map = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG
        }
        log_level = level_map.get(str(log_level).upper(), logging.WARNING)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=config.getoption("--log-cli-format"),
        datefmt=config.getoption("--log-cli-date-format"),
        force=True
    )

    # Configure module loggers
    logging.getLogger('git').setLevel(max(logging.WARNING, log_level))
    logging.getLogger('chronicler').setLevel(log_level) 