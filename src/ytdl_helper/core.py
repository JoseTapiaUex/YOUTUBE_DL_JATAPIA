"""Core functionality for video downloading with yt-dlp."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

import yt_dlp
from rich.console import Console

from ytdl_helper.config import Settings
from ytdl_helper.utils import validate_url, confirm_rights

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Custom exception for download errors."""

    pass


class RightsError(Exception):
    """Custom exception for rights-related errors."""

    pass


class VideoInfo:
    """Container for video information."""

    def __init__(self, info: Dict[str, Any]) -> None:
        """Initialize with yt-dlp info dictionary."""
        self.title = info.get("title", "Unknown")
        self.duration = info.get("duration", 0)
        self.uploader = info.get("uploader", "Unknown")
        self.upload_date = info.get("upload_date", "")
        self.view_count = info.get("view_count", 0)
        self.description = info.get("description", "")
        self.thumbnail = info.get("thumbnail", "")
        self.url = info.get("webpage_url", info.get("url", ""))
        self.formats = info.get("formats", [])
        self.is_playlist = info.get("_type") == "playlist"
        self.playlist_count = info.get("playlist_count", 1)
        self.entries = info.get("entries", [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "duration": self.duration,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "url": self.url,
            "is_playlist": self.is_playlist,
            "playlist_count": self.playlist_count,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Video: {self.title} by {self.uploader}"


class ProgressHook:
    """Progress hook for yt-dlp."""

    def __init__(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """Initialize with optional progress callback."""
        self.progress_callback = progress_callback
        self.console = Console()

    def __call__(self, d: Dict[str, Any]) -> None:
        """Progress hook callback."""
        if d["status"] == "downloading":
            if self.progress_callback:
                self.progress_callback(d)
        elif d["status"] == "finished":
            logger.info(f"Downloaded: {d.get('filename', 'Unknown')}")
        elif d["status"] == "error":
            logger.error(f"Download error: {d.get('error', 'Unknown error')}")


class VideoDownloader:
    """Main video downloader class."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize downloader with settings."""
        self.settings = settings or Settings()
        self.console = Console()
        self.progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set progress callback function."""
        self.progress_callback = callback

    def get_video_info(self, url: str) -> VideoInfo:
        """Get video information without downloading."""
        if not validate_url(url):
            raise ValueError(f"Invalid URL: {url}")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    raise DownloadError("Could not extract video information")
                
                return VideoInfo(info)
        except Exception as e:
            raise DownloadError(f"Failed to get video info: {str(e)}")

    def validate_rights(self, video_info: VideoInfo) -> bool:
        """Validate user has rights to download the content."""
        if self.settings.user.skip_rights_check:
            return True

        if not self.settings.user.confirm_rights:
            return True

        self.console.print(f"\n[yellow]Content Information:[/yellow]")
        self.console.print(f"Title: {video_info.title}")
        self.console.print(f"Uploader: {video_info.uploader}")
        self.console.print(f"URL: {video_info.url}")
        
        if video_info.is_playlist:
            self.console.print(f"Playlist items: {video_info.playlist_count}")

        self.console.print("\n[yellow]Important:[/yellow] Only download content you own or have explicit permission to download.")
        self.console.print("This includes:")
        self.console.print("• Your own videos")
        self.console.print("• Content with Creative Commons license")
        self.console.print("• Content with explicit permission from the copyright holder")

        return confirm_rights("Do you confirm you have the rights to download this content?")

    def download_single(self, url: str, output_path: Optional[Path] = None) -> Path:
        """Download a single video."""
        video_info = self.get_video_info(url)
        
        if not self.validate_rights(video_info):
            raise RightsError("User does not confirm having rights to the content")

        # Override output path if provided
        if output_path:
            self.settings.download.output_dir = output_path.parent
            self.settings.download.output_template = output_path.name

        ydl_opts = self.settings.get_ytdlp_options()
        ydl_opts["progress_hooks"] = [ProgressHook(self.progress_callback)]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Return the expected output path
            output_file = self.settings.download.output_dir / self.settings.download.output_template
            return output_file
        except Exception as e:
            raise DownloadError(f"Download failed: {str(e)}")

    def download_playlist(
        self, 
        url: str, 
        max_items: Optional[int] = None,
        start_item: int = 1,
        end_item: Optional[int] = None
    ) -> List[Path]:
        """Download a playlist with limits."""
        if not self.settings.user.allow_playlist_download:
            raise RightsError("Playlist downloads are not allowed in settings")

        video_info = self.get_video_info(url)
        
        if not video_info.is_playlist:
            raise ValueError("URL is not a playlist")

        if not self.validate_rights(video_info):
            raise RightsError("User does not confirm having rights to the content")

        # Apply limits
        max_items = max_items or self.settings.user.max_playlist_items
        if end_item is None:
            end_item = min(start_item + max_items - 1, video_info.playlist_count)

        # Ensure we don't exceed playlist bounds
        start_item = max(1, start_item)
        end_item = min(end_item, video_info.playlist_count)

        logger.info(f"Downloading playlist items {start_item} to {end_item} of {video_info.playlist_count}")

        # Update settings for playlist
        self.settings.download.playlist_start = start_item
        self.settings.download.playlist_end = end_item

        ydl_opts = self.settings.get_ytdlp_options()
        
        downloaded_files: List[Path] = []

        def playlist_progress_hook(d: Dict[str, Any]) -> None:
            """Progress hook for playlist downloads."""
            if d["status"] == "downloading":
                # Show progress for individual items
                title = d.get("filename", "Unknown")
                if "playlist_index" in d:
                    title = f"[{d['playlist_index']}/{video_info.playlist_count}] {title}"
                logger.info(f"Downloading: {title}")
            elif d["status"] == "finished":
                filename = d.get("filename", "")
                if filename:
                    downloaded_files.append(Path(filename))
                    logger.info(f"Completed: {filename}")
            elif d["status"] == "error":
                logger.error(f"Download error: {d.get('error', 'Unknown error')}")
            
            if self.progress_callback:
                self.progress_callback(d)

        ydl_opts["progress_hooks"] = [playlist_progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return downloaded_files
        except Exception as e:
            raise DownloadError(f"Playlist download failed: {str(e)}")

    def list_formats(self, url: str) -> List[Dict[str, Any]]:
        """List available formats for a video."""
        video_info = self.get_video_info(url)
        return video_info.formats

    def extract_audio_only(self, url: str, output_path: Optional[Path] = None) -> Path:
        """Extract audio only from video."""
        # Temporarily modify settings for audio extraction
        original_extract_audio = self.settings.download.extract_audio
        self.settings.download.extract_audio = True

        try:
            return self.download_single(url, output_path)
        finally:
            self.settings.download.extract_audio = original_extract_audio

    def save_metadata(self, video_info: VideoInfo, output_dir: Path) -> Path:
        """Save video metadata to JSON file."""
        metadata_file = output_dir / f"{video_info.title}_metadata.json"
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(video_info.to_dict(), f, indent=2, ensure_ascii=False)
        
        return metadata_file

    def download_thumbnail(self, video_info: VideoInfo, output_dir: Path) -> Optional[Path]:
        """Download video thumbnail."""
        if not video_info.thumbnail:
            return None

        import requests
        
        thumbnail_url = video_info.thumbnail
        thumbnail_ext = Path(thumbnail_url).suffix or ".jpg"
        thumbnail_file = output_dir / f"{video_info.title}_thumbnail{thumbnail_ext}"

        try:
            response = requests.get(thumbnail_url, timeout=30)
            response.raise_for_status()
            
            with open(thumbnail_file, "wb") as f:
                f.write(response.content)
            
            return thumbnail_file
        except Exception as e:
            logger.error(f"Failed to download thumbnail: {str(e)}")
            return None

