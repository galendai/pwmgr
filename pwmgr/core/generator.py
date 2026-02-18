"""
Password generator module.
"""
import secrets
import string
from typing import List, Tuple


class PasswordStrength:
    """Password strength levels."""
    VERY_WEAK = 1
    WEAK = 2
    MEDIUM = 3
    STRONG = 4
    VERY_STRONG = 5


class PasswordGenerator:
    """
    Generates secure random passwords using cryptographically secure random.
    """

    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"

    # Minimum recommended password length
    MIN_LENGTH = 8
    RECOMMENDED_LENGTH = 16

    @classmethod
    def generate(cls,
                 length: int = 16,
                 include_lowercase: bool = True,
                 include_uppercase: bool = True,
                 include_digits: bool = True,
                 include_symbols: bool = True) -> str:
        """
        Generate a secure random password using cryptographically secure random.

        Args:
            length: Length of the password (default: 16)
            include_lowercase: Whether to include lowercase letters (default: True)
            include_uppercase: Whether to include uppercase letters (default: True)
            include_digits: Whether to include digits (default: True)
            include_symbols: Whether to include symbols (default: True)

        Returns:
            A secure random password

        Raises:
            ValueError: If length is less than minimum required
        """
        # Validate minimum length
        min_required = sum([include_lowercase, include_uppercase, include_digits, include_symbols])
        if length < min_required:
            raise ValueError(f"Password length must be at least {min_required} to include all selected character types")

        # Ensure at least one character set is included
        if not any([include_lowercase, include_uppercase, include_digits, include_symbols]):
            include_lowercase = True

        # Create character pool
        char_pool = ""
        if include_lowercase:
            char_pool += cls.LOWERCASE
        if include_uppercase:
            char_pool += cls.UPPERCASE
        if include_digits:
            char_pool += cls.DIGITS
        if include_symbols:
            char_pool += cls.SYMBOLS

        # Generate password
        # First, ensure at least one character from each selected set is included
        password_chars: List[str] = []

        if include_lowercase:
            password_chars.append(secrets.choice(cls.LOWERCASE))
        if include_uppercase:
            password_chars.append(secrets.choice(cls.UPPERCASE))
        if include_digits:
            password_chars.append(secrets.choice(cls.DIGITS))
        if include_symbols:
            password_chars.append(secrets.choice(cls.SYMBOLS))

        # Fill the rest of the password with secure random characters
        remaining_length = length - len(password_chars)
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(char_pool))

        # Shuffle using cryptographically secure random
        cls._secure_shuffle(password_chars)

        return ''.join(password_chars)

    @staticmethod
    def _secure_shuffle(items: List) -> None:
        """
        Shuffle a list using cryptographically secure random (Fisher-Yates shuffle).

        Args:
            items: List to shuffle in place
        """
        for i in range(len(items) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]

    @classmethod
    def check_password_strength(cls, password: str) -> Tuple[int, str, List[str]]:
        """
        Check the strength of a password.

        Args:
            password: The password to check

        Returns:
            A tuple of (strength_level, strength_label, suggestions)
        """
        suggestions = []
        score = 0

        # Length check
        if len(password) >= 16:
            score += 2
        elif len(password) >= 12:
            score += 1
        elif len(password) < 8:
            suggestions.append("Use at least 8 characters")

        # Character variety checks
        has_lower = any(c in cls.LOWERCASE for c in password)
        has_upper = any(c in cls.UPPERCASE for c in password)
        has_digit = any(c in cls.DIGITS for c in password)
        has_symbol = any(c in cls.SYMBOLS for c in password)

        variety_count = sum([has_lower, has_upper, has_digit, has_symbol])

        if variety_count >= 4:
            score += 2
        elif variety_count >= 3:
            score += 1

        if not has_lower:
            suggestions.append("Add lowercase letters")
        if not has_upper:
            suggestions.append("Add uppercase letters")
        if not has_digit:
            suggestions.append("Add numbers")
        if not has_symbol:
            suggestions.append("Add special characters")

        # Common pattern checks
        common_patterns = ['123', 'abc', 'qwe', 'password', 'admin']
        if any(pattern in password.lower() for pattern in common_patterns):
            score -= 1
            suggestions.append("Avoid common patterns or words")

        # Repeated character check
        if len(password) > 2 and any(password[i] == password[i-1] == password[i-2] for i in range(2, len(password))):
            score -= 1
            suggestions.append("Avoid repeated characters")

        # Calculate final strength
        score = max(1, min(5, score))

        strength_labels = {
            1: "Very Weak",
            2: "Weak",
            3: "Medium",
            4: "Strong",
            5: "Very Strong"
        }

        return score, strength_labels[score], suggestions 