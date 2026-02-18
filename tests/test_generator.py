"""
Tests for PasswordGenerator.
"""
import pytest
import string

from pwmgr.core.generator import PasswordGenerator, PasswordStrength


class TestPasswordGenerator:
    """Test cases for PasswordGenerator."""

    def test_generate_default_password(self):
        """Test generating a password with default settings."""
        password = PasswordGenerator.generate()

        assert len(password) == 16
        assert any(c in string.ascii_lowercase for c in password)
        assert any(c in string.ascii_uppercase for c in password)
        assert any(c in string.digits for c in password)
        assert any(c in PasswordGenerator.SYMBOLS for c in password)

    def test_generate_custom_length(self):
        """Test generating a password with custom length."""
        password = PasswordGenerator.generate(length=24)

        assert len(password) == 24

    def test_generate_lowercase_only(self):
        """Test generating a password with only lowercase letters."""
        password = PasswordGenerator.generate(
            length=16,
            include_lowercase=True,
            include_uppercase=False,
            include_digits=False,
            include_symbols=False
        )

        assert len(password) == 16
        assert all(c in string.ascii_lowercase for c in password)

    def test_generate_uppercase_only(self):
        """Test generating a password with only uppercase letters."""
        password = PasswordGenerator.generate(
            length=16,
            include_lowercase=False,
            include_uppercase=True,
            include_digits=False,
            include_symbols=False
        )

        assert len(password) == 16
        assert all(c in string.ascii_uppercase for c in password)

    def test_generate_digits_only(self):
        """Test generating a password with only digits."""
        password = PasswordGenerator.generate(
            length=16,
            include_lowercase=False,
            include_uppercase=False,
            include_digits=True,
            include_symbols=False
        )

        assert len(password) == 16
        assert all(c in string.digits for c in password)

    def test_generate_symbols_only(self):
        """Test generating a password with only symbols."""
        password = PasswordGenerator.generate(
            length=16,
            include_lowercase=False,
            include_uppercase=False,
            include_digits=False,
            include_symbols=True
        )

        assert len(password) == 16
        assert all(c in PasswordGenerator.SYMBOLS for c in password)

    def test_generate_minimum_length(self):
        """Test generating password with minimum length for selected character types."""
        # With all 4 character types, minimum is 4
        password = PasswordGenerator.generate(length=4)

        assert len(password) == 4

    def test_generate_length_too_small(self):
        """Test that too small length raises an error."""
        with pytest.raises(ValueError):
            PasswordGenerator.generate(length=2)  # Need at least 4 for all character types

    def test_generate_default_to_lowercase(self):
        """Test that with no character types, defaults to lowercase."""
        password = PasswordGenerator.generate(
            length=16,
            include_lowercase=False,
            include_uppercase=False,
            include_digits=False,
            include_symbols=False
        )

        assert len(password) == 16
        assert all(c in string.ascii_lowercase for c in password)

    def test_generate_unique_passwords(self):
        """Test that multiple generated passwords are unique."""
        passwords = [PasswordGenerator.generate() for _ in range(100)]

        # All passwords should be unique (extremely high probability with secure random)
        assert len(set(passwords)) == 100

    def test_secure_shuffle(self):
        """Test that secure shuffle works."""
        items = list(range(20))
        original = items.copy()

        PasswordGenerator._secure_shuffle(items)

        # Items should contain same elements
        assert set(items) == set(original)
        # Items should be shuffled (extremely unlikely to remain the same)
        assert items != original

    def test_check_password_strength_very_strong(self):
        """Test password strength checking for very strong passwords."""
        # A good mix of character types without common patterns or repeated chars
        password = "MySecure!Pass2024XyZ"
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)

        assert strength >= PasswordStrength.STRONG
        assert "Strong" in label or "Very Strong" in label

    def test_check_password_strength_weak(self):
        """Test password strength checking for weak passwords."""
        password = "abc"  # Very short, one case
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)

        assert strength <= PasswordStrength.WEAK
        assert len(suggestions) > 0

    def test_check_password_strength_with_common_pattern(self):
        """Test that common patterns are detected."""
        password = "password123"
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)

        # Should detect the word "password"
        assert any("pattern" in s.lower() or "common" in s.lower() for s in suggestions)

    def test_check_password_strength_with_repeated_chars(self):
        """Test that repeated characters are detected."""
        password = "aaa111BBB"
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)

        # Should detect repeated characters
        assert any("repeat" in s.lower() for s in suggestions)

    def test_check_password_strength_suggestions(self):
        """Test that appropriate suggestions are given."""
        password = "abcdefgh"  # Only lowercase
        strength, label, suggestions = PasswordGenerator.check_password_strength(password)

        # Should suggest adding uppercase, digits, symbols
        suggestion_text = " ".join(suggestions).lower()
        assert "uppercase" in suggestion_text or "number" in suggestion_text or "special" in suggestion_text

    def test_check_password_strength_length_recommendation(self):
        """Test password length recommendations."""
        short_password = "Ab1!"
        strength, label, suggestions = PasswordGenerator.check_password_strength(short_password)

        # Should suggest longer password
        assert any("8" in s or "character" in s.lower() for s in suggestions)


class TestPasswordStrengthConstants:
    """Test password strength constants."""

    def test_strength_levels_defined(self):
        """Test that all strength levels are defined."""
        assert PasswordStrength.VERY_WEAK == 1
        assert PasswordStrength.WEAK == 2
        assert PasswordStrength.MEDIUM == 3
        assert PasswordStrength.STRONG == 4
        assert PasswordStrength.VERY_STRONG == 5