"""
Storage module for the password manager.
Handles reading and writing of encrypted password data.
"""
import os
import json
import stat
import platform
from typing import List, Optional, Dict, Any
import os.path

from ..crypto import EncryptionService
from .models import PasswordEntry


class PasswordStorage:
    """
    Handles storage and retrieval of encrypted password entries.
    """

    DEFAULT_FILE_PATH = os.path.expanduser("~/.pwmgr/passwords.json.enc")
    DEFAULT_DIR_PATH = os.path.dirname(DEFAULT_FILE_PATH)

    # Secure file permissions: read/write for owner only
    SECURE_FILE_MODE = 0o600
    SECURE_DIR_MODE = 0o700

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the password storage.

        Args:
            file_path: Path to the password file. If not provided, uses the default path.
        """
        self.file_path = file_path or self.DEFAULT_FILE_PATH
        self._ensure_storage_dir_exists()

    def _ensure_storage_dir_exists(self) -> None:
        """Ensure the storage directory exists with secure permissions."""
        dir_path = os.path.dirname(self.file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            self._set_secure_dir_permissions(dir_path)

    def _set_secure_file_permissions(self, file_path: str) -> None:
        """
        Set secure permissions on a file (owner read/write only).

        Args:
            file_path: Path to the file
        """
        # On Windows, file permissions work differently
        # We still try to set restrictive permissions, but they may not have the same effect
        try:
            current_mode = os.stat(file_path).st_mode
            # Remove all permissions for group and others
            new_mode = current_mode & (stat.S_IRUSR | stat.S_IWUSR)
            os.chmod(file_path, new_mode)
        except OSError:
            # Silently ignore permission errors on systems that don't support Unix permissions
            pass

    def _set_secure_dir_permissions(self, dir_path: str) -> None:
        """
        Set secure permissions on a directory (owner access only).

        Args:
            dir_path: Path to the directory
        """
        try:
            current_mode = os.stat(dir_path).st_mode
            # Remove all permissions for group and others
            new_mode = current_mode & (stat.S_IRWXU)
            os.chmod(dir_path, new_mode)
        except OSError:
            pass

    def _check_file_permissions(self) -> Optional[str]:
        """
        Check if file permissions are secure.

        Returns:
            Warning message if permissions are insecure, None otherwise
        """
        if not self.file_exists():
            return None

        try:
            file_stat = os.stat(self.file_path)
            mode = file_stat.st_mode

            # Check if group or others have any access
            if mode & (stat.S_IRWXG | stat.S_IRWXO):
                return (f"Warning: Password file '{self.file_path}' has insecure permissions. "
                        f"Run: chmod 600 '{self.file_path}'")
        except OSError:
            pass

        return None

    def _check_platform_security(self) -> Optional[str]:
        """
        Check platform-specific security considerations.

        Returns:
            Warning message for Windows users, None for Unix-like systems
        """
        if platform.system() == 'Windows':
            return ("Note: On Windows, file permissions are managed by ACLs. "
                    "Ensure your password file is in a secure location accessible only to your user account.")
        return None

    def file_exists(self) -> bool:
        """
        Check if the password file exists.

        Returns:
            True if the file exists, False otherwise
        """
        return os.path.exists(self.file_path)

    def save(self, entries: List[PasswordEntry], master_password: str) -> None:
        """
        Save password entries to file with secure permissions.

        Args:
            entries: List of password entries to save
            master_password: Master password for encryption
        """
        # Convert entries to dictionary format
        data = {
            "entries": [entry.to_dict() for entry in entries]
        }

        # Encrypt and save
        json_data = json.dumps(data)
        encrypted_data = EncryptionService.encrypt_password_data(json_data, master_password)

        # Write to a temporary file first, then rename for atomic operation
        temp_file = self.file_path + '.tmp'
        try:
            with open(temp_file, 'w') as f:
                f.write(encrypted_data)

            # Set secure permissions before moving
            self._set_secure_file_permissions(temp_file)

            # Atomic rename
            os.replace(temp_file, self.file_path)

            # Ensure final file has secure permissions
            self._set_secure_file_permissions(self.file_path)

        finally:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    def load(self, master_password: str) -> Optional[List[PasswordEntry]]:
        """
        Load password entries from file.

        Args:
            master_password: Master password for decryption

        Returns:
            List of password entries or None if decryption fails
        """
        if not self.file_exists():
            return []

        # Check file permissions (informational only)
        permission_warning = self._check_file_permissions()

        with open(self.file_path, 'r') as f:
            encrypted_data = f.read()

        # Decrypt the data
        json_data = EncryptionService.decrypt_password_data(encrypted_data, master_password)
        if json_data is None:
            return None

        # Parse the decrypted data
        data = json.loads(json_data)

        # Convert dictionaries to PasswordEntry objects
        entries = [PasswordEntry.from_dict(entry_dict) for entry_dict in data.get("entries", [])]

        return entries

    def initialize(self, master_password: str) -> None:
        """
        Initialize a new password file with secure permissions.

        Args:
            master_password: Master password for encryption
        """
        # Create an empty password database
        self.save([], master_password)

        # Set directory permissions as well
        self._set_secure_dir_permissions(os.path.dirname(self.file_path))

    def is_valid_master_password(self, master_password: str) -> bool:
        """
        Check if the provided master password is valid.

        Args:
            master_password: Master password to check

        Returns:
            True if the password is valid, False otherwise
        """
        if not self.file_exists():
            return False

        return self.load(master_password) is not None

    def get_security_warnings(self) -> List[str]:
        """
        Get any security warnings about the storage configuration.

        Returns:
            List of warning messages
        """
        warnings = []

        # Check file permissions
        perm_warning = self._check_file_permissions()
        if perm_warning:
            warnings.append(perm_warning)

        # Check platform-specific considerations
        platform_warning = self._check_platform_security()
        if platform_warning:
            warnings.append(platform_warning)

        return warnings 