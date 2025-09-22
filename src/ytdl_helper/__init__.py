"""YTDL Helper - A CLI tool for downloading videos with yt-dlp."""

__version__ = "0.1.0"
__author__ = "YTDL Helper Team"
__email__ = "team@ytdl-helper.dev"

from ytdl_helper.cli import app
from ytdl_helper.core import VideoDownloader
from ytdl_helper.config import Settings

__all__ = ["app", "VideoDownloader", "Settings"]

