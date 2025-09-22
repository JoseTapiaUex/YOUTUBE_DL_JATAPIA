"""Utility functions for ytdl-helper."""

import re
import sys
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table


def validate_url(url: str) -> bool:
    """Validate if URL is supported by yt-dlp."""
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
    except Exception:
        return False

    # Common video platform patterns
    supported_patterns = [
        r"youtube\.com",
        r"youtu\.be",
        r"vimeo\.com",
        r"dailymotion\.com",
        r"twitch\.tv",
        r"instagram\.com",
        r"tiktok\.com",
        r"twitter\.com",
        r"x\.com",
        r"facebook\.com",
        r"soundcloud\.com",
        r"bandcamp\.com",
        r"archive\.org",
    ]

    # Check if URL matches any supported platform
    for pattern in supported_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True

    # For other URLs, assume they might be supported
    return True


def confirm_rights(message: str = "Do you confirm you have the rights to download this content?") -> bool:
    """Ask user to confirm they have rights to the content."""
    console = Console()
    return Confirm.ask(message, default=False)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}h {minutes}m {remaining_seconds}s"


def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem compatibility."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32 or char in '\t\n\r')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    return filename


def create_output_path(
    output_dir: Path,
    template: str,
    title: str,
    extension: str,
    uploader: Optional[str] = None,
    upload_date: Optional[str] = None
) -> Path:
    """Create output path from template and variables."""
    # Sanitize variables
    safe_title = sanitize_filename(title)
    safe_uploader = sanitize_filename(uploader) if uploader else "Unknown"
    safe_date = upload_date or "Unknown"
    
    # Replace template variables
    filename = template
    filename = filename.replace("%(title)s", safe_title)
    filename = filename.replace("%(uploader)s", safe_uploader)
    filename = filename.replace("%(upload_date)s", safe_date)
    filename = filename.replace("%(ext)s", extension)
    
    # Ensure extension is present
    if not filename.endswith(f".{extension}"):
        filename += f".{extension}"
    
    return output_dir / filename


def display_video_info_table(video_info, console: Optional[Console] = None) -> None:
    """Display video information in a nice table."""
    if console is None:
        console = Console()
    
    table = Table(title="Video Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Title", video_info.title)
    table.add_row("Uploader", video_info.uploader)
    table.add_row("Duration", format_duration(video_info.duration))
    table.add_row("Upload Date", video_info.upload_date)
    table.add_row("View Count", f"{video_info.view_count:,}")
    table.add_row("URL", video_info.url)
    
    if video_info.is_playlist:
        table.add_row("Type", f"Playlist ({video_info.playlist_count} items)")
    else:
        table.add_row("Type", "Single Video")
    
    console.print(table)


def display_formats_table(formats: List[dict], console: Optional[Console] = None) -> None:
    """Display available formats in a table."""
    if console is None:
        console = Console()
    
    if not formats:
        console.print("[yellow]No formats available[/yellow]")
        return
    
    table = Table(title="Available Formats")
    table.add_column("Format ID", style="cyan")
    table.add_column("Extension", style="green")
    table.add_column("Quality", style="yellow")
    table.add_column("Size", style="magenta")
    table.add_column("Codec", style="blue")
    
    for fmt in formats[:20]:  # Limit to first 20 formats
        format_id = fmt.get("format_id", "unknown")
        ext = fmt.get("ext", "unknown")
        quality = fmt.get("quality", "unknown")
        filesize = fmt.get("filesize", 0)
        codec = fmt.get("codec", "unknown")
        
        size_str = format_file_size(filesize) if filesize else "Unknown"
        
        table.add_row(format_id, ext, str(quality), size_str, codec)
    
    console.print(table)


def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default."""
    return Prompt.ask(prompt, default=default or "")


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_playlist_url(url: str) -> bool:
    """Check if URL is likely a playlist."""
    playlist_indicators = [
        "/playlist",
        "/channel/",
        "/user/",
        "/c/",
        "/@",
        "list=",
    ]
    
    return any(indicator in url.lower() for indicator in playlist_indicators)


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from URL."""
    # YouTube playlist
    if "youtube.com" in url or "youtu.be" in url:
        match = re.search(r'[?&]list=([^&]+)', url)
        if match:
            return match.group(1)
    
    # Other platforms might have different patterns
    # This is a simplified implementation
    return None


def validate_output_path(path: Path) -> bool:
    """Validate output path is writable."""
    try:
        # Check if parent directory exists and is writable
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to create a test file
        test_file = path.parent / ".ytdl_test"
        test_file.touch()
        test_file.unlink()
        
        return True
    except Exception:
        return False


def get_safe_filename(title: str, extension: str = "") -> str:
    """Get a safe filename from title."""
    safe_title = sanitize_filename(title)
    
    if extension and not safe_title.endswith(f".{extension}"):
        safe_title += f".{extension}"
    
    return safe_title


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def print_error(message: str, console: Optional[Console] = None) -> None:
    """Print error message in red."""
    if console is None:
        console = Console()
    console.print(f"[red]Error: {message}[/red]")


def print_success(message: str, console: Optional[Console] = None) -> None:
    """Print success message in green."""
    if console is None:
        console = Console()
    console.print(f"[green]Success: {message}[/green]")


def print_warning(message: str, console: Optional[Console] = None) -> None:
    """Print warning message in yellow."""
    if console is None:
        console = Console()
    console.print(f"[yellow]Warning: {message}[/yellow]")


def print_info(message: str, console: Optional[Console] = None) -> None:
    """Print info message in blue."""
    if console is None:
        console = Console()
    console.print(f"[blue]Info: {message}[/blue]")

