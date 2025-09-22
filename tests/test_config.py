"""Tests for config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ytdl_helper.config import Settings, DownloadSettings, MetadataSettings, UserSettings


class TestDownloadSettings:
    """Test DownloadSettings class."""

    def test_default_values(self) -> None:
        """Test default values."""
        settings = DownloadSettings()
        assert settings.format == "best"
        assert settings.output_template == "%(title)s.%(ext)s"
        assert settings.output_dir == Path.cwd()
        assert settings.extract_audio is False
        assert settings.audio_format == "mp3"
        assert settings.video_format == "mp4"
        assert settings.quality == "best"
        assert settings.max_filesize is None
        assert settings.max_duration is None

    def test_custom_values(self) -> None:
        """Test custom values."""
        output_dir = Path("/tmp/test")
        settings = DownloadSettings(
            format="worst",
            output_template="%(uploader)s - %(title)s.%(ext)s",
            output_dir=output_dir,
            extract_audio=True,
            audio_format="wav",
            max_filesize="100MB",
            max_duration=300,
        )
        assert settings.format == "worst"
        assert settings.output_template == "%(uploader)s - %(title)s.%(ext)s"
        assert settings.output_dir == output_dir
        assert settings.extract_audio is True
        assert settings.audio_format == "wav"
        assert settings.max_filesize == "100MB"
        assert settings.max_duration == 300

    def test_output_dir_creation(self) -> None:
        """Test that output directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "nonexistent" / "path"
            settings = DownloadSettings(output_dir=test_dir)
            assert test_dir.exists()

    def test_format_validation(self) -> None:
        """Test format validation."""
        with pytest.raises(ValidationError):
            DownloadSettings(format="")

    def test_empty_format_validation(self) -> None:
        """Test empty format validation."""
        with pytest.raises(ValidationError):
            DownloadSettings(format="")


class TestMetadataSettings:
    """Test MetadataSettings class."""

    def test_default_values(self) -> None:
        """Test default values."""
        settings = MetadataSettings()
        assert settings.write_info_json is False
        assert settings.write_thumbnail is False
        assert settings.write_description is False
        assert settings.write_annotations is False
        assert settings.write_subtitles is False
        assert settings.subtitle_langs == ["en"]

    def test_custom_values(self) -> None:
        """Test custom values."""
        settings = MetadataSettings(
            write_info_json=True,
            write_thumbnail=True,
            write_description=True,
            subtitle_langs=["en", "es", "fr"],
        )
        assert settings.write_info_json is True
        assert settings.write_thumbnail is True
        assert settings.write_description is True
        assert settings.subtitle_langs == ["en", "es", "fr"]


class TestUserSettings:
    """Test UserSettings class."""

    def test_default_values(self) -> None:
        """Test default values."""
        settings = UserSettings()
        assert settings.confirm_rights is True
        assert settings.skip_rights_check is False
        assert settings.max_playlist_items == 10
        assert settings.allow_playlist_download is False

    def test_custom_values(self) -> None:
        """Test custom values."""
        settings = UserSettings(
            confirm_rights=False,
            skip_rights_check=True,
            max_playlist_items=50,
            allow_playlist_download=True,
        )
        assert settings.confirm_rights is False
        assert settings.skip_rights_check is True
        assert settings.max_playlist_items == 50
        assert settings.allow_playlist_download is True


class TestSettings:
    """Test main Settings class."""

    def test_default_values(self) -> None:
        """Test default values."""
        settings = Settings()
        assert isinstance(settings.download, DownloadSettings)
        assert isinstance(settings.metadata, MetadataSettings)
        assert isinstance(settings.user, UserSettings)
        assert settings.verbose is False
        assert settings.quiet is False
        assert settings.retries == 3
        assert settings.fragment_retries == 10

    def test_custom_values(self) -> None:
        """Test custom values."""
        settings = Settings(
            verbose=True,
            quiet=False,
            retries=5,
            fragment_retries=15,
        )
        assert settings.verbose is True
        assert settings.quiet is False
        assert settings.retries == 5
        assert settings.fragment_retries == 15

    def test_cache_dir_creation(self) -> None:
        """Test that cache directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            settings = Settings(cache_dir=cache_dir)
            assert cache_dir.exists()

    def test_get_ytdlp_options(self) -> None:
        """Test yt-dlp options generation."""
        settings = Settings()
        options = settings.get_ytdlp_options()
        
        assert "format" in options
        assert "outtmpl" in options
        assert "retries" in options
        assert "fragment_retries" in options
        assert "quiet" in options
        assert "no_warnings" in options

    def test_get_ytdlp_options_audio(self) -> None:
        """Test yt-dlp options for audio extraction."""
        settings = Settings()
        settings.download.extract_audio = True
        options = settings.get_ytdlp_options()
        
        assert options["format"] == "bestaudio/best"
        assert "postprocessors" in options

    def test_get_ytdlp_options_metadata(self) -> None:
        """Test yt-dlp options for metadata."""
        settings = Settings()
        settings.metadata.write_info_json = True
        settings.metadata.write_thumbnail = True
        options = settings.get_ytdlp_options()
        
        assert options["writeinfojson"] is True
        assert options["writethumbnail"] is True

    def test_get_ytdlp_options_playlist(self) -> None:
        """Test yt-dlp options for playlist."""
        settings = Settings()
        settings.download.playlist_start = 1
        settings.download.playlist_end = 5
        options = settings.get_ytdlp_options()
        
        assert options["playliststart"] == 1
        assert options["playlistend"] == 5

    @patch.dict("os.environ", {"YTDL_VERBOSE": "true", "YTDL_RETRIES": "10"})
    def test_from_env(self) -> None:
        """Test loading settings from environment."""
        settings = Settings.from_env()
        assert settings.verbose is True
        assert settings.retries == 10

    def test_save_and_load_from_file(self) -> None:
        """Test saving and loading settings from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            file_path = Path(f.name)
        
        try:
            # Create settings
            settings = Settings()
            settings.verbose = True
            settings.retries = 5
            
            # Save to file
            settings.save_to_file(file_path)
            
            # Load from file
            loaded_settings = Settings.load_from_file(file_path)
            
            assert loaded_settings.verbose is True
            assert loaded_settings.retries == 5
        finally:
            file_path.unlink()

    def test_load_from_nonexistent_file(self) -> None:
        """Test loading from nonexistent file."""
        nonexistent_file = Path("/tmp/nonexistent.json")
        settings = Settings.load_from_file(nonexistent_file)
        assert isinstance(settings, Settings)

