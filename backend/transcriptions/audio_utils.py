import os
import uuid
import tempfile
import shutil
from pathlib import Path
from pydub import AudioSegment

# All audio formats supported by ffmpeg / pydub
SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a",
    ".wma", ".aiff", ".aif", ".opus", ".amr", ".ape",
    ".ac3", ".webm", ".caf", ".spx", ".oga", ".wv",
    ".mp4", ".mov", ".mkv",  # video files with audio track
}

UPLOAD_DIR = Path(tempfile.gettempdir()) / "audio_transcriber_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DEFAULT_MAX_CHUNK_MINUTES = 60       # minutes per chunk
DEFAULT_MAX_CHUNK_MB      = 100      # MB per chunk

def _setup_ffmpeg():
    """Locate ffmpeg and ffprobe, set pydub paths explicitly."""
    search_dirs = [
        "/opt/homebrew/bin",       # Apple Silicon Homebrew
        "/usr/local/bin",          # Intel Homebrew / manual install
        "/usr/bin",                # system
    ]
    for name, attr in [("ffmpeg", "converter"), ("ffprobe", "ffprobe")]:
        # Already findable?
        if shutil.which(name):
            continue
        for d in search_dirs:
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                if attr == "converter":
                    AudioSegment.converter = candidate
                else:
                    AudioSegment.ffprobe = candidate
                break

_setup_ffmpeg()

def split_audio(filepath: str, max_minutes: int, max_mb: int, preferred_format: str = "mp3") -> list[str]:
    """
    Split an audio file by duration AND file-size constraints.
    Returns a list of temporary file paths for each chunk.
    """
    audio = AudioSegment.from_file(filepath)
    fmt = preferred_format if preferred_format in ["mp3", "m4a"] else "mp3"

    chunk_ms = max_minutes * 60 * 1000
    chunks_by_time: list[AudioSegment] = []

    # First pass: split by time
    for start in range(0, len(audio), chunk_ms):
        chunks_by_time.append(audio[start:start + chunk_ms])

    # Second pass: further split any chunk that exceeds max_mb
    final_chunks: list[AudioSegment] = []
    for chunk in chunks_by_time:
        tmp = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
        chunk.export(tmp.name, format=fmt)
        tmp.close()
        size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        os.unlink(tmp.name)

        if size_mb <= max_mb:
            final_chunks.append(chunk)
        else:
            # Binary-split until every piece fits
            sub_chunks = _binary_split(chunk, fmt, max_mb)
            final_chunks.extend(sub_chunks)

    # Export final chunks
    paths: list[str] = []
    for i, chunk in enumerate(final_chunks):
        out = UPLOAD_DIR / f"{uuid.uuid4().hex}_{i}.{fmt}"
        chunk.export(str(out), format=fmt)
        paths.append(str(out))
    return paths


def _binary_split(segment: AudioSegment, fmt: str, max_mb: int) -> list[AudioSegment]:
    """Recursively halve a segment until each piece is <= max_mb."""
    tmp = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
    segment.export(tmp.name, format=fmt)
    tmp.close()
    size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
    os.unlink(tmp.name)

    if size_mb <= max_mb:
        return [segment]
    mid = len(segment) // 2
    return _binary_split(segment[:mid], fmt, max_mb) + \
           _binary_split(segment[mid:], fmt, max_mb)
