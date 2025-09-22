"""Terminal User Interface using Rich."""

import time
from typing import Any, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.text import Text

from ytdl_helper.utils import format_duration, format_file_size


class DownloadProgress:
    """Progress display for downloads."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize progress display."""
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
        )
        self.task_id: Optional[str] = None
        self.live: Optional[Live] = None

    def start_download(self, filename: str) -> None:
        """Start progress display for download."""
        self.task_id = self.progress.add_task(
            f"Downloading {filename}",
            total=100,
        )
        
        self.live = Live(
            Panel(self.progress, title="Download Progress", border_style="blue"),
            console=self.console,
            refresh_per_second=4,
        )
        self.live.start()

    def update_progress(self, progress_data: Dict[str, Any]) -> None:
        """Update progress from yt-dlp hook."""
        if not self.task_id or not self.live:
            return

        # Extract progress information
        downloaded = progress_data.get("downloaded_bytes", 0)
        total = progress_data.get("total_bytes", 0)
        speed = progress_data.get("speed", 0)
        
        if total > 0:
            percentage = (downloaded / total) * 100
            self.progress.update(
                self.task_id,
                completed=percentage,
                total=100,
                downloaded=format_file_size(downloaded),
                total_size=format_file_size(total),
                speed=format_file_size(speed) + "/s",
            )

    def finish_download(self) -> None:
        """Finish progress display."""
        if self.live:
            self.live.stop()
            self.live = None
        
        if self.task_id:
            self.progress.update(self.task_id, completed=100)
            self.task_id = None

    def show_error(self, error_message: str) -> None:
        """Show error message."""
        if self.live:
            self.live.stop()
            self.live = None
        
        self.console.print(f"[red]Download Error: {error_message}[/red]")


class VideoInfoDisplay:
    """Display video information in TUI."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize display."""
        self.console = console or Console()

    def show_video_info(self, video_info: Any) -> None:
        """Show video information in a panel."""
        # Create info text
        info_lines = [
            f"[bold]Title:[/bold] {video_info.title}",
            f"[bold]Uploader:[/bold] {video_info.uploader}",
            f"[bold]Duration:[/bold] {format_duration(video_info.duration)}",
            f"[bold]Upload Date:[/bold] {video_info.upload_date}",
            f"[bold]View Count:[/bold] {video_info.view_count:,}",
        ]
        
        if video_info.is_playlist:
            info_lines.append(f"[bold]Playlist Items:[/bold] {video_info.playlist_count}")
        
        info_text = "\n".join(info_lines)
        
        # Create panel
        panel = Panel(
            info_text,
            title="[bold blue]Video Information[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_formats_table(self, formats: list) -> None:
        """Show available formats in a table."""
        if not formats:
            self.console.print("[yellow]No formats available[/yellow]")
            return

        table = Table(title="Available Formats")
        table.add_column("Format ID", style="cyan", width=10)
        table.add_column("Extension", style="green", width=8)
        table.add_column("Quality", style="yellow", width=10)
        table.add_column("Size", style="magenta", width=12)
        table.add_column("Codec", style="blue", width=15)
        table.add_column("Note", style="dim", width=20)

        # Show only first 15 formats to avoid clutter
        for fmt in formats[:15]:
            format_id = fmt.get("format_id", "unknown")
            ext = fmt.get("ext", "unknown")
            quality = fmt.get("quality", "unknown")
            filesize = fmt.get("filesize", 0)
            codec = fmt.get("codec", "unknown")
            note = fmt.get("format_note", "")

            size_str = format_file_size(filesize) if filesize else "Unknown"
            
            # Truncate long notes
            if len(note) > 20:
                note = note[:17] + "..."

            table.add_row(
                format_id,
                ext,
                str(quality),
                size_str,
                codec,
                note,
            )

        self.console.print(table)

    def show_rights_warning(self) -> None:
        """Show copyright warning."""
        warning_text = """
[bold red]IMPORTANT: COPYRIGHT NOTICE[/bold red]

[yellow]Only download content that you own or have explicit permission to download.[/yellow]

This includes:
• Your own videos
• Content with Creative Commons license
• Content with explicit permission from the copyright holder

[red]Do not download copyrighted content without permission![/red]
        """.strip()

        panel = Panel(
            warning_text,
            title="[bold red]Copyright Warning[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_download_summary(self, downloaded_files: list) -> None:
        """Show download summary."""
        if not downloaded_files:
            return

        summary_lines = [
            f"[bold green]Successfully downloaded {len(downloaded_files)} file(s):[/bold green]",
            ""
        ]
        
        for file_path in downloaded_files:
            summary_lines.append(f"• {file_path}")

        summary_text = "\n".join(summary_lines)
        
        panel = Panel(
            summary_text,
            title="[bold green]Download Complete[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        
        self.console.print(panel)


class InteractiveTUI:
    """Interactive Terminal User Interface."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize TUI."""
        self.console = console or Console()
        self.progress = DownloadProgress(self.console)
        self.info_display = VideoInfoDisplay(self.console)

    def show_welcome(self) -> None:
        """Show welcome message."""
        welcome_text = """
[bold blue]YTDL Helper[/bold blue] - Video Downloader

A CLI tool for downloading videos with yt-dlp,
respecting copyright and user rights.
        """.strip()

        panel = Panel(
            welcome_text,
            title="[bold blue]Welcome[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold]Usage Examples:[/bold]

[cyan]Download single video:[/cyan]
  ytdl-helper download https://youtube.com/watch?v=VIDEO_ID

[cyan]Download audio only:[/cyan]
  ytdl-helper download --audio-only https://youtube.com/watch?v=VIDEO_ID

[cyan]List available formats:[/cyan]
  ytdl-helper info https://youtube.com/watch?v=VIDEO_ID

[cyan]Download playlist (limited):[/cyan]
  ytdl-helper download --playlist --max-items 5 https://youtube.com/playlist?list=PLAYLIST_ID

[bold]Options:[/bold]
  --output-dir PATH     Output directory
  --format FORMAT       Video format (best, worst, mp4, etc.)
  --audio-only          Extract audio only
  --audio-format FORMAT Audio format (mp3, wav, etc.)
  --metadata            Save metadata and thumbnail
  --help                Show this help
        """.strip()

        panel = Panel(
            help_text,
            title="[bold blue]Help[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_error(self, error_message: str, details: Optional[str] = None) -> None:
        """Show error message."""
        error_content = f"[bold red]{error_message}[/bold red]"
        
        if details:
            error_content += f"\n\n[dim]{details}[/dim]"

        panel = Panel(
            error_content,
            title="[bold red]Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_success(self, message: str) -> None:
        """Show success message."""
        panel = Panel(
            f"[bold green]{message}[/bold green]",
            title="[bold green]Success[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        
        self.console.print(panel)

    def show_loading(self, message: str) -> None:
        """Show loading spinner."""
        with self.console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
            time.sleep(0.1)  # Just to show the spinner

    def clear_screen(self) -> None:
        """Clear the screen."""
        self.console.clear()

    def pause(self) -> None:
        """Pause for user input."""
        self.console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

