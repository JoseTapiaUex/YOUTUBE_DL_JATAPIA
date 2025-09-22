# YTDL Helper

A CLI tool for downloading videos with yt-dlp, respecting copyright and user rights. This tool ensures that users only download content they own or have explicit permission to download.

## Features

- **Copyright Compliance**: Built-in rights confirmation to ensure legal downloads
- **Multiple Platforms**: Supports YouTube, Vimeo, Twitch, Instagram, TikTok, and more
- **Flexible Formats**: Download video, audio-only, or specific formats
- **Playlist Support**: Download playlists with configurable limits
- **Rich TUI**: Beautiful terminal interface with progress bars and colored output
- **Metadata Extraction**: Save video metadata, thumbnails, and descriptions
- **Configurable**: Extensive configuration options via environment variables or config files

## Installation

### Using pipx (Recommended)

```bash
pipx install ytdl-helper
```

### Using pip

```bash
pip install ytdl-helper
```

### From Source

```bash
git clone https://github.com/ytdl-helper/ytdl-helper.git
cd ytdl-helper
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Download a single video
ytdl-helper download https://youtube.com/watch?v=VIDEO_ID

# Download audio only
ytdl-helper download --audio-only https://youtube.com/watch?v=VIDEO_ID

# Get video information
ytdl-helper info https://youtube.com/watch?v=VIDEO_ID

# Interactive mode
ytdl-helper interactive
```

### Advanced Usage

```bash
# Download with specific format and output directory
ytdl-helper download \
  --format "best[height<=720]" \
  --output-dir /path/to/downloads \
  https://youtube.com/watch?v=VIDEO_ID

# Download playlist with limits
ytdl-helper download \
  --playlist \
  --max-items 5 \
  https://youtube.com/playlist?list=PLAYLIST_ID

# Save metadata and thumbnail
ytdl-helper download \
  --metadata \
  --output-dir ./downloads \
  https://youtube.com/watch?v=VIDEO_ID

# Extract audio in different format
ytdl-helper download \
  --audio-only \
  --audio-format wav \
  https://youtube.com/watch?v=VIDEO_ID
```

## Commands

### `download`

Download a video or audio from a URL.

**Options:**
- `--output-dir`, `-o`: Output directory (default: current directory)
- `--format`, `-f`: Video format (default: "best")
- `--audio-only`, `-a`: Extract audio only
- `--audio-format`: Audio format (default: "mp3")
- `--playlist`, `-p`: Allow playlist download
- `--max-items`, `-n`: Maximum playlist items (default: 10)
- `--metadata`, `-m`: Save metadata and thumbnail
- `--skip-rights-check`: Skip rights confirmation (not recommended)
- `--verbose`, `-v`: Verbose output
- `--quiet`, `-q`: Quiet mode

### `info`

Get information about a video without downloading.

**Options:**
- `--formats`, `-f`: Show available formats
- `--verbose`, `-v`: Verbose output

### `config`

Manage configuration settings.

**Options:**
- `--show`, `-s`: Show current configuration
- `--reset`, `-r`: Reset configuration to defaults
- `--config-file`, `-c`: Configuration file path

### `interactive`

Start interactive mode for guided downloads.

### `version`

Show version information.

## Configuration

### Environment Variables

All settings can be configured via environment variables with the `YTDL_` prefix:

```bash
export YTDL_OUTPUT_DIR="/path/to/downloads"
export YTDL_FORMAT="best[height<=720]"
export YTDL_AUDIO_FORMAT="mp3"
export YTDL_MAX_PLAYLIST_ITEMS=10
export YTDL_CONFIRM_RIGHTS=true
export YTDL_VERBOSE=false
```

### Configuration File

Create a configuration file at `~/.config/ytdl-helper/config.json`:

```json
{
  "download": {
    "format": "best[height<=720]",
    "output_dir": "/path/to/downloads",
    "extract_audio": false,
    "audio_format": "mp3"
  },
  "metadata": {
    "write_info_json": true,
    "write_thumbnail": true,
    "write_description": false
  },
  "user": {
    "confirm_rights": true,
    "max_playlist_items": 10,
    "allow_playlist_download": false
  }
}
```

## Supported Platforms

- YouTube
- Vimeo
- Twitch
- Instagram
- TikTok
- Twitter/X
- Facebook
- SoundCloud
- Bandcamp
- Archive.org
- And many more (via yt-dlp)

## Format Options

### Video Formats

- `best`: Best quality available
- `worst`: Worst quality available
- `best[height<=720]`: Best quality up to 720p
- `bestvideo+bestaudio`: Best video and audio separately
- `mp4`: MP4 format only
- `webm`: WebM format only

### Audio Formats

- `mp3`: MP3 audio
- `wav`: WAV audio
- `flac`: FLAC audio
- `aac`: AAC audio
- `m4a`: M4A audio

## Copyright Notice

**IMPORTANT**: This tool is designed to respect copyright laws. Only download content that you:

- Own yourself
- Have explicit permission to download
- Is licensed under Creative Commons or similar open licenses

The tool includes built-in rights confirmation to help ensure legal compliance. Do not use this tool to download copyrighted content without permission.

## Examples

### Download Your Own YouTube Video

```bash
ytdl-helper download https://youtube.com/watch?v=YOUR_VIDEO_ID
```

### Download Creative Commons Content

```bash
ytdl-helper download \
  --metadata \
  https://youtube.com/watch?v=CC_VIDEO_ID
```

### Extract Audio from Your Content

```bash
ytdl-helper download \
  --audio-only \
  --audio-format mp3 \
  https://youtube.com/watch?v=YOUR_VIDEO_ID
```

### Download Limited Playlist

```bash
ytdl-helper download \
  --playlist \
  --max-items 3 \
  https://youtube.com/playlist?list=YOUR_PLAYLIST_ID
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/ytdl-helper/ytdl-helper.git
cd ytdl-helper
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Linting

```bash
ruff check src/ tests/
mypy src/ tests/
```

### Build Package

```bash
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and linting
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and personal use only. Users are responsible for ensuring they have the legal right to download any content. The developers are not responsible for any misuse of this tool.

## Support

- **Issues**: [GitHub Issues](https://github.com/ytdl-helper/ytdl-helper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ytdl-helper/ytdl-helper/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/ytdl-helper/ytdl-helper/wiki)