"""Unit tests for password hashing service."""

import pytest

from app.services.password import PasswordService, password_service


class TestPasswordService:
    """Tests for PasswordService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = PasswordService()

    def test_hash_password_produces_valid_format(self) -> None:
        """Test that hash_password produces valid Argon2id format."""
        password = "secure_password_123"
        hashed = self.service.hash_password(password)

        # Argon2id hashes start with $argon2id$
        assert hashed.startswith("$argon2id$")

        # Hash should contain version, parameters, salt, and hash
        parts = hashed.split("$")
        assert len(parts) >= 5
        assert parts[1] == "argon2id"

    def test_hash_password_produces_different_hashes_for_same_password(self) -> None:
        """Test that same password produces different hashes (due to random salt)."""
        password = "secure_password_123"
        hash1 = self.service.hash_password(password)
        hash2 = self.service.hash_password(password)

        # Different random salts should produce different hashes
        assert hash1 != hash2

    def test_verify_password_succeeds_with_correct_password(self) -> None:
        """Test that verification succeeds with correct password."""
        password = "my_secure_password"
        hashed = self.service.hash_password(password)

        assert self.service.verify_password(password, hashed) is True

    def test_verify_password_fails_with_incorrect_password(self) -> None:
        """Test that verification fails with incorrect password."""
        password = "my_secure_password"
        wrong_password = "wrong_password_123"
        hashed = self.service.hash_password(password)

        assert self.service.verify_password(wrong_password, hashed) is False

    def test_verify_password_fails_with_invalid_hash(self) -> None:
        """Test that verification fails gracefully with invalid hash format."""
        password = "my_secure_password"
        invalid_hash = "not_a_valid_hash"

        assert self.service.verify_password(password, invalid_hash) is False

    def test_verify_password_fails_with_empty_hash(self) -> None:
        """Test that verification fails gracefully with empty hash."""
        password = "my_secure_password"

        assert self.service.verify_password(password, "") is False

    def test_hash_password_enforces_minimum_length(self) -> None:
        """Test that password must be at least 8 characters."""
        short_password = "short"

        with pytest.raises(ValueError) as exc_info:
            self.service.hash_password(short_password)

        assert "at least 8 characters" in str(exc_info.value)

    def test_hash_password_accepts_exactly_8_characters(self) -> None:
        """Test that exactly 8 character password is accepted."""
        password = "12345678"
        hashed = self.service.hash_password(password)

        assert hashed.startswith("$argon2id$")
        assert self.service.verify_password(password, hashed)

    def test_hash_password_rejects_7_characters(self) -> None:
        """Test that 7 character password is rejected."""
        password = "1234567"

        with pytest.raises(ValueError):
            self.service.hash_password(password)

    def test_validate_password_strength_raises_for_short_password(self) -> None:
        """Test validate_password_strength raises for short passwords."""
        with pytest.raises(ValueError) as exc_info:
            self.service.validate_password_strength("short")

        assert "at least 8 characters" in str(exc_info.value)

    def test_validate_password_strength_accepts_valid_password(self) -> None:
        """Test validate_password_strength accepts valid passwords."""
        # Should not raise
        self.service.validate_password_strength("valid_password_123")

    def test_hash_password_handles_special_characters(self) -> None:
        """Test that passwords with special characters work correctly."""
        password = "p@ssw0rd!#$%^&*()_+{}|:<>?"
        hashed = self.service.hash_password(password)

        assert self.service.verify_password(password, hashed)

    def test_hash_password_handles_unicode(self) -> None:
        """Test that passwords with unicode characters work correctly."""
        password = "secure_пароль_密码_🔐"
        hashed = self.service.hash_password(password)

        assert self.service.verify_password(password, hashed)

    def test_hash_password_handles_long_password(self) -> None:
        """Test that very long passwords work correctly."""
        password = "a" * 1000
        hashed = self.service.hash_password(password)

        assert self.service.verify_password(password, hashed)

    def test_needs_rehash_returns_false_for_fresh_hash(self) -> None:
        """Test that fresh hash doesn't need rehashing."""
        password = "secure_password"
        hashed = self.service.hash_password(password)

        assert self.service.needs_rehash(hashed) is False

    def test_singleton_instance_exists(self) -> None:
        """Test that singleton password_service instance exists."""
        assert password_service is not None
        assert isinstance(password_service, PasswordService)

    def test_singleton_instance_works(self) -> None:
        """Test that singleton instance works correctly."""
        password = "test_password_123"
        hashed = password_service.hash_password(password)

        assert password_service.verify_password(password, hashed)

    def test_timing_attack_resistance(self) -> None:
        """Test that verification doesn't leak timing information.

        Note: This is more of a documentation test - the actual timing
        resistance is provided by argon2-cffi's internal implementation.
        """
        password = "correct_password"
        hashed = self.service.hash_password(password)

        # Both correct and incorrect verifications should complete
        # (actual timing tests would require statistical analysis)
        result_correct = self.service.verify_password(password, hashed)
        result_wrong = self.service.verify_password("wrong_password", hashed)

        assert result_correct is True
        assert result_wrong is False

    def test_min_password_length_constant(self) -> None:
        """Test that MIN_PASSWORD_LENGTH is set correctly."""
        assert self.service.MIN_PASSWORD_LENGTH == 8
        assert PasswordService.MIN_PASSWORD_LENGTH == 8
