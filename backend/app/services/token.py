"""JWT token service for authentication."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings


@dataclass
class TokenPayload:
    """Decoded JWT token payload."""

    sub: str  # Subject (user_id)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    jti: str  # JWT ID (unique identifier)
    token_type: str  # "access" or "refresh"


class TokenService:
    """JWT token creation and verification service.

    Creates and verifies JWT tokens for authentication.
    Access tokens are short-lived (15 minutes by default).
    Refresh tokens are long-lived (7 days by default).
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """Initialize token service.

        Args:
            secret_key: Secret key for signing tokens.
            algorithm: JWT signing algorithm (default: HS256).
            access_token_expire_minutes: Access token expiration in minutes.
            refresh_token_expire_days: Refresh token expiration in days.
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, user_id: uuid.UUID | str) -> str:
        """Create a short-lived access token.

        Args:
            user_id: The user ID to encode in the token.

        Returns:
            Encoded JWT access token string.
        """
        return self._create_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=self._access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: uuid.UUID | str) -> str:
        """Create a long-lived refresh token.

        Args:
            user_id: The user ID to encode in the token.

        Returns:
            Encoded JWT refresh token string.
        """
        return self._create_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=self._refresh_token_expire_days),
        )

    def _create_token(
        self,
        user_id: uuid.UUID | str,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        """Create a JWT token with the specified parameters.

        Args:
            user_id: The user ID to encode in the token.
            token_type: Type of token ("access" or "refresh").
            expires_delta: Token expiration time delta.

        Returns:
            Encoded JWT token string.
        """
        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "token_type": token_type,
        }

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify.

        Returns:
            Decoded TokenPayload.

        Raises:
            ValueError: If token is invalid or expired.
        """
        if not token:
            raise ValueError("Invalid token")

        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError as e:
            error_message = str(e).lower()
            if "expired" in error_message:
                raise ValueError("Token has expired") from e
            raise ValueError("Invalid token") from e

        # Parse datetime fields
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)

        return TokenPayload(
            sub=payload["sub"],
            exp=exp,
            iat=iat,
            jti=payload["jti"],
            token_type=payload.get("token_type", "access"),
        )


def _create_token_service() -> TokenService:
    """Create token service from application settings."""
    settings = get_settings()
    return TokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        refresh_token_expire_days=settings.jwt_refresh_token_expire_days,
    )


# Singleton instance for convenience
token_service = _create_token_service()
