"""
Path resolution utilities for Audio Transcriber.
Handles paths correctly in both development mode and PyInstaller bundles.
"""

import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """
    Get the base directory for bundled/read-only resources.
    In PyInstaller: _MEIPASS (where bundled files are extracted)
    In dev: the project root directory
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_data_dir() -> Path:
    """
    Get the writable data directory for user data (databases, clips, etc).
    In PyInstaller: ~/Library/Application Support/AudioTranscriber/
    In dev: ./data/ (project root)
    """
    if hasattr(sys, '_MEIPASS'):
        app_support = Path.home() / "Library" / "Application Support" / "AudioTranscriber"
    else:
        app_support = Path(__file__).resolve().parent / "data"
    app_support.mkdir(parents=True, exist_ok=True)
    return app_support


def is_frozen() -> bool:
    """Check if we're running from a PyInstaller bundle."""
    return hasattr(sys, '_MEIPASS')
