"""
Storage module for the password manager.
Handles reading and writing of encrypted password data.
"""
import os
import json
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
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the password storage.
        
        Args:
            file_path: Path to the password file. If not provided, uses the default path.
        """
        self.file_path = file_path or self.DEFAULT_FILE_PATH
        self._ensure_storage_dir_exists()
    
    def _ensure_storage_dir_exists(self) -> None:
        """Ensure the storage directory exists."""
        dir_path = os.path.dirname(self.file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    def file_exists(self) -> bool:
        """
        Check if the password file exists.
        
        Returns:
            True if the file exists, False otherwise
        """
        return os.path.exists(self.file_path)
    
    def save(self, entries: List[PasswordEntry], master_password: str) -> None:
        """
        Save password entries to file.
        
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
        
        with open(self.file_path, 'w') as f:
            f.write(encrypted_data)
    
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
        Initialize a new password file.
        
        Args:
            master_password: Master password for encryption
        """
        # Create an empty password database
        self.save([], master_password)
    
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