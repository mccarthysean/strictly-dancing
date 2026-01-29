"""Unit tests for StorageService."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.services.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageBackend,
    StorageService,
    get_storage_service,
)


def create_test_image(
    width: int = 800,
    height: int = 600,
    format: str = "JPEG",
    mode: str = "RGB",
) -> bytes:
    """Create a test image in memory.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        format: Image format (JPEG, PNG, WEBP).
        mode: Color mode (RGB, RGBA, P).

    Returns:
        Image data as bytes.
    """
    img = Image.new(mode, (width, height), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.s3_bucket_name = ""
    settings.s3_region = "us-west-2"
    settings.s3_access_key_id = ""
    settings.s3_secret_access_key = ""
    settings.s3_endpoint_url = ""
    settings.storage_base_url = ""
    settings.avatar_max_size_bytes = 5 * 1024 * 1024
    settings.avatar_allowed_types = ["image/jpeg", "image/png", "image/webp"]
    settings.avatar_resize_width = 400
    settings.avatar_resize_height = 400
    settings.avatar_thumbnail_size = 100
    return settings


@pytest.fixture
def mock_backend():
    """Create a mock storage backend."""
    backend = AsyncMock(spec=StorageBackend)
    backend.upload.return_value = "https://example.com/test.jpg"
    backend.delete.return_value = True
    return backend


@pytest.fixture
def storage_service(mock_backend, mock_settings):
    """Create a StorageService with mock backend."""
    with patch("app.services.storage.get_settings", return_value=mock_settings):
        service = StorageService(backend=mock_backend)
    return service


class TestStorageServiceValidation:
    """Tests for image validation."""

    def test_validate_valid_jpeg(self, storage_service):
        """Test validation accepts valid JPEG."""
        image_data = create_test_image(format="JPEG")
        is_valid, error = storage_service.validate_image(
            image_data, "image/jpeg", "test.jpg"
        )
        assert is_valid is True
        assert error is None

    def test_validate_valid_png(self, storage_service):
        """Test validation accepts valid PNG."""
        image_data = create_test_image(format="PNG")
        is_valid, error = storage_service.validate_image(
            image_data, "image/png", "test.png"
        )
        assert is_valid is True
        assert error is None

    def test_validate_valid_webp(self, storage_service):
        """Test validation accepts valid WebP."""
        image_data = create_test_image(format="WEBP")
        is_valid, error = storage_service.validate_image(
            image_data, "image/webp", "test.webp"
        )
        assert is_valid is True
        assert error is None

    def test_validate_rejects_too_large(self, storage_service, mock_settings):
        """Test validation rejects files that are too large."""
        # Create image larger than max size
        mock_settings.avatar_max_size_bytes = 100  # Very small limit
        large_data = b"x" * 200

        is_valid, error = storage_service.validate_image(
            large_data, "image/jpeg", "test.jpg"
        )
        assert is_valid is False
        assert "too large" in error.lower()

    def test_validate_rejects_invalid_content_type(self, storage_service):
        """Test validation rejects invalid content types."""
        image_data = create_test_image(format="JPEG")
        is_valid, error = storage_service.validate_image(
            image_data, "image/gif", "test.gif"
        )
        assert is_valid is False
        assert "Invalid file type" in error

    def test_validate_rejects_corrupted_image(self, storage_service):
        """Test validation rejects corrupted/invalid image data."""
        corrupted_data = b"not an image"
        is_valid, error = storage_service.validate_image(
            corrupted_data, "image/jpeg", "test.jpg"
        )
        assert is_valid is False
        assert "Invalid image" in error


class TestStorageServiceResize:
    """Tests for image resizing."""

    def test_resize_large_image(self, storage_service):
        """Test resizing reduces large image dimensions."""
        large_image = create_test_image(width=1000, height=800)
        resized_data, content_type = storage_service.resize_image(
            large_image, max_width=400, max_height=400
        )

        # Verify output is valid image
        img = Image.open(io.BytesIO(resized_data))
        assert img.width <= 400
        assert img.height <= 400
        assert content_type == "image/webp"

    def test_resize_preserves_aspect_ratio(self, storage_service):
        """Test resizing preserves aspect ratio."""
        wide_image = create_test_image(width=1000, height=500)  # 2:1 ratio
        resized_data, _ = storage_service.resize_image(
            wide_image, max_width=400, max_height=400
        )

        img = Image.open(io.BytesIO(resized_data))
        # Should scale to 400x200 (2:1 ratio preserved)
        assert img.width == 400
        assert img.height == 200

    def test_resize_small_image_unchanged(self, storage_service):
        """Test small images are not upscaled."""
        small_image = create_test_image(width=200, height=150)
        resized_data, _ = storage_service.resize_image(
            small_image, max_width=400, max_height=400
        )

        img = Image.open(io.BytesIO(resized_data))
        assert img.width == 200
        assert img.height == 150

    def test_resize_rgba_to_webp(self, storage_service):
        """Test RGBA images convert correctly to WebP."""
        rgba_image = create_test_image(format="PNG", mode="RGBA")
        resized_data, content_type = storage_service.resize_image(
            rgba_image, max_width=400, max_height=400
        )

        img = Image.open(io.BytesIO(resized_data))
        assert img.mode in ("RGB", "RGBA")
        assert content_type == "image/webp"

    def test_resize_to_jpeg(self, storage_service):
        """Test can output as JPEG."""
        image = create_test_image()
        resized_data, content_type = storage_service.resize_image(
            image, max_width=400, max_height=400, output_format="JPEG"
        )

        img = Image.open(io.BytesIO(resized_data))
        assert img.format == "JPEG"
        assert content_type == "image/jpeg"


class TestStorageServiceThumbnail:
    """Tests for thumbnail creation."""

    def test_create_thumbnail_square_crop(self, storage_service):
        """Test thumbnail creates square crop."""
        wide_image = create_test_image(width=1000, height=500)
        thumb_data, content_type = storage_service.create_thumbnail(
            wide_image, size=100
        )

        img = Image.open(io.BytesIO(thumb_data))
        assert img.width == 100
        assert img.height == 100
        assert content_type == "image/webp"

    def test_create_thumbnail_tall_image(self, storage_service):
        """Test thumbnail handles tall images."""
        tall_image = create_test_image(width=500, height=1000)
        thumb_data, _ = storage_service.create_thumbnail(tall_image, size=100)

        img = Image.open(io.BytesIO(thumb_data))
        assert img.width == 100
        assert img.height == 100

    def test_create_thumbnail_already_square(self, storage_service):
        """Test thumbnail handles already square images."""
        square_image = create_test_image(width=800, height=800)
        thumb_data, _ = storage_service.create_thumbnail(square_image, size=100)

        img = Image.open(io.BytesIO(thumb_data))
        assert img.width == 100
        assert img.height == 100


class TestStorageServiceUploadAvatar:
    """Tests for avatar upload."""

    async def test_upload_avatar_success(self, storage_service, mock_backend):
        """Test successful avatar upload."""
        image_data = create_test_image()
        mock_backend.upload.side_effect = [
            "https://example.com/avatar.webp",
            "https://example.com/thumb.webp",
        ]

        result = await storage_service.upload_avatar(
            user_id="user-123",
            file_data=image_data,
            content_type="image/jpeg",
            filename="profile.jpg",
        )

        assert "avatar_url" in result
        assert "avatar_thumbnail_url" in result
        assert mock_backend.upload.call_count == 2

    async def test_upload_avatar_validation_error(self, storage_service):
        """Test upload rejects invalid image."""
        with pytest.raises(ValueError, match="Invalid image"):
            await storage_service.upload_avatar(
                user_id="user-123",
                file_data=b"not an image",
                content_type="image/jpeg",
            )

    async def test_upload_avatar_wrong_content_type(self, storage_service):
        """Test upload rejects wrong content type."""
        image_data = create_test_image()
        with pytest.raises(ValueError, match="Invalid file type"):
            await storage_service.upload_avatar(
                user_id="user-123",
                file_data=image_data,
                content_type="image/gif",
            )


class TestStorageServiceDeleteAvatar:
    """Tests for avatar deletion."""

    async def test_delete_avatar_success(self, storage_service, mock_backend):
        """Test successful avatar deletion."""
        result = await storage_service.delete_avatar(
            "https://example.com/avatars/user-123/abc123/avatar.webp"
        )

        assert result is True
        assert mock_backend.delete.call_count == 2

    async def test_delete_avatar_invalid_url(self, storage_service, mock_backend):
        """Test deletion with invalid URL format."""
        result = await storage_service.delete_avatar(
            "https://example.com/something/else.jpg"
        )

        assert result is False
        mock_backend.delete.assert_not_called()


class TestLocalStorageBackend:
    """Tests for LocalStorageBackend."""

    async def test_upload_creates_file(self, tmp_path):
        """Test upload creates file on disk."""
        backend = LocalStorageBackend(base_path=str(tmp_path))

        await backend.upload(
            file_data=b"test content",
            key="test/file.txt",
            content_type="text/plain",
        )

        assert (tmp_path / "test" / "file.txt").exists()
        assert (tmp_path / "test" / "file.txt").read_bytes() == b"test content"

    async def test_delete_removes_file(self, tmp_path):
        """Test delete removes file from disk."""
        backend = LocalStorageBackend(base_path=str(tmp_path))

        # Create a file first
        (tmp_path / "test").mkdir()
        (tmp_path / "test" / "file.txt").write_bytes(b"test content")

        result = await backend.delete("test/file.txt")

        assert result is True
        assert not (tmp_path / "test" / "file.txt").exists()

    async def test_delete_nonexistent_file(self, tmp_path):
        """Test delete returns False for nonexistent file."""
        backend = LocalStorageBackend(base_path=str(tmp_path))

        result = await backend.delete("nonexistent/file.txt")

        assert result is False


class TestS3StorageBackend:
    """Tests for S3StorageBackend."""

    @patch("app.services.storage.get_settings")
    async def test_upload_calls_s3_put_object(self, mock_get_settings):
        """Test upload calls S3 put_object."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-west-2"
        mock_settings.s3_access_key_id = "key"
        mock_settings.s3_secret_access_key = "secret"
        mock_settings.s3_endpoint_url = ""
        mock_settings.storage_base_url = "https://cdn.example.com"
        mock_get_settings.return_value = mock_settings

        # Mock aioboto3
        with patch("app.services.storage.S3StorageBackend._get_client_config"):
            backend = S3StorageBackend()

            mock_s3 = AsyncMock()
            mock_s3.put_object = AsyncMock()

            with patch.object(
                backend._session,
                "client",
                return_value=AsyncMock(
                    __aenter__=AsyncMock(return_value=mock_s3),
                    __aexit__=AsyncMock(),
                ),
            ):
                url = await backend.upload(
                    file_data=b"test content",
                    key="test/file.txt",
                    content_type="text/plain",
                )

                assert url == "https://cdn.example.com/test/file.txt"
                mock_s3.put_object.assert_called_once()


class TestGetStorageService:
    """Tests for get_storage_service factory."""

    @patch("app.services.storage.get_settings")
    def test_returns_storage_service(self, mock_get_settings, mock_settings):
        """Test factory returns StorageService instance."""
        mock_get_settings.return_value = mock_settings

        service = get_storage_service()

        assert isinstance(service, StorageService)

    @patch("app.services.storage.get_settings")
    def test_uses_local_backend_when_no_s3(self, mock_get_settings, mock_settings):
        """Test uses LocalStorageBackend when S3 not configured."""
        mock_settings.s3_bucket_name = ""
        mock_get_settings.return_value = mock_settings

        service = get_storage_service()

        assert isinstance(service._backend, LocalStorageBackend)


class TestStorageServiceEdgeCases:
    """Edge case tests for StorageService."""

    def test_resize_palette_mode_image(self, storage_service):
        """Test resizing palette mode (P) images."""
        # Create a palette mode image
        img = Image.new("P", (800, 600))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        palette_image = buffer.read()

        resized_data, _ = storage_service.resize_image(
            palette_image, max_width=400, max_height=400
        )

        result_img = Image.open(io.BytesIO(resized_data))
        assert result_img.mode in ("RGB", "RGBA", "P")

    def test_resize_with_different_quality(self, storage_service):
        """Test resize with different quality settings uses JPEG for consistent comparison."""
        # Create a larger image with more detail for quality comparison
        image = create_test_image(width=800, height=600)

        low_quality, _ = storage_service.resize_image(
            image, max_width=800, max_height=600, quality=20, output_format="JPEG"
        )
        high_quality, _ = storage_service.resize_image(
            image, max_width=800, max_height=600, quality=95, output_format="JPEG"
        )

        # High quality should be larger (JPEG is more predictable than WebP)
        assert len(high_quality) > len(low_quality)

    async def test_upload_avatar_creates_unique_keys(
        self, storage_service, mock_backend
    ):
        """Test each upload creates unique storage keys."""
        image_data = create_test_image()
        mock_backend.upload.return_value = "https://example.com/test.webp"

        await storage_service.upload_avatar(
            user_id="user-123",
            file_data=image_data,
            content_type="image/jpeg",
        )

        # Check the keys passed to upload are unique
        call_args_list = mock_backend.upload.call_args_list
        keys = [call[0][1] for call in call_args_list]  # Second positional arg is key

        assert "avatars/user-123/" in keys[0]
        assert "avatars/user-123/" in keys[1]
        assert "avatar.webp" in keys[0]
        assert "thumb.webp" in keys[1]
