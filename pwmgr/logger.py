"""
Logging configuration for the password manager.
Provides audit logging and sensitive data sanitization.
"""
import os
import logging
import json
from datetime import datetime
from typing import Optional, Any
from pathlib import Path


# Sensitive field names that should be redacted in logs
SENSITIVE_FIELDS = {'password', 'master_password', 'secret', 'token', 'key', 'credential'}


def sanitize_data(data: Any) -> Any:
    """
    Sanitize sensitive data for logging.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized copy of data with sensitive fields redacted
    """
    if isinstance(data, dict):
        return {
            key: '***REDACTED***' if key.lower() in SENSITIVE_FIELDS else sanitize_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        # Check if the string looks like it might contain sensitive data
        lower_data = data.lower()
        for field in SENSITIVE_FIELDS:
            if field in lower_data and ':' in data:
                # Potential key:value pair, redact the value
                return '***REDACTED***'
        return data
    else:
        return data


class AuditLogFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive data."""

    def format(self, record):
        # Sanitize the message if it contains arguments
        if record.args:
            record.args = sanitize_data(record.args)
        return super().format(record)


class PassMgrLogger:
    """
    Centralized logging for the password manager.
    Provides both file and console logging with sensitive data sanitization.
    """

    DEFAULT_LOG_DIR = os.path.expanduser("~/.pwmgr/logs")
    DEFAULT_LOG_FILE = "pwmgr.log"

    def __init__(self, name: str = "pwmgr", log_dir: Optional[str] = None, level: int = logging.INFO):
        """
        Initialize the logger.

        Args:
            name: Logger name
            log_dir: Directory for log files (default: ~/.pwmgr/logs)
            level: Logging level
        """
        self.name = name
        self.log_dir = log_dir or self.DEFAULT_LOG_DIR
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up log handlers."""
        # Avoid adding duplicate handlers
        if self.logger.handlers:
            return

        # Create log directory if it doesn't exist
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)

        # File handler
        log_file = os.path.join(self.log_dir, self.DEFAULT_LOG_FILE)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = AuditLogFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler (only for warnings and above by default)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = AuditLogFormatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def audit(self, action: str, details: Optional[dict] = None):
        """
        Log an audit event.

        Args:
            action: The action being performed
            details: Additional details (will be sanitized)
        """
        sanitized_details = sanitize_data(details) if details else {}
        self.logger.info(f"AUDIT: {action} | {json.dumps(sanitized_details)}")

    def debug(self, message: str, *args):
        """Log a debug message."""
        self.logger.debug(message, *args)

    def info(self, message: str, *args):
        """Log an info message."""
        self.logger.info(message, *args)

    def warning(self, message: str, *args):
        """Log a warning message."""
        self.logger.warning(message, *args)

    def error(self, message: str, *args):
        """Log an error message."""
        self.logger.error(message, *args)

    def exception(self, message: str, *args):
        """Log an exception with traceback."""
        self.logger.exception(message, *args)


# Global logger instance
_logger: Optional[PassMgrLogger] = None


def get_logger() -> PassMgrLogger:
    """
    Get the global logger instance.

    Returns:
        PassMgrLogger instance
    """
    global _logger
    if _logger is None:
        _logger = PassMgrLogger()
    return _logger


def log_audit(action: str, details: Optional[dict] = None):
    """
    Convenience function to log an audit event.

    Args:
        action: The action being performed
        details: Additional details (will be sanitized)
    """
    get_logger().audit(action, details)
