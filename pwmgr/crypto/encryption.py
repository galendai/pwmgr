"""
Encryption service for the password manager.
Provides secure encryption and decryption of password data using AES-256-GCM.
"""
import os
import base64
import struct
from typing import Tuple, Optional

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class EncryptionVersion:
    """Encryption version identifiers for backward compatibility."""
    CBC = 1  # Legacy AES-256-CBC (deprecated)
    GCM = 2  # AES-256-GCM (current)


class EncryptionService:
    """Handles encryption and decryption of sensitive data using AES-256-GCM."""

    # Number of iterations for PBKDF2
    ITERATIONS = 100000
    # Salt length in bytes
    SALT_LENGTH = 16
    # Key length in bytes for AES-256
    KEY_LENGTH = 32
    # IV/Nonce length in bytes
    IV_LENGTH = 16
    # GCM tag length in bytes
    GCM_TAG_LENGTH = 16
    # Current encryption version
    CURRENT_VERSION = EncryptionVersion.GCM

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt for key derivation."""
        return os.urandom(EncryptionService.SALT_LENGTH)

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """
        Derive an encryption key from the master password and salt.

        Args:
            master_password: The user's master password
            salt: Random salt for key derivation

        Returns:
            The derived key for encryption/decryption
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=EncryptionService.KEY_LENGTH,
            salt=salt,
            iterations=EncryptionService.ITERATIONS,
        )
        return kdf.derive(master_password.encode('utf-8'))

    @staticmethod
    def _encrypt_gcm(data: str, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            data: The plaintext data to encrypt
            key: The encryption key

        Returns:
            A tuple of (nonce, ciphertext, tag)
        """
        # Generate a random nonce (12 bytes is recommended for GCM)
        nonce = os.urandom(12)

        # Create the cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt the data (GCM doesn't need padding)
        ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()

        # Get the authentication tag
        tag = encryptor.tag

        return nonce, ciphertext, tag

    @staticmethod
    def _decrypt_gcm(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> str:
        """
        Decrypt data using AES-256-GCM.

        Args:
            nonce: The nonce used for encryption
            ciphertext: The encrypted data
            tag: The authentication tag
            key: The decryption key

        Returns:
            The decrypted plaintext

        Raises:
            ValueError: If authentication fails
        """
        # Create the cipher with the tag
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        data = decryptor.update(ciphertext) + decryptor.finalize()

        return data.decode('utf-8')

    @staticmethod
    def _encrypt_cbc(data: str, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-CBC (legacy method for backward compatibility).

        Args:
            data: The plaintext data to encrypt
            key: The encryption key

        Returns:
            A tuple of (iv, ciphertext)
        """
        # Generate a random IV
        iv = os.urandom(EncryptionService.IV_LENGTH)

        # Pad the data
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data.encode('utf-8')) + padder.finalize()

        # Create the cipher
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Encrypt the data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return iv, ciphertext

    @staticmethod
    def _decrypt_cbc(iv: bytes, ciphertext: bytes, key: bytes) -> str:
        """
        Decrypt data using AES-256-CBC (legacy method for backward compatibility).

        Args:
            iv: The initialization vector
            ciphertext: The encrypted data
            key: The decryption key

        Returns:
            The decrypted plaintext
        """
        # Create the cipher
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        # Decrypt the data
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad the data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data.decode('utf-8')

    @staticmethod
    def encrypt(data: str, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            data: The plaintext data to encrypt
            key: The encryption key

        Returns:
            A tuple of (nonce, ciphertext, tag)
        """
        return EncryptionService._encrypt_gcm(data, key)

    @staticmethod
    def decrypt(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> str:
        """
        Decrypt data using AES-256-GCM.

        Args:
            nonce: The nonce used for encryption
            ciphertext: The encrypted data
            tag: The authentication tag
            key: The decryption key

        Returns:
            The decrypted plaintext
        """
        return EncryptionService._decrypt_gcm(nonce, ciphertext, tag, key)

    @staticmethod
    def encrypt_password_data(data: str, master_password: str) -> str:
        """
        Encrypt password data with the master password using AES-256-GCM.

        Args:
            data: The password data to encrypt
            master_password: The user's master password

        Returns:
            Encoded string with version, salt, nonce, tag, and ciphertext
        """
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key(master_password, salt)
        nonce, ciphertext, tag = EncryptionService._encrypt_gcm(data, key)

        # Combine version (1 byte) + salt + nonce + tag + ciphertext for storage
        version_byte = struct.pack('B', EncryptionService.CURRENT_VERSION)
        combined = version_byte + salt + nonce + tag + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def decrypt_password_data(encrypted_data: str, master_password: str) -> Optional[str]:
        """
        Decrypt password data with the master password.
        Supports both GCM (v2) and legacy CBC (v1) formats for backward compatibility.

        Args:
            encrypted_data: The encrypted password data
            master_password: The user's master password

        Returns:
            The decrypted password data or None if decryption fails
        """
        try:
            # Decode the combined data
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))

            # Check if data has version prefix (new format)
            if len(decoded) < 1:
                return None

            version = struct.unpack('B', decoded[:1])[0]

            if version == EncryptionVersion.GCM:
                # GCM format: version(1) + salt(16) + nonce(12) + tag(16) + ciphertext
                salt = decoded[1:1 + EncryptionService.SALT_LENGTH]
                nonce = decoded[1 + EncryptionService.SALT_LENGTH:1 + EncryptionService.SALT_LENGTH + 12]
                tag = decoded[1 + EncryptionService.SALT_LENGTH + 12:1 + EncryptionService.SALT_LENGTH + 12 + EncryptionService.GCM_TAG_LENGTH]
                ciphertext = decoded[1 + EncryptionService.SALT_LENGTH + 12 + EncryptionService.GCM_TAG_LENGTH:]

                # Derive the key and decrypt
                key = EncryptionService.derive_key(master_password, salt)
                return EncryptionService._decrypt_gcm(nonce, ciphertext, tag, key)

            elif version == EncryptionVersion.CBC:
                # Legacy CBC format: version(1) + salt(16) + iv(16) + ciphertext
                salt = decoded[1:1 + EncryptionService.SALT_LENGTH]
                iv = decoded[1 + EncryptionService.SALT_LENGTH:1 + EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH]
                ciphertext = decoded[1 + EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH:]

                # Derive the key and decrypt
                key = EncryptionService.derive_key(master_password, salt)
                return EncryptionService._decrypt_cbc(iv, ciphertext, key)

            else:
                # Unknown version, try legacy format (without version prefix)
                # Old format: salt(16) + iv(16) + ciphertext
                salt = decoded[:EncryptionService.SALT_LENGTH]
                iv = decoded[EncryptionService.SALT_LENGTH:EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH]
                ciphertext = decoded[EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH:]

                # Derive the key and decrypt
                key = EncryptionService.derive_key(master_password, salt)
                return EncryptionService._decrypt_cbc(iv, ciphertext, key)

        except Exception:
            # Return None if decryption fails (e.g., wrong password)
            return None

    @staticmethod
    def migrate_to_gcm(encrypted_data: str, master_password: str) -> Optional[str]:
        """
        Migrate legacy CBC encrypted data to GCM format.

        Args:
            encrypted_data: The legacy encrypted password data
            master_password: The user's master password

        Returns:
            Re-encrypted data in GCM format, or None if migration fails
        """
        # Decrypt using the backward-compatible method
        decrypted = EncryptionService.decrypt_password_data(encrypted_data, master_password)
        if decrypted is None:
            return None

        # Re-encrypt with GCM
        return EncryptionService.encrypt_password_data(decrypted, master_password)