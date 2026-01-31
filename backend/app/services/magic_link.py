"""Magic link authentication service using Redis for code storage."""

import json
import secrets
from datetime import UTC, datetime
from typing import TypedDict

import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class RegistrationData(TypedDict):
    """Type for pending registration data stored in Redis."""

    email: str
    first_name: str
    last_name: str
    user_type: str
    code: str
    created_at: str


class MagicLinkService:
    """Service for generating and verifying magic link authentication codes.

    Stores codes in Redis with automatic expiry. Codes are 6-digit numeric
    for easy entry on mobile devices.

    Attributes:
        CODE_LENGTH: Length of generated codes (6 digits).
        DEFAULT_EXPIRY_MINUTES: Default code expiry time (15 minutes).
        REDIS_KEY_PREFIX: Prefix for Redis keys storing magic link codes.
    """

    CODE_LENGTH = 6
    DEFAULT_EXPIRY_MINUTES = 15
    REDIS_KEY_PREFIX = "magic_link:"
    REGISTRATION_KEY_PREFIX = "registration_magic_link:"

    def __init__(self, redis_client=None) -> None:
        """Initialize the magic link service.

        Args:
            redis_client: Optional Redis client. If not provided, will be
                created lazily from settings.
        """
        self._redis = redis_client
        self._settings = get_settings()

    async def _get_redis(self):
        """Get or create the Redis client.

        Returns:
            Redis client instance.
        """
        if self._redis is None:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _generate_code(self) -> str:
        """Generate a cryptographically secure 6-digit code.

        Uses secrets.randbelow for cryptographic randomness rather than
        random.randint which is not suitable for security purposes.

        Returns:
            A 6-digit string code (e.g., "123456").
        """
        # Generate a number between 0 and 999999, then zero-pad to 6 digits
        code = secrets.randbelow(10**self.CODE_LENGTH)
        return str(code).zfill(self.CODE_LENGTH)

    def _get_redis_key(self, email: str) -> str:
        """Get the Redis key for storing a magic link code.

        Args:
            email: The user's email address.

        Returns:
            The Redis key string.
        """
        # Normalize email to lowercase for consistent key generation
        return f"{self.REDIS_KEY_PREFIX}{email.lower()}"

    async def create_code(
        self,
        email: str,
        expiry_minutes: int | None = None,
    ) -> str:
        """Create a new magic link code for the given email.

        Overwrites any existing code for the same email. The code is stored
        in Redis with automatic expiry.

        Args:
            email: The user's email address.
            expiry_minutes: Optional custom expiry time. Defaults to 15 minutes.

        Returns:
            The generated 6-digit code.
        """
        redis = await self._get_redis()
        code = self._generate_code()
        expiry = expiry_minutes or self.DEFAULT_EXPIRY_MINUTES

        key = self._get_redis_key(email)

        # Store code with expiry - format: code:timestamp
        timestamp = datetime.now(UTC).isoformat()
        value = f"{code}:{timestamp}"

        await redis.setex(key, expiry * 60, value)

        logger.info(
            "magic_link_code_created",
            email=email,
            expiry_minutes=expiry,
        )

        return code

    async def verify_code(self, email: str, code: str) -> bool:
        """Verify a magic link code for the given email.

        If verification is successful, the code is deleted from Redis
        to prevent reuse.

        Args:
            email: The user's email address.
            code: The code to verify.

        Returns:
            True if the code is valid, False otherwise.
        """
        redis = await self._get_redis()
        key = self._get_redis_key(email)

        stored_value = await redis.get(key)

        if stored_value is None:
            logger.warning(
                "magic_link_code_not_found",
                email=email,
            )
            return False

        # Extract code from stored value (format: code:timestamp)
        stored_code = stored_value.split(":")[0]

        if stored_code != code:
            logger.warning(
                "magic_link_code_mismatch",
                email=email,
            )
            return False

        # Code is valid - delete it to prevent reuse
        await redis.delete(key)

        logger.info(
            "magic_link_code_verified",
            email=email,
        )

        return True

    async def invalidate_code(self, email: str) -> bool:
        """Invalidate any existing code for the given email.

        Args:
            email: The user's email address.

        Returns:
            True if a code was deleted, False if no code existed.
        """
        redis = await self._get_redis()
        key = self._get_redis_key(email)

        deleted = await redis.delete(key)

        if deleted:
            logger.info(
                "magic_link_code_invalidated",
                email=email,
            )

        return deleted > 0

    async def get_remaining_ttl(self, email: str) -> int | None:
        """Get the remaining time-to-live for a code in seconds.

        Args:
            email: The user's email address.

        Returns:
            Remaining TTL in seconds, or None if no code exists.
        """
        redis = await self._get_redis()
        key = self._get_redis_key(email)

        ttl = await redis.ttl(key)

        # Redis returns -2 if key doesn't exist, -1 if no expiry
        return ttl if ttl > 0 else None

    def _get_registration_redis_key(self, email: str) -> str:
        """Get the Redis key for storing registration data.

        Args:
            email: The user's email address.

        Returns:
            The Redis key string.
        """
        return f"{self.REGISTRATION_KEY_PREFIX}{email.lower()}"

    async def create_registration_code(
        self,
        email: str,
        first_name: str,
        last_name: str,
        user_type: str,
        expiry_minutes: int | None = None,
    ) -> str:
        """Create a new registration code and store pending registration data.

        Stores the registration details in Redis along with the code.
        The data is stored as JSON with automatic expiry.

        Args:
            email: The user's email address.
            first_name: User's first name.
            last_name: User's last name.
            user_type: Type of user account (client/host).
            expiry_minutes: Optional custom expiry time. Defaults to 15 minutes.

        Returns:
            The generated 6-digit code.
        """
        redis = await self._get_redis()
        code = self._generate_code()
        expiry = expiry_minutes or self.DEFAULT_EXPIRY_MINUTES

        key = self._get_registration_redis_key(email)

        # Store registration data as JSON
        data: RegistrationData = {
            "email": email.lower(),
            "first_name": first_name,
            "last_name": last_name,
            "user_type": user_type,
            "code": code,
            "created_at": datetime.now(UTC).isoformat(),
        }

        await redis.setex(key, expiry * 60, json.dumps(data))

        logger.info(
            "registration_code_created",
            email=email,
            expiry_minutes=expiry,
        )

        return code

    async def verify_registration_code(
        self,
        email: str,
        code: str,
    ) -> RegistrationData | None:
        """Verify a registration code and return the stored registration data.

        If verification is successful, the data is deleted from Redis
        to prevent reuse.

        Args:
            email: The user's email address.
            code: The code to verify.

        Returns:
            The registration data if valid, None otherwise.
        """
        redis = await self._get_redis()
        key = self._get_registration_redis_key(email)

        stored_value = await redis.get(key)

        if stored_value is None:
            logger.warning(
                "registration_code_not_found",
                email=email,
            )
            return None

        try:
            data: RegistrationData = json.loads(stored_value)
        except json.JSONDecodeError:
            logger.error(
                "registration_data_corrupted",
                email=email,
            )
            return None

        if data["code"] != code:
            logger.warning(
                "registration_code_mismatch",
                email=email,
            )
            return None

        # Code is valid - delete it to prevent reuse
        await redis.delete(key)

        logger.info(
            "registration_code_verified",
            email=email,
        )

        return data


# Singleton instance for convenience
magic_link_service = MagicLinkService()
