"""
Tests for the password generator.
"""
import unittest
import string
from pwmgr.core import PasswordGenerator


class TestPasswordGenerator(unittest.TestCase):
    """Test the password generator."""

    def test_default_password_generation(self):
        """Test password generation with default settings."""
        password = PasswordGenerator.generate()

        # Check the length
        self.assertEqual(len(password), 16)

        # Check that it contains at least one of each character set
        self.assertTrue(any(c in string.ascii_lowercase for c in password))
        self.assertTrue(any(c in string.ascii_uppercase for c in password))
        self.assertTrue(any(c in string.digits for c in password))
        self.assertTrue(any(c in PasswordGenerator.SYMBOLS for c in password))

    def test_custom_length(self):
        """Test password generation with custom length."""
        password = PasswordGenerator.generate(length=24)
        self.assertEqual(len(password), 24)

    def test_character_sets(self):
        """Test password generation with specific character sets."""
        # Only lowercase
        password = PasswordGenerator.generate(
            include_lowercase=True,
            include_uppercase=False,
            include_digits=False,
            include_symbols=False
        )
        self.assertTrue(all(c in string.ascii_lowercase for c in password))

        # Only uppercase
        password = PasswordGenerator.generate(
            include_lowercase=False,
            include_uppercase=True,
            include_digits=False,
            include_symbols=False
        )
        self.assertTrue(all(c in string.ascii_uppercase for c in password))

        # Only digits
        password = PasswordGenerator.generate(
            include_lowercase=False,
            include_uppercase=False,
            include_digits=True,
            include_symbols=False
        )
        self.assertTrue(all(c in string.digits for c in password))

        # Only symbols
        password = PasswordGenerator.generate(
            include_lowercase=False,
            include_uppercase=False,
            include_digits=False,
            include_symbols=True
        )
        self.assertTrue(all(c in PasswordGenerator.SYMBOLS for c in password))

    def test_multiple_generations_are_different(self):
        """Test that multiple generations produce different passwords."""
        password1 = PasswordGenerator.generate()
        password2 = PasswordGenerator.generate()

        self.assertNotEqual(password1, password2)


if __name__ == "__main__":
    unittest.main()