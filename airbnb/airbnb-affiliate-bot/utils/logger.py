"""
Logging Configuration System
Provides centralized logging setup with file rotation and formatting.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: str = "10MB",
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger('airbnb_affiliate_bot')
    logger.setLevel(numeric_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max file size
        max_bytes = _parse_file_size(max_file_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def _parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str: Size string like "10MB", "1GB", "500KB"
    
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    # Extract number and unit
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes if no unit specified
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'airbnb_affiliate_bot.{name}')


class LoggerMixin:
    """Mixin class to add logging capability to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


# Example usage and testing
if __name__ == "__main__":
    # Test logging setup
    logger = setup_logging(
        log_level="DEBUG",
        log_file="test_logs/test.log",
        max_file_size="1MB",
        backup_count=3
    )
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test child logger
    child_logger = get_logger("test_module")
    child_logger.info("This is from a child logger")
    
    # Test LoggerMixin
    class TestClass(LoggerMixin):
        def test_method(self):
            self.logger.info("This is from a class with LoggerMixin")
    
    test_obj = TestClass()
    test_obj.test_method()
    
    print("Logging test completed. Check test_logs/test.log for output.")
