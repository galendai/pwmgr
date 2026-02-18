"""
Tests for PasswordEntry model.
"""
import pytest
from datetime import datetime

from pwmgr.core.models import PasswordEntry


class TestPasswordEntry:
    """Test cases for PasswordEntry model."""

    def test_create_entry_with_required_fields(self):
        """Test creating an entry with only required fields."""
        entry = PasswordEntry(
            name="TestSite",
            username="testuser",
            password="testpass123"
        )

        assert entry.name == "TestSite"
        assert entry.username == "testuser"
        assert entry.password == "testpass123"
        assert entry.notes is None
        assert entry.id is not None
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_create_entry_with_all_fields(self):
        """Test creating an entry with all fields."""
        entry = PasswordEntry(
            name="TestSite",
            username="testuser",
            password="testpass123",
            notes="Test notes",
            id="custom-id",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )

        assert entry.name == "TestSite"
        assert entry.username == "testuser"
        assert entry.password == "testpass123"
        assert entry.notes == "Test notes"
        assert entry.id == "custom-id"
        assert entry.created_at == "2024-01-01T00:00:00"
        assert entry.updated_at == "2024-01-02T00:00:00"

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = PasswordEntry(
            name="TestSite",
            username="testuser",
            password="testpass123",
            notes="Test notes",
            id="test-id",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )

        result = entry.to_dict()

        assert result == {
            "id": "test-id",
            "name": "TestSite",
            "username": "testuser",
            "password": "testpass123",
            "notes": "Test notes",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00"
        }

    def test_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "id": "test-id",
            "name": "TestSite",
            "username": "testuser",
            "password": "testpass123",
            "notes": "Test notes",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00"
        }

        entry = PasswordEntry.from_dict(data)

        assert entry.id == "test-id"
        assert entry.name == "TestSite"
        assert entry.username == "testuser"
        assert entry.password == "testpass123"
        assert entry.notes == "Test notes"
        assert entry.created_at == "2024-01-01T00:00:00"
        assert entry.updated_at == "2024-01-02T00:00:00"

    def test_from_dict_with_missing_optional_fields(self):
        """Test creating entry from dictionary with missing optional fields."""
        data = {
            "name": "TestSite",
            "username": "testuser",
            "password": "testpass123"
        }

        entry = PasswordEntry.from_dict(data)

        assert entry.name == "TestSite"
        assert entry.username == "testuser"
        assert entry.password == "testpass123"
        assert entry.notes is None
        assert entry.id is not None
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_unique_id_generation(self):
        """Test that each entry gets a unique ID."""
        entry1 = PasswordEntry(name="Site1", username="user1", password="pass1")
        entry2 = PasswordEntry(name="Site2", username="user2", password="pass2")

        assert entry1.id != entry2.id

    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        entry = PasswordEntry(name="Test", username="user", password="pass")

        # Should be able to parse the timestamp
        datetime.fromisoformat(entry.created_at)
        datetime.fromisoformat(entry.updated_at)

    def test_roundtrip_dict_conversion(self):
        """Test that to_dict and from_dict are inverses."""
        original = PasswordEntry(
            name="TestSite",
            username="testuser",
            password="testpass123",
            notes="Test notes",
            id="test-id",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-02T00:00:00"
        )

        data = original.to_dict()
        restored = PasswordEntry.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.username == original.username
        assert restored.password == original.password
        assert restored.notes == original.notes
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at
