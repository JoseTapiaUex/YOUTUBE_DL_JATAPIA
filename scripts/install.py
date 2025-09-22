#!/usr/bin/env python3
"""Installation script for ytdl-helper."""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main() -> None:
    """Main installation process."""
    print("🚀 Installing ytdl-helper...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -e .", "Installing ytdl-helper"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Installation failed at: {description}")
            sys.exit(1)
    
    # Verify installation
    print("🔍 Verifying installation...")
    try:
        import ytdl_helper
        print(f"✅ ytdl-helper {ytdl_helper.__version__} installed successfully")
    except ImportError as e:
        print(f"❌ Installation verification failed: {e}")
        sys.exit(1)
    
    # Test CLI
    try:
        result = subprocess.run(
            ["ytdl-helper", "--help"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print("✅ CLI command works correctly")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ CLI verification failed: {e}")
        print("Note: You may need to restart your terminal or add the installation directory to PATH")
    
    print("\n🎉 Installation completed!")
    print("\nUsage examples:")
    print("  ytdl-helper download https://youtube.com/watch?v=VIDEO_ID")
    print("  ytdl-helper info https://youtube.com/watch?v=VIDEO_ID")
    print("  ytdl-helper interactive")
    print("\nFor more information, run: ytdl-helper --help")


if __name__ == "__main__":
    main()

