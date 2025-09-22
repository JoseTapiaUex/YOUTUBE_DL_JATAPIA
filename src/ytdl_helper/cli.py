"""Command Line Interface using Typer."""

import sys
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ytdl_helper.config import Settings
from ytdl_helper.core import VideoDownloader, DownloadError, RightsError
from ytdl_helper.tui import InteractiveTUI
from ytdl_helper.utils import validate_url, print_error, print_success, print_warning

app = typer.Typer(
    name="ytdl-helper",
    help="A CLI tool for downloading videos with yt-dlp, respecting copyright",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
tui = InteractiveTUI(console)


@app.command()
def download(
    url: Annotated[str, typer.Argument(help="Video URL to download")],
    output_dir: Annotated[Optional[Path], typer.Option(
        "--output-dir", "-o", help="Output directory"
    )] = None,
    format: Annotated[str, typer.Option(
        "--format", "-f", help="Video format (best, worst, mp4, etc.)"
    )] = "best",
    audio_only: Annotated[bool, typer.Option(
        "--audio-only", "-a", help="Extract audio only"
    )] = False,
    audio_format: Annotated[str, typer.Option(
        "--audio-format", help="Audio format (mp3, wav, etc.)"
    )] = "mp3",
    playlist: Annotated[bool, typer.Option(
        "--playlist", "-p", help="Allow playlist download"
    )] = False,
    max_items: Annotated[int, typer.Option(
        "--max-items", "-n", help="Maximum number of playlist items"
    )] = 10,
    metadata: Annotated[bool, typer.Option(
        "--metadata", "-m", help="Save metadata and thumbnail"
    )] = False,
    skip_rights_check: Annotated[bool, typer.Option(
        "--skip-rights-check", help="Skip rights confirmation (not recommended)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Verbose output"
    )] = False,
    quiet: Annotated[bool, typer.Option(
        "--quiet", "-q", help="Quiet mode"
    )] = False,
) -> None:
    """Download a video or audio from URL."""
    try:
        # Validate URL
        if not validate_url(url):
            print_error("Invalid URL provided")
            raise typer.Exit(1)

        # Create settings
        settings = Settings()
        settings.verbose = verbose
        settings.quiet = quiet
        settings.user.skip_rights_check = skip_rights_check
        settings.user.allow_playlist_download = playlist
        settings.user.max_playlist_items = max_items
        
        if output_dir:
            settings.download.output_dir = output_dir
        if format != "best":
            settings.download.format = format
        if audio_only:
            settings.download.extract_audio = True
            settings.download.audio_format = audio_format
        if metadata:
            settings.metadata.write_info_json = True
            settings.metadata.write_thumbnail = True

        # Create downloader
        downloader = VideoDownloader(settings)

        # Set up progress callback
        def progress_callback(data: dict) -> None:
            if not quiet:
                tui.progress.update_progress(data)

        downloader.set_progress_callback(progress_callback)

        # Check if it's a playlist
        if playlist or downloader.get_video_info(url).is_playlist:
            if not playlist:
                print_warning("URL appears to be a playlist. Use --playlist flag to download.")
                raise typer.Exit(1)
            
            # Download playlist
            if not quiet:
                tui.show_welcome()
                tui.progress.start_download("Playlist")
            
            try:
                downloaded_files = downloader.download_playlist(url, max_items)
                if not quiet:
                    tui.progress.finish_download()
                    tui.info_display.show_download_summary(downloaded_files)
                print_success(f"Downloaded {len(downloaded_files)} files from playlist")
            except RightsError as e:
                if not quiet:
                    tui.progress.show_error(str(e))
                print_error(str(e))
                raise typer.Exit(1)
        else:
            # Download single video
            if not quiet:
                tui.show_welcome()
                video_info = downloader.get_video_info(url)
                tui.info_display.show_video_info(video_info)
                tui.info_display.show_rights_warning()
                
                if not downloader.validate_rights(video_info):
                    print_error("Rights confirmation required")
                    raise typer.Exit(1)
                
                tui.progress.start_download(video_info.title)
            
            try:
                downloaded_file = downloader.download_single(url)
                if not quiet:
                    tui.progress.finish_download()
                    tui.info_display.show_download_summary([downloaded_file])
                print_success(f"Downloaded: {downloaded_file}")
            except RightsError as e:
                if not quiet:
                    tui.progress.show_error(str(e))
                print_error(str(e))
                raise typer.Exit(1)

    except DownloadError as e:
        if not quiet:
            tui.show_error("Download failed", str(e))
        print_error(f"Download failed: {str(e)}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        if not quiet:
            tui.show_error("Download cancelled by user")
        print_error("Download cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        if not quiet:
            tui.show_error("Unexpected error", str(e))
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def info(
    url: Annotated[str, typer.Argument(help="Video URL to get information")],
    formats: Annotated[bool, typer.Option(
        "--formats", "-f", help="Show available formats"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Verbose output"
    )] = False,
) -> None:
    """Get information about a video."""
    try:
        # Validate URL
        if not validate_url(url):
            print_error("Invalid URL provided")
            raise typer.Exit(1)

        # Create downloader
        settings = Settings()
        settings.verbose = verbose
        downloader = VideoDownloader(settings)

        # Get video info
        video_info = downloader.get_video_info(url)
        
        # Display information
        tui.show_welcome()
        tui.info_display.show_video_info(video_info)
        
        if formats:
            available_formats = downloader.list_formats(url)
            tui.info_display.show_formats_table(available_formats)

    except DownloadError as e:
        tui.show_error("Failed to get video information", str(e))
        print_error(f"Failed to get video information: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        tui.show_error("Unexpected error", str(e))
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def playlist(
    url: Annotated[str, typer.Argument(help="Playlist URL to download")],
    output_dir: Annotated[Optional[Path], typer.Option(
        "--output-dir", "-o", help="Output directory"
    )] = None,
    max_items: Annotated[int, typer.Option(
        "--max-items", "-n", help="Maximum number of items to download"
    )] = 10,
    start_item: Annotated[int, typer.Option(
        "--start", "-s", help="Start downloading from this item number"
    )] = 1,
    end_item: Annotated[Optional[int], typer.Option(
        "--end", "-e", help="Stop downloading at this item number"
    )] = None,
    format: Annotated[str, typer.Option(
        "--format", "-f", help="Video format (best, worst, mp4, etc.)"
    )] = "best",
    audio_only: Annotated[bool, typer.Option(
        "--audio-only", "-a", help="Extract audio only"
    )] = False,
    audio_format: Annotated[str, typer.Option(
        "--audio-format", help="Audio format (mp3, wav, etc.)"
    )] = "mp3",
    metadata: Annotated[bool, typer.Option(
        "--metadata", "-m", help="Save metadata and thumbnail"
    )] = False,
    skip_rights_check: Annotated[bool, typer.Option(
        "--skip-rights-check", help="Skip rights confirmation (not recommended)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Verbose output"
    )] = False,
    quiet: Annotated[bool, typer.Option(
        "--quiet", "-q", help="Quiet mode"
    )] = False,
) -> None:
    """Download a playlist from URL."""
    try:
        # Validate URL
        if not validate_url(url):
            print_error("Invalid URL provided")
            raise typer.Exit(1)

        # Create settings
        settings = Settings()
        settings.verbose = verbose
        settings.quiet = quiet
        settings.user.skip_rights_check = skip_rights_check
        settings.user.allow_playlist_download = True
        settings.user.max_playlist_items = max_items
        
        if output_dir:
            settings.download.output_dir = output_dir
        if format != "best":
            settings.download.format = format
        if audio_only:
            settings.download.extract_audio = True
            settings.download.audio_format = audio_format
        if metadata:
            settings.metadata.write_info_json = True
            settings.metadata.write_thumbnail = True

        # Create downloader
        downloader = VideoDownloader(settings)

        # Set up progress callback
        def progress_callback(data: dict) -> None:
            if not quiet:
                tui.progress.update_progress(data)

        downloader.set_progress_callback(progress_callback)

        # Get playlist info first
        if not quiet:
            tui.show_welcome()
            
        playlist_info = downloader.get_video_info(url)
        
        if not playlist_info.is_playlist:
            print_error("URL is not a playlist")
            raise typer.Exit(1)
            
        if not quiet:
            tui.info_display.show_video_info(playlist_info)
            tui.info_display.show_rights_warning()
            
            if not downloader.validate_rights(playlist_info):
                print_error("Rights confirmation required")
                raise typer.Exit(1)
                
            tui.progress.start_download(f"Playlist: {playlist_info.title}")
        
        try:
            downloaded_files = downloader.download_playlist(
                url, 
                max_items=max_items,
                start_item=start_item,
                end_item=end_item
            )
            
            if not quiet:
                tui.progress.finish_download()
                tui.info_display.show_download_summary(downloaded_files)
                
            print_success(f"Downloaded {len(downloaded_files)} files from playlist")
            
        except RightsError as e:
            if not quiet:
                tui.progress.show_error(str(e))
            print_error(str(e))
            raise typer.Exit(1)

    except DownloadError as e:
        if not quiet:
            tui.show_error("Download failed", str(e))
        print_error(f"Download failed: {str(e)}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        if not quiet:
            tui.show_error("Download cancelled by user")
        print_error("Download cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        if not quiet:
            tui.show_error("Unexpected error", str(e))
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def config(
    show: Annotated[bool, typer.Option(
        "--show", "-s", help="Show current configuration"
    )] = False,
    reset: Annotated[bool, typer.Option(
        "--reset", "-r", help="Reset configuration to defaults"
    )] = False,
    config_file: Annotated[Optional[Path], typer.Option(
        "--config-file", "-c", help="Configuration file path"
    )] = None,
) -> None:
    """Manage configuration settings."""
    try:
        if show:
            settings = Settings()
            console.print("[bold blue]Current Configuration:[/bold blue]")
            console.print(settings.model_dump_json(indent=2))
        
        elif reset:
            settings = Settings()
            config_path = config_file or Path.home() / ".config" / "ytdl-helper" / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            settings.save_to_file(config_path)
            print_success(f"Configuration reset to defaults and saved to {config_path}")
        
        else:
            tui.show_help()
            console.print("\n[bold]Configuration Options:[/bold]")
            console.print("• Use --show to display current configuration")
            console.print("• Use --reset to reset configuration to defaults")
            console.print("• Environment variables: YTDL_* (e.g., YTDL_OUTPUT_DIR)")

    except Exception as e:
        tui.show_error("Configuration error", str(e))
        print_error(f"Configuration error: {str(e)}")
        raise typer.Exit(1)


@app.command()
def interactive() -> None:
    """Start interactive mode."""
    try:
        tui.show_welcome()
        tui.show_help()
        
        while True:
            console.print("\n[bold blue]Interactive Mode[/bold blue]")
            
            # Get URL from user
            url = Prompt.ask("Enter video URL (or 'quit' to exit)")
            
            if url.lower() in ['quit', 'exit', 'q']:
                console.print("[green]Goodbye![/green]")
                break
            
            if not validate_url(url):
                print_error("Invalid URL")
                continue
            
            # Ask what to do
            action = Prompt.ask(
                "What would you like to do?",
                choices=["info", "download", "formats", "back"],
                default="info"
            )
            
            if action == "back":
                continue
            
            # Get video info
            try:
                settings = Settings()
                downloader = VideoDownloader(settings)
                video_info = downloader.get_video_info(url)
                
                if action == "info":
                    tui.info_display.show_video_info(video_info)
                
                elif action == "formats":
                    formats = downloader.list_formats(url)
                    tui.info_display.show_formats_table(formats)
                
                elif action == "download":
                    tui.info_display.show_video_info(video_info)
                    tui.info_display.show_rights_warning()
                    
                    if downloader.validate_rights(video_info):
                        audio_only = Confirm.ask("Extract audio only?", default=False)
                        save_metadata = Confirm.ask("Save metadata and thumbnail?", default=False)
                        
                        if audio_only:
                            settings.download.extract_audio = True
                        if save_metadata:
                            settings.metadata.write_info_json = True
                            settings.metadata.write_thumbnail = True
                        
                        downloader.settings = settings
                        
                        def progress_callback(data: dict) -> None:
                            tui.progress.update_progress(data)
                        
                        downloader.set_progress_callback(progress_callback)
                        tui.progress.start_download(video_info.title)
                        
                        try:
                            downloaded_file = downloader.download_single(url)
                            tui.progress.finish_download()
                            tui.info_display.show_download_summary([downloaded_file])
                            print_success(f"Downloaded: {downloaded_file}")
                        except Exception as e:
                            tui.progress.show_error(str(e))
                            print_error(f"Download failed: {str(e)}")
                    
                    else:
                        print_error("Rights confirmation required")

            except Exception as e:
                tui.show_error("Error", str(e))
                print_error(f"Error: {str(e)}")

    except KeyboardInterrupt:
        console.print("\n[green]Goodbye![/green]")
    except Exception as e:
        tui.show_error("Interactive mode error", str(e))
        print_error(f"Interactive mode error: {str(e)}")


@app.command()
def version() -> None:
    """Show version information."""
    from ytdl_helper import __version__
    console.print(f"[bold blue]ytdl-helper[/bold blue] version [green]{__version__}[/green]")


def main() -> None:
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()

