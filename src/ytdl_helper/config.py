"""Configuration management using Pydantic Settings."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DownloadSettings(BaseModel):
    """Settings for video/audio download."""

    format: str = Field(default="best", description="Download format")
    output_template: str = Field(
        default="%(title)s.%(ext)s", description="Output filename template"
    )
    output_dir: Path = Field(default=Path.cwd(), description="Output directory")
    extract_audio: bool = Field(default=False, description="Extract audio only")
    audio_format: str = Field(default="mp3", description="Audio format")
    video_format: str = Field(default="mp4", description="Video format")
    quality: str = Field(default="best", description="Quality preference")
    max_filesize: Optional[str] = Field(default=None, description="Maximum file size")
    max_duration: Optional[int] = Field(default=None, description="Maximum duration in seconds")
    playlist_items: Optional[str] = Field(default=None, description="Playlist items to download")
    playlist_end: Optional[int] = Field(default=None, description="Last playlist item")
    playlist_start: Optional[int] = Field(default=1, description="First playlist item")

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate format string."""
        if not v:
            raise ValueError("Format cannot be empty")
        return v


class MetadataSettings(BaseModel):
    """Settings for metadata extraction."""

    write_info_json: bool = Field(default=False, description="Write metadata to JSON file")
    write_thumbnail: bool = Field(default=False, description="Download thumbnail")
    write_description: bool = Field(default=False, description="Write video description")
    write_annotations: bool = Field(default=False, description="Write annotations")
    write_subtitles: bool = Field(default=False, description="Download subtitles")
    subtitle_langs: List[str] = Field(default=["en"], description="Subtitle languages")


class UserSettings(BaseModel):
    """User confirmation and rights settings."""

    confirm_rights: bool = Field(default=True, description="Require rights confirmation")
    skip_rights_check: bool = Field(default=False, description="Skip rights confirmation")
    max_playlist_items: int = Field(default=10, description="Maximum playlist items")
    allow_playlist_download: bool = Field(default=True, description="Allow playlist downloads")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="YTDL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Download settings
    download: DownloadSettings = Field(default_factory=DownloadSettings)

    # Metadata settings
    metadata: MetadataSettings = Field(default_factory=MetadataSettings)

    # User settings
    user: UserSettings = Field(default_factory=UserSettings)

    # yt-dlp specific settings
    verbose: bool = Field(default=False, description="Verbose output")
    quiet: bool = Field(default=False, description="Quiet mode")
    no_warnings: bool = Field(default=False, description="Suppress warnings")
    ignore_errors: bool = Field(default=False, description="Ignore download errors")
    retries: int = Field(default=3, description="Number of retries")
    fragment_retries: int = Field(default=10, description="Fragment retries")
    buffer_size: int = Field(default=1024, description="Buffer size")
    http_chunk_size: int = Field(default=1048576, description="HTTP chunk size")

    # Cache and temporary files
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ytdl-helper")
    temp_dir: Optional[Path] = Field(default=None, description="Temporary directory")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization setup."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.temp_dir:
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_ytdlp_options(self) -> Dict[str, Any]:
        """Get yt-dlp options dictionary."""
        options = {
            "format": self.download.format,
            "outtmpl": str(self.download.output_dir / self.download.output_template),
            "retries": self.retries,
            "fragment_retries": self.fragment_retries,
            "buffersize": self.buffer_size,
            "http_chunk_size": self.http_chunk_size,
            "quiet": self.quiet,
            "no_warnings": self.no_warnings,
            "ignoreerrors": self.ignore_errors,
        }

        # Audio extraction
        if self.download.extract_audio:
            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.download.audio_format,
                    "preferredquality": "192",
                }],
            })

        # File size and duration limits
        if self.download.max_filesize:
            options["max_filesize"] = self.download.max_filesize
        if self.download.max_duration:
            options["max_duration"] = self.download.max_duration

        # Playlist settings
        if self.download.playlist_items:
            options["playlist_items"] = self.download.playlist_items
        if self.download.playlist_start:
            options["playliststart"] = self.download.playlist_start
        if self.download.playlist_end:
            options["playlistend"] = self.download.playlist_end

        # Metadata settings
        if self.metadata.write_info_json:
            options["writeinfojson"] = True
        if self.metadata.write_thumbnail:
            options["writethumbnail"] = True
        if self.metadata.write_description:
            options["writedescription"] = True
        if self.metadata.write_annotations:
            options["writeannotations"] = True
        if self.metadata.write_subtitles:
            options["writesubtitles"] = True
            options["subtitleslangs"] = self.metadata.subtitle_langs

        # Cache directory
        options["cachedir"] = str(self.cache_dir)

        return options

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

    def save_to_file(self, file_path: Path) -> None:
        """Save settings to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, file_path: Path) -> "Settings":
        """Load settings from a JSON file."""
        if not file_path.exists():
            return cls()
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read()
        return cls.model_validate_json(data)

