"""Tests for core module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import yt_dlp

from ytdl_helper.config import Settings
from ytdl_helper.core import (
    VideoDownloader,
    VideoInfo,
    DownloadError,
    RightsError,
    ProgressHook,
)


class TestVideoInfo:
    """Test VideoInfo class."""

    def test_video_info_creation(self) -> None:
        """Test VideoInfo creation."""
        info_data = {
            "title": "Test Video",
            "duration": 120,
            "uploader": "Test User",
            "upload_date": "20231201",
            "view_count": 1000,
            "description": "Test description",
            "thumbnail": "http://example.com/thumb.jpg",
            "webpage_url": "http://example.com/video",
            "formats": [{"format_id": "best", "ext": "mp4"}],
        }
        
        video_info = VideoInfo(info_data)
        
        assert video_info.title == "Test Video"
        assert video_info.duration == 120
        assert video_info.uploader == "Test User"
        assert video_info.upload_date == "20231201"
        assert video_info.view_count == 1000
        assert video_info.description == "Test description"
        assert video_info.thumbnail == "http://example.com/thumb.jpg"
        assert video_info.url == "http://example.com/video"
        assert video_info.formats == [{"format_id": "best", "ext": "mp4"}]
        assert video_info.is_playlist is False
        assert video_info.playlist_count == 1

    def test_playlist_info(self) -> None:
        """Test playlist information."""
        info_data = {
            "title": "Test Playlist",
            "_type": "playlist",
            "playlist_count": 5,
            "entries": [{"title": "Video 1"}, {"title": "Video 2"}],
        }
        
        video_info = VideoInfo(info_data)
        
        assert video_info.title == "Test Playlist"
        assert video_info.is_playlist is True
        assert video_info.playlist_count == 5

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        info_data = {
            "title": "Test Video",
            "duration": 120,
            "uploader": "Test User",
            "upload_date": "20231201",
            "view_count": 1000,
            "description": "Test description",
            "thumbnail": "http://example.com/thumb.jpg",
            "webpage_url": "http://example.com/video",
        }
        
        video_info = VideoInfo(info_data)
        result = video_info.to_dict()
        
        assert result["title"] == "Test Video"
        assert result["duration"] == 120
        assert result["uploader"] == "Test User"
        assert result["is_playlist"] is False

    def test_str_representation(self) -> None:
        """Test string representation."""
        info_data = {
            "title": "Test Video",
            "uploader": "Test User",
        }
        
        video_info = VideoInfo(info_data)
        assert str(video_info) == "Video: Test Video by Test User"


class TestProgressHook:
    """Test ProgressHook class."""

    def test_progress_hook_creation(self) -> None:
        """Test ProgressHook creation."""
        hook = ProgressHook()
        assert hook.progress_callback is None
        assert hook.console is not None

    def test_progress_hook_with_callback(self) -> None:
        """Test ProgressHook with callback."""
        callback = Mock()
        hook = ProgressHook(callback)
        assert hook.progress_callback == callback

    def test_progress_hook_downloading(self) -> None:
        """Test progress hook for downloading status."""
        callback = Mock()
        hook = ProgressHook(callback)
        
        data = {
            "status": "downloading",
            "downloaded_bytes": 1024,
            "total_bytes": 2048,
        }
        
        hook(data)
        callback.assert_called_once_with(data)

    def test_progress_hook_finished(self) -> None:
        """Test progress hook for finished status."""
        hook = ProgressHook()
        
        data = {
            "status": "finished",
            "filename": "test.mp4",
        }
        
        # Should not raise an exception
        hook(data)

    def test_progress_hook_error(self) -> None:
        """Test progress hook for error status."""
        hook = ProgressHook()
        
        data = {
            "status": "error",
            "error": "Test error",
        }
        
        # Should not raise an exception
        hook(data)


class TestVideoDownloader:
    """Test VideoDownloader class."""

    def test_downloader_creation(self) -> None:
        """Test VideoDownloader creation."""
        settings = Settings()
        downloader = VideoDownloader(settings)
        
        assert downloader.settings == settings
        assert downloader.console is not None
        assert downloader.progress_callback is None

    def test_downloader_creation_default_settings(self) -> None:
        """Test VideoDownloader creation with default settings."""
        downloader = VideoDownloader()
        
        assert isinstance(downloader.settings, Settings)
        assert downloader.console is not None

    def test_set_progress_callback(self) -> None:
        """Test setting progress callback."""
        downloader = VideoDownloader()
        callback = Mock()
        
        downloader.set_progress_callback(callback)
        assert downloader.progress_callback == callback

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    def test_get_video_info_success(self, mock_ydl_class) -> None:
        """Test successful video info extraction."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        expected_info = {
            "title": "Test Video",
            "duration": 120,
            "uploader": "Test User",
            "webpage_url": "http://example.com/video",
        }
        mock_ydl.extract_info.return_value = expected_info
        
        downloader = VideoDownloader()
        video_info = downloader.get_video_info("http://example.com/video")
        
        assert video_info.title == "Test Video"
        assert video_info.duration == 120
        assert video_info.uploader == "Test User"

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    def test_get_video_info_failure(self, mock_ydl_class) -> None:
        """Test video info extraction failure."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = None
        
        downloader = VideoDownloader()
        
        with pytest.raises(DownloadError, match="Could not extract video information"):
            downloader.get_video_info("http://example.com/video")

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    def test_get_video_info_exception(self, mock_ydl_class) -> None:
        """Test video info extraction with exception."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")
        
        downloader = VideoDownloader()
        
        with pytest.raises(DownloadError, match="Failed to get video info"):
            downloader.get_video_info("http://example.com/video")

    @patch("ytdl_helper.core.validate_url")
    def test_get_video_info_invalid_url(self, mock_validate) -> None:
        """Test video info with invalid URL."""
        mock_validate.return_value = False
        
        downloader = VideoDownloader()
        
        with pytest.raises(ValueError, match="Invalid URL"):
            downloader.get_video_info("invalid-url")

    @patch("ytdl_helper.core.confirm_rights")
    def test_validate_rights_skip_check(self, mock_confirm) -> None:
        """Test rights validation with skip check."""
        settings = Settings()
        settings.user.skip_rights_check = True
        
        downloader = VideoDownloader(settings)
        video_info = VideoInfo({"title": "Test Video"})
        
        result = downloader.validate_rights(video_info)
        assert result is True
        mock_confirm.assert_not_called()

    @patch("ytdl_helper.core.confirm_rights")
    def test_validate_rights_no_confirmation(self, mock_confirm) -> None:
        """Test rights validation without confirmation."""
        settings = Settings()
        settings.user.confirm_rights = False
        
        downloader = VideoDownloader(settings)
        video_info = VideoInfo({"title": "Test Video"})
        
        result = downloader.validate_rights(video_info)
        assert result is True
        mock_confirm.assert_not_called()

    @patch("ytdl_helper.core.confirm_rights")
    def test_validate_rights_with_confirmation(self, mock_confirm) -> None:
        """Test rights validation with confirmation."""
        settings = Settings()
        settings.user.confirm_rights = True
        
        mock_confirm.return_value = True
        
        downloader = VideoDownloader(settings)
        video_info = VideoInfo({"title": "Test Video"})
        
        result = downloader.validate_rights(video_info)
        assert result is True
        mock_confirm.assert_called_once()

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    @patch("ytdl_helper.core.VideoDownloader.validate_rights")
    def test_download_single_success(self, mock_validate, mock_ydl_class) -> None:
        """Test successful single video download."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_validate.return_value = True
        
        settings = Settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.download.output_dir = Path(tmpdir)
            downloader = VideoDownloader(settings)
            
            result = downloader.download_single("http://example.com/video")
            
            assert isinstance(result, Path)
            mock_ydl.download.assert_called_once_with(["http://example.com/video"])

    @patch("ytdl_helper.core.VideoDownloader.validate_rights")
    def test_download_single_no_rights(self, mock_validate) -> None:
        """Test single video download without rights."""
        mock_validate.return_value = False
        
        downloader = VideoDownloader()
        
        with pytest.raises(RightsError, match="User does not confirm having rights"):
            downloader.download_single("http://example.com/video")

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    def test_download_single_exception(self, mock_ydl_class) -> None:
        """Test single video download with exception."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.download.side_effect = Exception("Download failed")
        
        settings = Settings()
        settings.user.skip_rights_check = True
        downloader = VideoDownloader(settings)
        
        with pytest.raises(DownloadError, match="Download failed"):
            downloader.download_single("http://example.com/video")

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    @patch("ytdl_helper.core.VideoDownloader.validate_rights")
    def test_download_playlist_success(self, mock_validate, mock_ydl_class) -> None:
        """Test successful playlist download."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_validate.return_value = True
        
        settings = Settings()
        settings.user.allow_playlist_download = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.download.output_dir = Path(tmpdir)
            downloader = VideoDownloader(settings)
            
            # Mock playlist info
            with patch.object(downloader, "get_video_info") as mock_get_info:
                mock_info = Mock()
                mock_info.is_playlist = True
                mock_get_info.return_value = mock_info
                
                result = downloader.download_playlist("http://example.com/playlist")
                
                assert isinstance(result, list)
                mock_ydl.download.assert_called_once_with(["http://example.com/playlist"])

    def test_download_playlist_not_allowed(self) -> None:
        """Test playlist download when not allowed."""
        settings = Settings()
        settings.user.allow_playlist_download = False
        
        downloader = VideoDownloader(settings)
        
        with pytest.raises(RightsError, match="Playlist downloads are not allowed"):
            downloader.download_playlist("http://example.com/playlist")

    @patch("ytdl_helper.core.yt_dlp.YoutubeDL")
    def test_download_playlist_not_playlist(self, mock_ydl_class) -> None:
        """Test playlist download with non-playlist URL."""
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        settings = Settings()
        settings.user.allow_playlist_download = True
        
        downloader = VideoDownloader(settings)
        
        # Mock non-playlist info
        with patch.object(downloader, "get_video_info") as mock_get_info:
            mock_info = Mock()
            mock_info.is_playlist = False
            mock_get_info.return_value = mock_info
            
            with pytest.raises(ValueError, match="URL is not a playlist"):
                downloader.download_playlist("http://example.com/video")

    def test_extract_audio_only(self) -> None:
        """Test audio extraction."""
        settings = Settings()
        downloader = VideoDownloader(settings)
        
        with patch.object(downloader, "download_single") as mock_download:
            mock_download.return_value = Path("/tmp/test.mp3")
            
            result = downloader.extract_audio_only("http://example.com/video")
            
            assert result == Path("/tmp/test.mp3")
            mock_download.assert_called_once()

    def test_save_metadata(self) -> None:
        """Test saving metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            video_info = VideoInfo({"title": "Test Video"})
            
            downloader = VideoDownloader()
            result = downloader.save_metadata(video_info, output_dir)
            
            assert result.exists()
            assert result.name == "Test Video_metadata.json"
            
            # Check content
            with open(result, "r") as f:
                data = json.load(f)
                assert data["title"] == "Test Video"

    @patch("requests.get")
    def test_download_thumbnail_success(self, mock_get) -> None:
        """Test successful thumbnail download."""
        mock_response = Mock()
        mock_response.content = b"thumbnail_data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            video_info = VideoInfo({
                "title": "Test Video",
                "thumbnail": "http://example.com/thumb.jpg"
            })
            
            downloader = VideoDownloader()
            result = downloader.download_thumbnail(video_info, output_dir)
            
            assert result is not None
            assert result.exists()
            assert result.name == "Test Video_thumbnail.jpg"

    def test_download_thumbnail_no_thumbnail(self) -> None:
        """Test thumbnail download with no thumbnail URL."""
        video_info = VideoInfo({"title": "Test Video"})
        downloader = VideoDownloader()
        
        result = downloader.download_thumbnail(video_info, Path("/tmp"))
        assert result is None

    @patch("requests.get")
    def test_download_thumbnail_failure(self, mock_get) -> None:
        """Test thumbnail download failure."""
        mock_get.side_effect = Exception("Network error")
        
        video_info = VideoInfo({
            "title": "Test Video",
            "thumbnail": "http://example.com/thumb.jpg"
        })
        
        downloader = VideoDownloader()
        result = downloader.download_thumbnail(video_info, Path("/tmp"))
        assert result is None

