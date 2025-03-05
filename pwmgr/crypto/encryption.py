"""
Encryption service for the password manager.
Provides secure encryption and decryption of password data.
"""
import os
import base64
from typing import Tuple, Optional

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class EncryptionService:
    """Handles encryption and decryption of sensitive data using AES-256."""

    # Number of iterations for PBKDF2
    ITERATIONS = 100000
    # Salt length in bytes
    SALT_LENGTH = 16
    # Key length in bytes for AES-256
    KEY_LENGTH = 32
    # IV length in bytes
    IV_LENGTH = 16

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
    def encrypt(data: str, key: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-CBC.

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
    def decrypt(iv: bytes, ciphertext: bytes, key: bytes) -> str:
        """
        Decrypt data using AES-256-CBC.

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
    def encrypt_password_data(data: str, master_password: str) -> str:
        """
        Encrypt password data with the master password.

        Args:
            data: The password data to encrypt
            master_password: The user's master password

        Returns:
            Encoded string with salt, iv, and ciphertext
        """
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key(master_password, salt)
        iv, ciphertext = EncryptionService.encrypt(data, key)

        # Combine salt, iv, and ciphertext for storage
        combined = salt + iv + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def decrypt_password_data(encrypted_data: str, master_password: str) -> Optional[str]:
        """
        Decrypt password data with the master password.

        Args:
            encrypted_data: The encrypted password data
            master_password: The user's master password

        Returns:
            The decrypted password data or None if decryption fails
        """
        try:
            # Decode the combined data
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))

            # Extract salt, iv, and ciphertext
            salt = decoded[:EncryptionService.SALT_LENGTH]
            iv = decoded[EncryptionService.SALT_LENGTH:EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH]
            ciphertext = decoded[EncryptionService.SALT_LENGTH + EncryptionService.IV_LENGTH:]

            # Derive the key and decrypt
            key = EncryptionService.derive_key(master_password, salt)
            return EncryptionService.decrypt(iv, ciphertext, key)
        except Exception:
            # Return None if decryption fails (e.g., wrong password)
            return None