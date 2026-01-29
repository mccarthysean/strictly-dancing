"""Storage service for file uploads using S3-compatible storage."""

import io
import logging
import uuid
from abc import ABC, abstractmethod

from PIL import Image

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
    ) -> str:
        """Upload a file and return its URL.

        Args:
            file_data: The file contents as bytes.
            key: The storage key/path for the file.
            content_type: MIME type of the file.

        Returns:
            The public URL of the uploaded file.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file by its key.

        Args:
            key: The storage key/path of the file.

        Returns:
            True if deleted, False if not found.
        """
        ...


class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend (AWS S3, Supabase Storage, MinIO)."""

    def __init__(self) -> None:
        """Initialize S3 client with settings."""
        try:
            import aioboto3
        except ImportError as exc:
            raise ImportError(
                "aioboto3 is required for S3 storage. "
                "Install with: pip install aioboto3"
            ) from exc

        self._session = aioboto3.Session()
        self._settings = get_settings()

    def _get_client_config(self) -> dict:
        """Get boto3 client configuration."""
        config = {
            "region_name": self._settings.s3_region,
        }

        # Add credentials if provided
        if self._settings.s3_access_key_id:
            config["aws_access_key_id"] = self._settings.s3_access_key_id
        if self._settings.s3_secret_access_key:
            config["aws_secret_access_key"] = self._settings.s3_secret_access_key

        # Add custom endpoint for Supabase/MinIO
        if self._settings.s3_endpoint_url:
            config["endpoint_url"] = self._settings.s3_endpoint_url

        return config

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
    ) -> str:
        """Upload a file to S3.

        Args:
            file_data: The file contents as bytes.
            key: The storage key/path for the file.
            content_type: MIME type of the file.

        Returns:
            The public URL of the uploaded file.
        """
        bucket = self._settings.s3_bucket_name
        config = self._get_client_config()

        async with self._session.client("s3", **config) as s3:
            await s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                CacheControl="max-age=31536000",  # 1 year cache
            )

        # Build public URL
        if self._settings.storage_base_url:
            return f"{self._settings.storage_base_url.rstrip('/')}/{key}"
        elif self._settings.s3_endpoint_url:
            return f"{self._settings.s3_endpoint_url.rstrip('/')}/{bucket}/{key}"
        else:
            return f"https://{bucket}.s3.{self._settings.s3_region}.amazonaws.com/{key}"

    async def delete(self, key: str) -> bool:
        """Delete a file from S3.

        Args:
            key: The storage key/path of the file.

        Returns:
            True if deleted, False if not found.
        """
        bucket = self._settings.s3_bucket_name
        config = self._get_client_config()

        try:
            async with self._session.client("s3", **config) as s3:
                await s3.delete_object(Bucket=bucket, Key=key)
                return True
        except Exception as e:
            logger.warning(f"Failed to delete {key} from S3: {e}")
            return False


class LocalStorageBackend(StorageBackend):
    """Local file storage backend for development."""

    def __init__(self, base_path: str = "/tmp/strictly-dancing-uploads") -> None:
        """Initialize local storage with base path.

        Args:
            base_path: Directory to store uploaded files.
        """
        import os

        self._base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._settings = get_settings()

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str,
    ) -> str:
        """Save a file locally.

        Args:
            file_data: The file contents as bytes.
            key: The storage key/path for the file.
            content_type: MIME type of the file (unused for local storage).

        Returns:
            The local file path as a URL.
        """
        import os

        file_path = os.path.join(self._base_path, key)
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file_data)

        # Return URL based on storage_base_url or local path
        if self._settings.storage_base_url:
            return f"{self._settings.storage_base_url.rstrip('/')}/{key}"
        return f"file://{file_path}"

    async def delete(self, key: str) -> bool:
        """Delete a local file.

        Args:
            key: The storage key/path of the file.

        Returns:
            True if deleted, False if not found.
        """
        import os

        file_path = os.path.join(self._base_path, key)
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False


class StorageService:
    """High-level storage service with image processing capabilities."""

    def __init__(self, backend: StorageBackend | None = None) -> None:
        """Initialize storage service with appropriate backend.

        Args:
            backend: Optional storage backend. If None, auto-selects based on settings.
        """
        self._settings = get_settings()

        if backend is not None:
            self._backend = backend
        elif self._settings.s3_bucket_name:
            self._backend = S3StorageBackend()
        else:
            self._backend = LocalStorageBackend()

    def validate_image(
        self,
        file_data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate an image file.

        Args:
            file_data: The image file contents.
            content_type: MIME type from upload.
            filename: Original filename (optional).

        Returns:
            Tuple of (is_valid, error_message).
        """
        settings = self._settings

        # Check file size
        if len(file_data) > settings.avatar_max_size_bytes:
            max_mb = settings.avatar_max_size_bytes / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_mb:.1f}MB"

        # Check content type
        if content_type not in settings.avatar_allowed_types:
            allowed = ", ".join(settings.avatar_allowed_types)
            return False, f"Invalid file type. Allowed types: {allowed}"

        # Verify it's actually an image by attempting to open it
        try:
            img = Image.open(io.BytesIO(file_data))
            img.verify()
        except Exception:
            return False, "Invalid image file"

        return True, None

    def resize_image(
        self,
        file_data: bytes,
        max_width: int,
        max_height: int,
        output_format: str = "WEBP",
        quality: int = 85,
    ) -> tuple[bytes, str]:
        """Resize an image while preserving aspect ratio.

        Args:
            file_data: Original image data.
            max_width: Maximum width in pixels.
            max_height: Maximum height in pixels.
            output_format: Output format (WEBP, JPEG, PNG).
            quality: Compression quality (1-100).

        Returns:
            Tuple of (resized_data, content_type).
        """
        img = Image.open(io.BytesIO(file_data))

        # Convert to RGB if necessary (for WEBP/JPEG output)
        if img.mode in ("RGBA", "P") and output_format in ("JPEG",):
            # Create white background for transparency
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Calculate new dimensions preserving aspect ratio
        orig_width, orig_height = img.size
        ratio = min(max_width / orig_width, max_height / orig_height)

        # Only resize if image is larger than target
        if ratio < 1:
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        save_kwargs = {"format": output_format, "quality": quality}

        # WEBP supports both RGB and RGBA
        if output_format == "WEBP":
            save_kwargs["method"] = 4  # Balance of speed/compression
        elif output_format == "JPEG":
            save_kwargs["optimize"] = True

        img.save(output, **save_kwargs)
        output.seek(0)

        content_types = {
            "WEBP": "image/webp",
            "JPEG": "image/jpeg",
            "PNG": "image/png",
        }

        return output.read(), content_types.get(output_format, "image/webp")

    def create_thumbnail(
        self,
        file_data: bytes,
        size: int,
        output_format: str = "WEBP",
        quality: int = 80,
    ) -> tuple[bytes, str]:
        """Create a square thumbnail from an image.

        Crops to center square then resizes.

        Args:
            file_data: Original image data.
            size: Thumbnail size (width and height).
            output_format: Output format (WEBP, JPEG, PNG).
            quality: Compression quality (1-100).

        Returns:
            Tuple of (thumbnail_data, content_type).
        """
        img = Image.open(io.BytesIO(file_data))

        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P") and output_format in ("JPEG",):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Crop to center square
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        img = img.crop((left, top, right, bottom))

        # Resize to target size
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        save_kwargs = {"format": output_format, "quality": quality}

        if output_format == "WEBP":
            save_kwargs["method"] = 4
        elif output_format == "JPEG":
            save_kwargs["optimize"] = True

        img.save(output, **save_kwargs)
        output.seek(0)

        content_types = {
            "WEBP": "image/webp",
            "JPEG": "image/jpeg",
            "PNG": "image/png",
        }

        return output.read(), content_types.get(output_format, "image/webp")

    async def upload_avatar(
        self,
        user_id: str,
        file_data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> dict[str, str]:
        """Process and upload a user avatar.

        Creates both a resized main image and a thumbnail.

        Args:
            user_id: The user's UUID.
            file_data: Original image data.
            content_type: Original MIME type.
            filename: Original filename (optional).

        Returns:
            Dict with 'avatar_url' and 'avatar_thumbnail_url'.

        Raises:
            ValueError: If validation fails.
        """
        settings = self._settings

        # Validate
        is_valid, error = self.validate_image(file_data, content_type, filename)
        if not is_valid:
            raise ValueError(error)

        # Generate unique key prefix
        unique_id = uuid.uuid4().hex[:12]
        key_prefix = f"avatars/{user_id}/{unique_id}"

        # Resize main image
        main_data, main_type = self.resize_image(
            file_data,
            settings.avatar_resize_width,
            settings.avatar_resize_height,
        )
        main_key = f"{key_prefix}/avatar.webp"

        # Create thumbnail
        thumb_data, thumb_type = self.create_thumbnail(
            file_data,
            settings.avatar_thumbnail_size,
        )
        thumb_key = f"{key_prefix}/thumb.webp"

        # Upload both
        avatar_url = await self._backend.upload(main_data, main_key, main_type)
        thumb_url = await self._backend.upload(thumb_data, thumb_key, thumb_type)

        logger.info(f"Uploaded avatar for user {user_id}: {avatar_url}")

        return {
            "avatar_url": avatar_url,
            "avatar_thumbnail_url": thumb_url,
        }

    async def delete_avatar(self, avatar_url: str) -> bool:
        """Delete an avatar and its thumbnail.

        Args:
            avatar_url: The avatar URL to delete.

        Returns:
            True if deleted successfully.
        """
        # Extract key from URL
        # URL format: .../avatars/{user_id}/{unique_id}/avatar.webp
        if "avatars/" not in avatar_url:
            return False

        # Get the base path (without filename)
        key_base = avatar_url.split("avatars/")[1]
        key_base = "avatars/" + key_base.rsplit("/", 1)[0]

        # Delete both files
        main_deleted = await self._backend.delete(f"{key_base}/avatar.webp")
        thumb_deleted = await self._backend.delete(f"{key_base}/thumb.webp")

        return main_deleted or thumb_deleted


def get_storage_service() -> StorageService:
    """Get a storage service instance.

    Factory function for dependency injection.

    Returns:
        StorageService instance with appropriate backend.
    """
    return StorageService()
