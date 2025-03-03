"""
Tests for the encryption service.
"""
import unittest
from pwmgr.crypto import EncryptionService


class TestEncryptionService(unittest.TestCase):
    """Test the encryption service."""
    
    def test_key_derivation(self):
        """Test that key derivation works and produces a key of the right length."""
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key("test_password", salt)
        
        self.assertEqual(len(key), EncryptionService.KEY_LENGTH)
        
        # Ensure same password + salt yields same key
        key2 = EncryptionService.derive_key("test_password", salt)
        self.assertEqual(key, key2)
        
        # Ensure different password yields different key
        key3 = EncryptionService.derive_key("different_password", salt)
        self.assertNotEqual(key, key3)
    
    def test_encryption_decryption(self):
        """Test encryption and decryption."""
        # Generate a key
        salt = EncryptionService.generate_salt()
        key = EncryptionService.derive_key("test_password", salt)
        
        # Test data
        plaintext = "This is a test message."
        
        # Encrypt
        iv, ciphertext = EncryptionService.encrypt(plaintext, key)
        
        # Ensure encryption produces different output
        self.assertNotEqual(plaintext.encode('utf-8'), ciphertext)
        
        # Decrypt
        decrypted = EncryptionService.decrypt(iv, ciphertext, key)
        
        # Ensure decryption works
        self.assertEqual(plaintext, decrypted)
    
    def test_password_data_encryption(self):
        """Test the encrypt_password_data and decrypt_password_data methods."""
        # Test data
        plaintext = '{"username": "test", "password": "secret"}'
        master_password = "master_password"
        
        # Encrypt
        encrypted = EncryptionService.encrypt_password_data(plaintext, master_password)
        
        # Ensure encryption produces different output
        self.assertNotEqual(plaintext, encrypted)
        
        # Decrypt
        decrypted = EncryptionService.decrypt_password_data(encrypted, master_password)
        
        # Ensure decryption works
        self.assertEqual(plaintext, decrypted)
        
        # Ensure wrong password fails
        failed_decrypt = EncryptionService.decrypt_password_data(encrypted, "wrong_password")
        self.assertIsNone(failed_decrypt)


if __name__ == "__main__":
    unittest.main() 