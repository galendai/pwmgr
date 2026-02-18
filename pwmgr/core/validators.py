"""
Input validation utilities for the password manager.
"""
import re
from typing import Tuple, Optional

from ..exceptions import ValidationError


class InputValidator:
    """Validates user input for password manager operations."""

    # Name validation rules
    NAME_MIN_LENGTH = 1
    NAME_MAX_LENGTH = 100
    NAME_PATTERN = re.compile(r'^[\w\s\-_\.]+$')  # Allow alphanumeric, spaces, hyphens, underscores, dots

    # Username validation rules
    USERNAME_MIN_LENGTH = 1
    USERNAME_MAX_LENGTH = 255
    USERNAME_PATTERN = re.compile(r'^[\w\.\-\+@]+$')  # Allow alphanumeric, dots, hyphens, plus, @

    # Password length rules
    PASSWORD_MIN_LENGTH = 1
    PASSWORD_MAX_LENGTH = 1000

    @classmethod
    def validate_name(cls, name: str) -> str:
        """
        Validate a password entry name.

        Args:
            name: The name to validate

        Returns:
            The validated and trimmed name

        Raises:
            ValidationError: If validation fails
        """
        if not name:
            raise ValidationError("Name cannot be empty", field="name")

        name = name.strip()

        if len(name) < cls.NAME_MIN_LENGTH:
            raise ValidationError(
                f"Name must be at least {cls.NAME_MIN_LENGTH} character(s)",
                field="name"
            )

        if len(name) > cls.NAME_MAX_LENGTH:
            raise ValidationError(
                f"Name cannot exceed {cls.NAME_MAX_LENGTH} characters",
                field="name"
            )

        if not cls.NAME_PATTERN.match(name):
            raise ValidationError(
                "Name can only contain letters, numbers, spaces, hyphens, underscores, and dots",
                field="name"
            )

        return name

    @classmethod
    def validate_username(cls, username: str) -> str:
        """
        Validate a username.

        Args:
            username: The username to validate

        Returns:
            The validated and trimmed username

        Raises:
            ValidationError: If validation fails
        """
        if not username:
            raise ValidationError("Username cannot be empty", field="username")

        username = username.strip()

        if len(username) < cls.USERNAME_MIN_LENGTH:
            raise ValidationError(
                f"Username must be at least {cls.USERNAME_MIN_LENGTH} character(s)",
                field="username"
            )

        if len(username) > cls.USERNAME_MAX_LENGTH:
            raise ValidationError(
                f"Username cannot exceed {cls.USERNAME_MAX_LENGTH} characters",
                field="username"
            )

        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username contains invalid characters",
                field="username"
            )

        return username

    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate a password.

        Args:
            password: The password to validate

        Returns:
            The validated password

        Raises:
            ValidationError: If validation fails
        """
        if password is None:
            raise ValidationError("Password cannot be None", field="password")

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            raise ValidationError(
                f"Password must be at least {cls.PASSWORD_MIN_LENGTH} character(s)",
                field="password"
            )

        if len(password) > cls.PASSWORD_MAX_LENGTH:
            raise ValidationError(
                f"Password cannot exceed {cls.PASSWORD_MAX_LENGTH} characters",
                field="password"
            )

        return password

    @classmethod
    def validate_url(cls, url: Optional[str]) -> Optional[str]:
        """
        Validate an optional URL.

        Args:
            url: The URL to validate (can be None)

        Returns:
            The validated URL or None

        Raises:
            ValidationError: If validation fails
        """
        if not url:
            return None

        url = url.strip()

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            raise ValidationError("Invalid URL format", field="url")

        return url

    @classmethod
    def validate_master_password(cls, password: str) -> str:
        """
        Validate a master password.

        Args:
            password: The master password to validate

        Returns:
            The validated master password

        Raises:
            ValidationError: If validation fails
        """
        if not password:
            raise ValidationError("Master password cannot be empty", field="master_password")

        if len(password) < 8:
            raise ValidationError(
                "Master password must be at least 8 characters long for security",
                field="master_password"
            )

        return password

    @classmethod
    def validate_password_length(cls, length: int) -> int:
        """
        Validate password generation length.

        Args:
            length: The length to validate

        Returns:
            The validated length

        Raises:
            ValidationError: If validation fails
        """
        if length < 4:
            raise ValidationError(
                "Password length must be at least 4 characters",
                field="length"
            )

        if length > 256:
            raise ValidationError(
                "Password length cannot exceed 256 characters",
                field="length"
            )

        return length

    @classmethod
    def validate_entry_input(cls, name: str, username: str, password: str) -> Tuple[str, str, str]:
        """
        Validate all inputs for creating/updating a password entry.

        Args:
            name: Entry name
            username: Username
            password: Password

        Returns:
            Tuple of (validated_name, validated_username, validated_password)

        Raises:
            ValidationError: If any validation fails
        """
        return (
            cls.validate_name(name),
            cls.validate_username(username),
            cls.validate_password(password)
        )
