"""Password hashing service using Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


class PasswordService:
    """Secure password hashing service using Argon2id.

    Uses argon2-cffi with secure parameters following OWASP recommendations:
    - time_cost=3 (iterations)
    - memory_cost=65536 (64 MiB)
    - parallelism=4 (threads)
    """

    MIN_PASSWORD_LENGTH = 8

    def __init__(self) -> None:
        """Initialize password hasher with secure Argon2id parameters."""
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,  # 64 MiB
            parallelism=4,
            hash_len=32,
            salt_len=16,
        )

    def validate_password_strength(self, password: str) -> None:
        """Validate password meets minimum requirements.

        Args:
            password: The password to validate.

        Raises:
            ValueError: If password doesn't meet requirements.
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long"
            )

    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2id.

        Args:
            password: The plaintext password to hash.

        Returns:
            The Argon2id hash string.

        Raises:
            ValueError: If password doesn't meet minimum requirements.
        """
        self.validate_password_strength(password)
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash using time-constant comparison.

        The argon2-cffi library uses time-constant comparison internally
        to prevent timing attacks.

        Args:
            password: The plaintext password to verify.
            password_hash: The Argon2id hash to verify against.

        Returns:
            True if password matches, False otherwise.
        """
        try:
            self._hasher.verify(password_hash, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Check if a password hash needs to be rehashed.

        This can happen if the hash parameters have changed.

        Args:
            password_hash: The hash to check.

        Returns:
            True if the hash should be rehashed with current parameters.
        """
        return self._hasher.check_needs_rehash(password_hash)


# Singleton instance for convenience
password_service = PasswordService()
