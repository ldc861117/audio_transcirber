import os
import uuid
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Persistent storage under project data/ directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RECORDINGS_DIR = _PROJECT_ROOT / "data" / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


class RecordingSession:
    """Manages a single recording session with incremental chunk storage."""

    def __init__(self, user_id: int, session_id: str | None = None):
        self.user_id = user_id
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.session_dir = RECORDINGS_DIR / str(user_id) / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._chunk_count = self._count_existing_chunks()

    def _count_existing_chunks(self) -> int:
        """Count existing chunk files to support resuming."""
        return len(list(self.session_dir.glob("chunk_*.webm")))

    @property
    def chunk_count(self) -> int:
        return self._chunk_count

    def save_chunk(self, chunk_data: bytes) -> dict:
        """Save a single chunk to disk. Returns chunk metadata."""
        chunk_path = self.session_dir / f"chunk_{self._chunk_count:04d}.webm"
        chunk_path.write_bytes(chunk_data)
        size_bytes = len(chunk_data)
        self._chunk_count += 1

        # Calculate total session size
        total_size = sum(
            f.stat().st_size for f in self.session_dir.glob("chunk_*.webm")
        )

        return {
            "chunk_index": self._chunk_count - 1,
            "chunk_size_bytes": size_bytes,
            "total_chunks": self._chunk_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def finalize(self) -> dict:
        """Concatenate all chunks into a single file using ffmpeg concat."""
        chunk_files = sorted(self.session_dir.glob("chunk_*.webm"))

        if not chunk_files:
            raise ValueError("No chunks found to finalize")

        # Output file sits alongside the session directory
        output_path = self.session_dir.parent / f"{self.session_id}.webm"

        if len(chunk_files) == 1:
            # Single chunk: just move it
            shutil.move(str(chunk_files[0]), str(output_path))
        else:
            # Multiple chunks: use ffmpeg concat demuxer
            concat_list = self.session_dir / "concat_list.txt"
            with open(concat_list, "w") as f:
                for chunk in chunk_files:
                    f.write(f"file '{chunk.resolve()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg concat failed: {result.stderr[:500]}")

        # Get file info
        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        # Clean up chunk directory
        shutil.rmtree(self.session_dir, ignore_errors=True)

        return {
            "session_id": self.session_id,
            "file_path": str(output_path),
            "size_mb": round(file_size_mb, 2),
            "total_chunks_merged": len(chunk_files),
        }

    @staticmethod
    def get_session_dir(user_id: int, session_id: str) -> Path | None:
        """Check if a session directory exists."""
        session_dir = RECORDINGS_DIR / str(user_id) / session_id
        return session_dir if session_dir.is_dir() else None

    @staticmethod
    def cleanup_stale_sessions(user_id: int, max_age_hours: int = 24):
        """Remove session directories older than max_age_hours."""
        user_dir = RECORDINGS_DIR / str(user_id)
        if not user_dir.exists():
            return
        now = datetime.now(timezone.utc).timestamp()
        for session_dir in user_dir.iterdir():
            if session_dir.is_dir():
                age_hours = (now - session_dir.stat().st_mtime) / 3600
                if age_hours > max_age_hours:
                    shutil.rmtree(session_dir, ignore_errors=True)
