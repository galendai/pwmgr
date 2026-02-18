"""
Custom exceptions for the password manager.
"""


class PassMgrError(Exception):
    """Base exception for all password manager errors."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ValidationError(PassMgrError):
    """Exception raised for input validation errors."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        code = f"VALIDATION_ERROR{f'_{field.upper()}' if field else ''}"
        super().__init__(message, code)


class AuthenticationError(PassMgrError):
    """Exception raised for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class EncryptionError(PassMgrError):
    """Exception raised for encryption/decryption errors."""

    def __init__(self, message: str = "Encryption operation failed"):
        super().__init__(message, "ENCRYPTION_ERROR")


class StorageError(PassMgrError):
    """Exception raised for storage operation errors."""

    def __init__(self, message: str, operation: str = None):
        self.operation = operation
        code = f"STORAGE_ERROR{f'_{operation.upper()}' if operation else ''}"
        super().__init__(message, code)


class EntryNotFoundError(PassMgrError):
    """Exception raised when a password entry is not found."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Password entry '{name}' not found", "ENTRY_NOT_FOUND")


class EntryExistsError(PassMgrError):
    """Exception raised when trying to create a duplicate entry."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Password entry '{name}' already exists", "ENTRY_EXISTS")


class ConfigurationError(PassMgrError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class BackupError(PassMgrError):
    """Exception raised for backup/restore operation errors."""

    def __init__(self, message: str, operation: str = None):
        self.operation = operation
        code = f"BACKUP_ERROR{f'_{operation.upper()}' if operation else ''}"
        super().__init__(message, code)
