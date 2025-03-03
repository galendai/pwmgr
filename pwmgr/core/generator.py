"""
Password generator module.
"""
import random
import string
from typing import List


class PasswordGenerator:
    """
    Generates secure random passwords.
    """
    
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    
    @classmethod
    def generate(cls, 
                 length: int = 16, 
                 include_lowercase: bool = True,
                 include_uppercase: bool = True,
                 include_digits: bool = True,
                 include_symbols: bool = True) -> str:
        """
        Generate a random password.
        
        Args:
            length: Length of the password (default: 16)
            include_lowercase: Whether to include lowercase letters (default: True)
            include_uppercase: Whether to include uppercase letters (default: True)
            include_digits: Whether to include digits (default: True)
            include_symbols: Whether to include symbols (default: True)
            
        Returns:
            A random password
        """
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
            password_chars.append(random.choice(cls.LOWERCASE))
        if include_uppercase:
            password_chars.append(random.choice(cls.UPPERCASE))
        if include_digits:
            password_chars.append(random.choice(cls.DIGITS))
        if include_symbols:
            password_chars.append(random.choice(cls.SYMBOLS))
        
        # Fill the rest of the password with random characters
        remaining_length = length - len(password_chars)
        password_chars.extend(random.choices(char_pool, k=remaining_length))
        
        # Shuffle to ensure random distribution
        random.shuffle(password_chars)
        
        return ''.join(password_chars) 