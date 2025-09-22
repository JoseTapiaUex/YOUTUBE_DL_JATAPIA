"""Tests for CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

from ytdl_helper.cli import app


class TestCLI:
    """Test CLI commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_download_command_success(self, mock_downloader_class) -> None:
        """Test successful download command."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Video",
            is_playlist=False
        )
        mock_downloader.validate_rights.return_value = True
        mock_downloader.download_single.return_value = Path("/tmp/test.mp4")
        
        result = self.runner.invoke(
            app,
            ["download", "https://youtube.com/watch?v=test", "--skip-rights-check"]
        )
        
        assert result.exit_code == 0
        mock_downloader.download_single.assert_called_once()

    @patch("ytdl_helper.cli.validate_url")
    def test_download_command_invalid_url(self, mock_validate) -> None:
        """Test download command with invalid URL."""
        mock_validate.return_value = False
        
        result = self.runner.invoke(
            app,
            ["download", "invalid-url"]
        )
        
        assert result.exit_code == 1
        assert "Invalid URL provided" in result.output

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_download_command_no_rights(self, mock_downloader_class) -> None:
        """Test download command without rights."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Video",
            is_playlist=False
        )
        mock_downloader.validate_rights.return_value = False
        
        result = self.runner.invoke(
            app,
            ["download", "https://youtube.com/watch?v=test"]
        )
        
        assert result.exit_code == 1
        assert "Rights confirmation required" in result.output

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_download_command_playlist(self, mock_downloader_class) -> None:
        """Test download command for playlist."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Playlist",
            is_playlist=True
        )
        mock_downloader.validate_rights.return_value = True
        mock_downloader.download_playlist.return_value = [
            Path("/tmp/video1.mp4"),
            Path("/tmp/video2.mp4")
        ]
        
        result = self.runner.invoke(
            app,
            [
                "download",
                "https://youtube.com/playlist?list=test",
                "--playlist",
                "--skip-rights-check"
            ]
        )
        
        assert result.exit_code == 0
        mock_downloader.download_playlist.assert_called_once()

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_download_command_playlist_not_allowed(self, mock_downloader_class) -> None:
        """Test download command for playlist when not allowed."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Playlist",
            is_playlist=True
        )
        
        result = self.runner.invoke(
            app,
            ["download", "https://youtube.com/playlist?list=test"]
        )
        
        assert result.exit_code == 1
        assert "Use --playlist flag to download" in result.output

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_info_command_success(self, mock_downloader_class) -> None:
        """Test successful info command."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Video",
            uploader="Test User",
            duration=120,
            upload_date="20231201",
            view_count=1000,
            url="https://youtube.com/watch?v=test",
            is_playlist=False,
            playlist_count=1
        )
        mock_downloader.list_formats.return_value = [
            {"format_id": "best", "ext": "mp4", "quality": 1080}
        ]
        
        result = self.runner.invoke(
            app,
            ["info", "https://youtube.com/watch?v=test", "--formats"]
        )
        
        assert result.exit_code == 0
        mock_downloader.get_video_info.assert_called_once()
        mock_downloader.list_formats.assert_called_once()

    @patch("ytdl_helper.cli.validate_url")
    def test_info_command_invalid_url(self, mock_validate) -> None:
        """Test info command with invalid URL."""
        mock_validate.return_value = False
        
        result = self.runner.invoke(
            app,
            ["info", "invalid-url"]
        )
        
        assert result.exit_code == 1
        assert "Invalid URL provided" in result.output

    def test_config_command_show(self) -> None:
        """Test config show command."""
        result = self.runner.invoke(app, ["config", "--show"])
        
        assert result.exit_code == 0
        assert "Current Configuration" in result.output

    def test_config_command_reset(self) -> None:
        """Test config reset command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            result = self.runner.invoke(
                app,
                ["config", "--reset", "--config-file", str(config_file)]
            )
            
            assert result.exit_code == 0
            assert "Configuration reset to defaults" in result.output
            assert config_file.exists()

    def test_version_command(self) -> None:
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "ytdl-helper" in result.output
        assert "version" in result.output

    def test_help_command(self) -> None:
        """Test help command."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "ytdl-helper" in result.output
        assert "A CLI tool for downloading videos" in result.output

    @patch("ytdl_helper.cli.Prompt")
    @patch("ytdl_helper.cli.VideoDownloader")
    def test_interactive_command(self, mock_downloader_class, mock_prompt) -> None:
        """Test interactive command."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Video",
            uploader="Test User",
            duration=120,
            upload_date="20231201",
            view_count=1000,
            url="https://youtube.com/watch?v=test",
            is_playlist=False,
            playlist_count=1
        )
        
        # Mock user input sequence
        mock_prompt.ask.side_effect = [
            "https://youtube.com/watch?v=test",  # URL
            "quit"  # Quit
        ]
        
        result = self.runner.invoke(app, ["interactive"], input="\n")
        
        # Should not crash and should handle the quit command
        assert result.exit_code == 0

    def test_download_command_with_options(self) -> None:
        """Test download command with various options."""
        with patch("ytdl_helper.cli.VideoDownloader") as mock_downloader_class:
            mock_downloader = Mock()
            mock_downloader_class.return_value = mock_downloader
            mock_downloader.get_video_info.return_value = Mock(
                title="Test Video",
                is_playlist=False
            )
            mock_downloader.validate_rights.return_value = True
            mock_downloader.download_single.return_value = Path("/tmp/test.mp3")
            
            result = self.runner.invoke(
                app,
                [
                    "download",
                    "https://youtube.com/watch?v=test",
                    "--audio-only",
                    "--audio-format", "wav",
                    "--format", "bestaudio",
                    "--output-dir", "/tmp",
                    "--metadata",
                    "--skip-rights-check"
                ]
            )
            
            assert result.exit_code == 0
            mock_downloader.download_single.assert_called_once()

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_download_command_download_error(self, mock_downloader_class) -> None:
        """Test download command with download error."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.return_value = Mock(
            title="Test Video",
            is_playlist=False
        )
        mock_downloader.validate_rights.return_value = True
        mock_downloader.download_single.side_effect = Exception("Network error")
        
        result = self.runner.invoke(
            app,
            ["download", "https://youtube.com/watch?v=test", "--skip-rights-check"]
        )
        
        assert result.exit_code == 1
        assert "Download failed" in result.output

    @patch("ytdl_helper.cli.VideoDownloader")
    def test_info_command_download_error(self, mock_downloader_class) -> None:
        """Test info command with error."""
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.get_video_info.side_effect = Exception("Network error")
        
        result = self.runner.invoke(
            app,
            ["info", "https://youtube.com/watch?v=test"]
        )
        
        assert result.exit_code == 1
        assert "Failed to get video information" in result.output

    def test_no_args_help(self) -> None:
        """Test that no arguments shows help."""
        result = self.runner.invoke(app, [])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output

