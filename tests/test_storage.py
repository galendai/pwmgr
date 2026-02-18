"""
Tests for PasswordStorage.
"""
import pytest
import os
import tempfile

from pwmgr.core.storage import PasswordStorage
from pwmgr.core.models import PasswordEntry


class TestPasswordStorage:
    """Test cases for PasswordStorage."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_passwords.json.enc")
            storage = PasswordStorage(file_path)
            yield storage

    @pytest.fixture
    def temp_storage_with_data(self, temp_storage):
        """Create a storage initialized with test data."""
        master_password = "test_master_password"
        temp_storage.initialize(master_password)
        return temp_storage, master_password

    def test_initialization(self, temp_storage):
        """Test storage initialization."""
        master_password = "test_password"

        assert not temp_storage.file_exists()
        temp_storage.initialize(master_password)
        assert temp_storage.file_exists()

    def test_save_and_load_entries(self, temp_storage_with_data):
        """Test saving and loading password entries."""
        storage, master_password = temp_storage_with_data

        entries = [
            PasswordEntry(name="Site1", username="user1", password="pass1"),
            PasswordEntry(name="Site2", username="user2", password="pass2", notes="Test notes")
        ]

        storage.save(entries, master_password)
        loaded_entries = storage.load(master_password)

        assert len(loaded_entries) == 2
        assert loaded_entries[0].name == "Site1"
        assert loaded_entries[1].name == "Site2"
        assert loaded_entries[1].notes == "Test notes"

    def test_load_with_wrong_password(self, temp_storage_with_data):
        """Test that loading with wrong password returns None."""
        storage, master_password = temp_storage_with_data

        entries = [PasswordEntry(name="Site1", username="user1", password="pass1")]
        storage.save(entries, master_password)

        wrong_password = "wrong_password"
        loaded = storage.load(wrong_password)

        assert loaded is None

    def test_load_nonexistent_file(self, temp_storage):
        """Test loading from nonexistent file returns empty list."""
        master_password = "password"
        loaded = temp_storage.load(master_password)

        assert loaded == []

    def test_is_valid_master_password(self, temp_storage_with_data):
        """Test master password validation."""
        storage, master_password = temp_storage_with_data

        assert storage.is_valid_master_password(master_password) is True
        assert storage.is_valid_master_password("wrong_password") is False

    def test_is_valid_master_password_no_file(self, temp_storage):
        """Test master password validation when file doesn't exist."""
        assert temp_storage.is_valid_master_password("any_password") is False

    def test_save_empty_entries(self, temp_storage_with_data):
        """Test saving empty entries list."""
        storage, master_password = temp_storage_with_data

        storage.save([], master_password)
        loaded = storage.load(master_password)

        assert loaded == []

    def test_overwrite_entries(self, temp_storage_with_data):
        """Test overwriting existing entries."""
        storage, master_password = temp_storage_with_data

        entries1 = [PasswordEntry(name="Site1", username="user1", password="pass1")]
        storage.save(entries1, master_password)

        entries2 = [
            PasswordEntry(name="Site2", username="user2", password="pass2"),
            PasswordEntry(name="Site3", username="user3", password="pass3")
        ]
        storage.save(entries2, master_password)

        loaded = storage.load(master_password)
        assert len(loaded) == 2
        assert all(e.name != "Site1" for e in loaded)

    def test_file_exists(self, temp_storage):
        """Test file_exists method."""
        assert not temp_storage.file_exists()

        temp_storage.initialize("password")
        assert temp_storage.file_exists()

    def test_get_security_warnings(self, temp_storage):
        """Test getting security warnings."""
        warnings = temp_storage.get_security_warnings()

        # Should return a list (may be empty on secure systems)
        assert isinstance(warnings, list)

    def test_atomic_save(self, temp_storage):
        """Test that save is atomic (no temp file left on success)."""
        master_password = "password"
        temp_storage.initialize(master_password)

        entries = [PasswordEntry(name="Test", username="user", password="pass")]
        temp_storage.save(entries, master_password)

        # No temp file should exist
        temp_file = temp_storage.file_path + '.tmp'
        assert not os.path.exists(temp_file)


class TestPasswordStorageSecurity:
    """Test security features of PasswordStorage."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_passwords.json.enc")
            storage = PasswordStorage(file_path)
            yield storage

    def test_encrypted_file_content(self, temp_storage):
        """Test that file content is encrypted, not plaintext."""
        master_password = "password"
        entries = [PasswordEntry(name="SecretSite", username="secretuser", password="secretpass")]

        temp_storage.save(entries, master_password)

        with open(temp_storage.file_path, 'r') as f:
            content = f.read()

        # Plaintext data should not appear in file
        assert "SecretSite" not in content
        assert "secretuser" not in content
        assert "secretpass" not in content
