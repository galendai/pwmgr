"""
Tests for EncryptionService.
"""
import pytest
import base64
import struct

from pwmgr.crypto.encryption import EncryptionService, EncryptionVersion


class TestEncryptionService:
    """Test cases for EncryptionService."""

    def test_generate_salt(self):
        """Test salt generation."""
        salt1 = EncryptionService.generate_salt()
        salt2 = EncryptionService.generate_salt()

        assert len(salt1) == EncryptionService.SALT_LENGTH
        assert len(salt2) == EncryptionService.SALT_LENGTH
        assert salt1 != salt2  # Salts should be unique

    def test_derive_key(self):
        """Test key derivation."""
        password = "test_password"
        salt = EncryptionService.generate_salt()

        key = EncryptionService.derive_key(password, salt)

        assert len(key) == EncryptionService.KEY_LENGTH
        # Same password and salt should produce same key
        key2 = EncryptionService.derive_key(password, salt)
        assert key == key2

    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        salt = EncryptionService.generate_salt()

        key1 = EncryptionService.derive_key("password1", salt)
        key2 = EncryptionService.derive_key("password2", salt)

        assert key1 != key2

    def test_encrypt_decrypt_gcm(self):
        """Test GCM encryption and decryption."""
        data = "sensitive data"
        key = EncryptionService.generate_salt()  # Use random bytes as key

        nonce, ciphertext, tag = EncryptionService._encrypt_gcm(data, key)
        decrypted = EncryptionService._decrypt_gcm(nonce, ciphertext, tag, key)

        assert decrypted == data
        assert len(nonce) == 12  # GCM recommended nonce size
        assert len(tag) == 16  # GCM tag size

    def test_encrypt_decrypt_gcm_tampered_tag(self):
        """Test that GCM decryption fails with tampered tag."""
        data = "sensitive data"
        key = EncryptionService.generate_salt()

        nonce, ciphertext, tag = EncryptionService._encrypt_gcm(data, key)

        # Tamper with the tag
        tampered_tag = tag[:-1] + bytes([tag[-1] ^ 0xFF])

        with pytest.raises(Exception):  # Should raise InvalidTag or similar
            EncryptionService._decrypt_gcm(nonce, ciphertext, tampered_tag, key)

    def test_encrypt_decrypt_password_data_gcm(self):
        """Test full encryption/decryption cycle with GCM."""
        data = '{"entries": [{"name": "test", "password": "secret"}]}'
        password = "master_password"

        encrypted = EncryptionService.encrypt_password_data(data, password)
        decrypted = EncryptionService.decrypt_password_data(encrypted, password)

        assert decrypted == data

    def test_encrypted_data_format(self):
        """Test that encrypted data includes version byte."""
        data = "test data"
        password = "password"

        encrypted = EncryptionService.encrypt_password_data(data, password)
        decoded = base64.b64decode(encrypted)

        # First byte should be the version
        version = struct.unpack('B', decoded[:1])[0]
        assert version == EncryptionVersion.GCM

    def test_decrypt_with_wrong_password(self):
        """Test that decryption fails with wrong password."""
        data = "sensitive data"
        correct_password = "correct_password"
        wrong_password = "wrong_password"

        encrypted = EncryptionService.encrypt_password_data(data, correct_password)
        decrypted = EncryptionService.decrypt_password_data(encrypted, wrong_password)

        assert decrypted is None

    def test_decrypt_invalid_data(self):
        """Test that decryption handles invalid data gracefully."""
        invalid_data = base64.b64encode(b"not valid encrypted data").decode()
        password = "password"

        decrypted = EncryptionService.decrypt_password_data(invalid_data, password)

        assert decrypted is None

    def test_encrypt_produces_different_ciphertext(self):
        """Test that encrypting the same data produces different ciphertext."""
        data = "same data"
        password = "password"

        encrypted1 = EncryptionService.encrypt_password_data(data, password)
        encrypted2 = EncryptionService.encrypt_password_data(data, password)

        # Due to random salt and nonce, ciphertexts should differ
        assert encrypted1 != encrypted2

        # But both should decrypt to the same data
        assert EncryptionService.decrypt_password_data(encrypted1, password) == data
        assert EncryptionService.decrypt_password_data(encrypted2, password) == data

    def test_migrate_to_gcm(self):
        """Test migration from CBC to GCM format."""
        data = "test data for migration"
        password = "password"

        # Create a legacy CBC encrypted blob
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key(password, salt)
        iv, ciphertext = EncryptionService._encrypt_cbc(data, key)

        # Format as legacy CBC: version(1) + salt(16) + iv(16) + ciphertext
        version_byte = struct.pack('B', EncryptionVersion.CBC)
        legacy_combined = version_byte + salt + iv + ciphertext
        legacy_encrypted = base64.b64encode(legacy_combined).decode()

        # Migrate to GCM
        migrated = EncryptionService.migrate_to_gcm(legacy_encrypted, password)

        assert migrated is not None

        # Verify the migrated data can be decrypted
        decrypted = EncryptionService.decrypt_password_data(migrated, password)
        assert decrypted == data

        # Verify the migrated data is in GCM format
        decoded = base64.b64decode(migrated)
        version = struct.unpack('B', decoded[:1])[0]
        assert version == EncryptionVersion.GCM

    def test_legacy_cbc_decryption(self):
        """Test backward compatibility with legacy CBC format."""
        data = "legacy test data"
        password = "password"

        # Create legacy CBC encrypted data
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key(password, salt)
        iv, ciphertext = EncryptionService._encrypt_cbc(data, key)

        # Format: version(1) + salt(16) + iv(16) + ciphertext
        version_byte = struct.pack('B', EncryptionVersion.CBC)
        legacy_combined = version_byte + salt + iv + ciphertext
        legacy_encrypted = base64.b64encode(legacy_combined).decode()

        # Should decrypt successfully
        decrypted = EncryptionService.decrypt_password_data(legacy_encrypted, password)
        assert decrypted == data 