#!/usr/bin/env python3
"""Example usage of ytdl-helper."""

from pathlib import Path
from ytdl_helper import VideoDownloader, Settings


def main() -> None:
    """Example usage of the ytdl-helper library."""
    
    # Create custom settings
    settings = Settings()
    settings.download.output_dir = Path("./downloads")
    settings.download.extract_audio = False
    settings.metadata.write_info_json = True
    settings.metadata.write_thumbnail = True
    settings.user.max_playlist_items = 5
    
    # Create downloader
    downloader = VideoDownloader(settings)
    
    # Example URLs (replace with actual URLs you have rights to)
    test_urls = [
        "https://youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with your own video
        # "https://youtube.com/playlist?list=PLrAXtmRdnEQy5nCwNwzMp8",  # Replace with your own playlist
    ]
    
    for url in test_urls:
        try:
            print(f"\nProcessing: {url}")
            
            # Get video information
            video_info = downloader.get_video_info(url)
            print(f"Title: {video_info.title}")
            print(f"Uploader: {video_info.uploader}")
            print(f"Duration: {video_info.duration} seconds")
            print(f"Is playlist: {video_info.is_playlist}")
            
            if video_info.is_playlist:
                print(f"Playlist items: {video_info.playlist_count}")
            
            # Validate rights (in real usage, this would prompt the user)
            if downloader.validate_rights(video_info):
                print("Rights confirmed, proceeding with download...")
                
                if video_info.is_playlist:
                    # Download playlist
                    downloaded_files = downloader.download_playlist(url)
                    print(f"Downloaded {len(downloaded_files)} files from playlist")
                else:
                    # Download single video
                    downloaded_file = downloader.download_single(url)
                    print(f"Downloaded: {downloaded_file}")
                    
                    # Save metadata if enabled
                    if settings.metadata.write_info_json:
                        metadata_file = downloader.save_metadata(video_info, settings.download.output_dir)
                        print(f"Metadata saved to: {metadata_file}")
                    
                    # Download thumbnail if enabled
                    if settings.metadata.write_thumbnail:
                        thumbnail_file = downloader.download_thumbnail(video_info, settings.download.output_dir)
                        if thumbnail_file:
                            print(f"Thumbnail saved to: {thumbnail_file}")
            else:
                print("Rights not confirmed, skipping download")
                
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")


if __name__ == "__main__":
    main()

