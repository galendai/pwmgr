"""
Backup and restore functionality for the password manager.
"""
import os
import json
import shutil
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from ..crypto import EncryptionService
from .models import PasswordEntry
from ..exceptions import BackupError
from ..logger import log_audit


class BackupManager:
    """
    Handles backup and restore operations for password data.
    """

    DEFAULT_BACKUP_DIR = os.path.expanduser("~/.pwmgr/backups")
    BACKUP_PREFIX = "pwmgr_backup_"
    BACKUP_EXTENSION = ".enc"

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize the backup manager.

        Args:
            backup_dir: Directory for backup files (default: ~/.pwmgr/backups)
        """
        self.backup_dir = backup_dir or self.DEFAULT_BACKUP_DIR
        self._ensure_backup_dir_exists()

    def _ensure_backup_dir_exists(self) -> None:
        """Ensure the backup directory exists."""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def _get_backup_filename(self, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a backup filename.

        Args:
            timestamp: Timestamp for the backup (default: now)

        Returns:
            Backup filename
        """
        if timestamp is None:
            timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{self.BACKUP_PREFIX}{timestamp_str}{self.BACKUP_EXTENSION}"

    def create_backup(self, entries: List[PasswordEntry], master_password: str,
                      name: Optional[str] = None) -> str:
        """
        Create a backup of password entries.

        Args:
            entries: List of password entries to backup
            master_password: Master password for encryption
            name: Optional custom name for the backup

        Returns:
            Path to the created backup file

        Raises:
            BackupError: If backup creation fails
        """
        try:
            # Prepare backup data
            backup_data = {
                "version": 1,
                "created_at": datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in entries]
            }

            # Encrypt the backup
            json_data = json.dumps(backup_data)
            encrypted_data = EncryptionService.encrypt_password_data(json_data, master_password)

            # Generate filename
            if name:
                # Sanitize name
                name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
                filename = f"{self.BACKUP_PREFIX}{name}{self.BACKUP_EXTENSION}"
            else:
                filename = self._get_backup_filename()

            backup_path = os.path.join(self.backup_dir, filename)

            # Write backup file
            with open(backup_path, 'w') as f:
                f.write(encrypted_data)

            log_audit("CREATE_BACKUP", {"path": backup_path, "entries_count": len(entries)})

            return backup_path

        except Exception as e:
            raise BackupError(f"Failed to create backup: {str(e)}", operation="create")

    def restore_backup(self, backup_path: str, master_password: str) -> List[PasswordEntry]:
        """
        Restore password entries from a backup.

        Args:
            backup_path: Path to the backup file
            master_password: Master password for decryption

        Returns:
            List of restored password entries

        Raises:
            BackupError: If restore fails
        """
        try:
            if not os.path.exists(backup_path):
                raise BackupError(f"Backup file not found: {backup_path}", operation="restore")

            # Read and decrypt backup
            with open(backup_path, 'r') as f:
                encrypted_data = f.read()

            json_data = EncryptionService.decrypt_password_data(encrypted_data, master_password)
            if json_data is None:
                raise BackupError("Failed to decrypt backup. Wrong password?", operation="restore")

            # Parse backup data
            backup_data = json.loads(json_data)

            # Validate backup format
            if "entries" not in backup_data:
                raise BackupError("Invalid backup format: missing entries", operation="restore")

            # Convert to PasswordEntry objects
            entries = [PasswordEntry.from_dict(entry_dict) for entry_dict in backup_data["entries"]]

            log_audit("RESTORE_BACKUP", {"path": backup_path, "entries_count": len(entries)})

            return entries

        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"Failed to restore backup: {str(e)}", operation="restore")

    def list_backups(self) -> List[dict]:
        """
        List all available backups.

        Returns:
            List of backup info dictionaries
        """
        backups = []

        if not os.path.exists(self.backup_dir):
            return backups

        for filename in os.listdir(self.backup_dir):
            if filename.startswith(self.BACKUP_PREFIX) and filename.endswith(self.BACKUP_EXTENSION):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    def delete_backup(self, backup_path: str) -> None:
        """
        Delete a backup file.

        Args:
            backup_path: Path to the backup file

        Raises:
            BackupError: If deletion fails
        """
        try:
            if not os.path.exists(backup_path):
                raise BackupError(f"Backup file not found: {backup_path}", operation="delete")

            os.remove(backup_path)
            log_audit("DELETE_BACKUP", {"path": backup_path})

        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"Failed to delete backup: {str(e)}", operation="delete")

    def get_backup_info(self, backup_path: str, master_password: str) -> dict:
        """
        Get information about a backup file without fully restoring it.

        Args:
            backup_path: Path to the backup file
            master_password: Master password for decryption

        Returns:
            Dictionary with backup information

        Raises:
            BackupError: If reading backup fails
        """
        try:
            if not os.path.exists(backup_path):
                raise BackupError(f"Backup file not found: {backup_path}", operation="info")

            # Read and decrypt backup
            with open(backup_path, 'r') as f:
                encrypted_data = f.read()

            json_data = EncryptionService.decrypt_password_data(encrypted_data, master_password)
            if json_data is None:
                raise BackupError("Failed to decrypt backup. Wrong password?", operation="info")

            backup_data = json.loads(json_data)

            return {
                "version": backup_data.get("version", "unknown"),
                "created_at": backup_data.get("created_at", "unknown"),
                "entries_count": len(backup_data.get("entries", [])),
                "entry_names": [e.get("name", "unknown") for e in backup_data.get("entries", [])]
            }

        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"Failed to read backup info: {str(e)}", operation="info")
