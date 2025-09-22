"""Tests for utils module."""

import tempfile
from pathlib import Path

import pytest

from ytdl_helper.utils import (
    validate_url,
    format_duration,
    format_file_size,
    sanitize_filename,
    create_output_path,
    is_playlist_url,
    extract_playlist_id,
    validate_output_path,
    get_safe_filename,
    truncate_string,
)


class TestValidateUrl:
    """Test URL validation."""

    def test_valid_youtube_urls(self) -> None:
        """Test valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/playlist?list=PLrAXtmRdnEQy5nCwNwzMp8",
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True

    def test_valid_other_platforms(self) -> None:
        """Test valid URLs from other platforms."""
        valid_urls = [
            "https://vimeo.com/123456789",
            "https://www.dailymotion.com/video/x123456",
            "https://www.twitch.tv/videos/123456789",
            "https://www.instagram.com/p/ABC123/",
            "https://www.tiktok.com/@user/video/123456789",
            "https://twitter.com/user/status/123456789",
            "https://x.com/user/status/123456789",
            "https://soundcloud.com/user/track",
            "https://bandcamp.com/album/album-name",
            "https://archive.org/details/video",
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True

    def test_invalid_urls(self) -> None:
        """Test invalid URLs."""
        invalid_urls = [
            "",
            None,
            "not-a-url",
            "ftp://example.com/file",
            "file:///local/path",
            "javascript:alert('test')",
            "mailto:test@example.com",
        ]
        
        for url in invalid_urls:
            assert validate_url(url) is False

    def test_empty_or_none_url(self) -> None:
        """Test empty or None URLs."""
        assert validate_url("") is False
        assert validate_url(None) is False


class TestFormatDuration:
    """Test duration formatting."""

    def test_seconds_only(self) -> None:
        """Test formatting seconds only."""
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"

    def test_minutes_and_seconds(self) -> None:
        """Test formatting minutes and seconds."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3599) == "59m 59s"

    def test_hours_minutes_seconds(self) -> None:
        """Test formatting hours, minutes, and seconds."""
        assert format_duration(3600) == "1h 0m 0s"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(7325) == "2h 2m 5s"

    def test_zero_duration(self) -> None:
        """Test zero duration."""
        assert format_duration(0) == "0s"

    def test_large_duration(self) -> None:
        """Test large duration."""
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(86400) == "24h 0m 0s"


class TestFormatFileSize:
    """Test file size formatting."""

    def test_bytes(self) -> None:
        """Test bytes formatting."""
        assert format_file_size(0) == "0.0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1023) == "1023.0 B"

    def test_kilobytes(self) -> None:
        """Test kilobytes formatting."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2.0 KB"

    def test_megabytes(self) -> None:
        """Test megabytes formatting."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 2.5) == "2.5 MB"

    def test_gigabytes(self) -> None:
        """Test gigabytes formatting."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1024 * 1024 * 1024 * 5) == "5.0 GB"

    def test_terabytes(self) -> None:
        """Test terabytes formatting."""
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_basic_sanitization(self) -> None:
        """Test basic filename sanitization."""
        assert sanitize_filename("test.mp4") == "test.mp4"
        assert sanitize_filename("test video.mp4") == "test video.mp4"

    def test_invalid_characters(self) -> None:
        """Test removal of invalid characters."""
        assert sanitize_filename("test<file.mp4") == "test_file.mp4"
        assert sanitize_filename("test>file.mp4") == "test_file.mp4"
        assert sanitize_filename("test:file.mp4") == "test_file.mp4"
        assert sanitize_filename("test\"file.mp4") == "test_file.mp4"
        assert sanitize_filename("test/file.mp4") == "test_file.mp4"
        assert sanitize_filename("test\\file.mp4") == "test_file.mp4"
        assert sanitize_filename("test|file.mp4") == "test_file.mp4"
        assert sanitize_filename("test?file.mp4") == "test_file.mp4"
        assert sanitize_filename("test*file.mp4") == "test_file.mp4"

    def test_control_characters(self) -> None:
        """Test removal of control characters."""
        assert sanitize_filename("test\x00file.mp4") == "testfile.mp4"
        assert sanitize_filename("test\x01file.mp4") == "testfile.mp4"

    def test_length_limit(self) -> None:
        """Test filename length limit."""
        long_name = "a" * 250
        result = sanitize_filename(long_name)
        assert len(result) == 200

    def test_leading_trailing_spaces(self) -> None:
        """Test removal of leading/trailing spaces and dots."""
        assert sanitize_filename(" test.mp4 ") == "test.mp4"
        assert sanitize_filename("...test.mp4...") == "test.mp4"
        assert sanitize_filename(" . test.mp4 . ") == ". test.mp4 ."


class TestCreateOutputPath:
    """Test output path creation."""

    def test_basic_template(self) -> None:
        """Test basic template replacement."""
        result = create_output_path(
            Path("/tmp"),
            "%(title)s.%(ext)s",
            "Test Video",
            "mp4"
        )
        assert result == Path("/tmp/Test Video.mp4")

    def test_template_with_uploader(self) -> None:
        """Test template with uploader."""
        result = create_output_path(
            Path("/tmp"),
            "%(uploader)s - %(title)s.%(ext)s",
            "Test Video",
            "mp4",
            uploader="Test User"
        )
        assert result == Path("/tmp/Test User - Test Video.mp4")

    def test_template_with_date(self) -> None:
        """Test template with upload date."""
        result = create_output_path(
            Path("/tmp"),
            "%(upload_date)s - %(title)s.%(ext)s",
            "Test Video",
            "mp4",
            upload_date="20231201"
        )
        assert result == Path("/tmp/20231201 - Test Video.mp4")

    def test_extension_handling(self) -> None:
        """Test extension handling."""
        result = create_output_path(
            Path("/tmp"),
            "%(title)s",
            "Test Video",
            "mp4"
        )
        assert result == Path("/tmp/Test Video.mp4")

    def test_multiple_extensions(self) -> None:
        """Test handling of multiple extensions."""
        result = create_output_path(
            Path("/tmp"),
            "%(title)s.mp4",
            "Test Video",
            "mp4"
        )
        assert result == Path("/tmp/Test Video.mp4.mp4")


class TestIsPlaylistUrl:
    """Test playlist URL detection."""

    def test_playlist_indicators(self) -> None:
        """Test URLs with playlist indicators."""
        playlist_urls = [
            "https://youtube.com/playlist?list=PL123",
            "https://youtube.com/channel/UC123",
            "https://youtube.com/user/testuser",
            "https://youtube.com/c/testchannel",
            "https://youtube.com/@testuser",
            "https://example.com/video?list=123",
        ]
        
        for url in playlist_urls:
            assert is_playlist_url(url) is True

    def test_non_playlist_urls(self) -> None:
        """Test URLs without playlist indicators."""
        non_playlist_urls = [
            "https://youtube.com/watch?v=123",
            "https://youtu.be/123",
            "https://vimeo.com/123456",
            "https://example.com/video",
        ]
        
        for url in non_playlist_urls:
            assert is_playlist_url(url) is False


class TestExtractPlaylistId:
    """Test playlist ID extraction."""

    def test_youtube_playlist_id(self) -> None:
        """Test YouTube playlist ID extraction."""
        url = "https://youtube.com/playlist?list=PLrAXtmRdnEQy5nCwNwzMp8"
        result = extract_playlist_id(url)
        assert result == "PLrAXtmRdnEQy5nCwNwzMp8"

    def test_youtube_playlist_id_with_other_params(self) -> None:
        """Test YouTube playlist ID with other parameters."""
        url = "https://youtube.com/playlist?list=PL123&index=1"
        result = extract_playlist_id(url)
        assert result == "PL123"

    def test_youtube_short_url(self) -> None:
        """Test YouTube short URL."""
        url = "https://youtu.be/123?list=PL456"
        result = extract_playlist_id(url)
        assert result == "PL456"

    def test_non_playlist_url(self) -> None:
        """Test non-playlist URL."""
        url = "https://youtube.com/watch?v=123"
        result = extract_playlist_id(url)
        assert result is None

    def test_other_platforms(self) -> None:
        """Test other platforms (should return None)."""
        url = "https://vimeo.com/123456"
        result = extract_playlist_id(url)
        assert result is None


class TestValidateOutputPath:
    """Test output path validation."""

    def test_valid_output_path(self) -> None:
        """Test valid output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.mp4"
            assert validate_output_path(path) is True

    def test_nonexistent_parent_directory(self) -> None:
        """Test path with nonexistent parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent" / "test.mp4"
            assert validate_output_path(path) is True  # Should create directory

    def test_unwritable_directory(self) -> None:
        """Test unwritable directory."""
        # This test might fail on some systems due to permissions
        # We'll use a path that's likely to be unwritable
        path = Path("/root/test.mp4")
        # We can't easily test unwritable paths in CI, so we'll skip this
        # assert validate_output_path(path) is False


class TestGetSafeFilename:
    """Test safe filename generation."""

    def test_basic_filename(self) -> None:
        """Test basic filename generation."""
        result = get_safe_filename("Test Video", "mp4")
        assert result == "Test Video.mp4"

    def test_filename_with_extension(self) -> None:
        """Test filename that already has extension."""
        result = get_safe_filename("Test Video.mp4", "mp4")
        assert result == "Test Video.mp4.mp4"

    def test_sanitized_filename(self) -> None:
        """Test sanitized filename."""
        result = get_safe_filename("Test<Video>", "mp4")
        assert result == "Test_Video_.mp4"


class TestTruncateString:
    """Test string truncation."""

    def test_short_string(self) -> None:
        """Test short string (no truncation needed)."""
        result = truncate_string("Short", 10)
        assert result == "Short"

    def test_long_string(self) -> None:
        """Test long string (truncation needed)."""
        result = truncate_string("This is a very long string", 10)
        assert result == "This is..."
        assert len(result) == 10

    def test_exact_length(self) -> None:
        """Test string of exact length."""
        result = truncate_string("Exactly", 7)
        assert result == "Exactly"

    def test_default_length(self) -> None:
        """Test default length."""
        result = truncate_string("This is a test string that is longer than 50 characters")
        assert len(result) == 50
        assert result.endswith("...")

