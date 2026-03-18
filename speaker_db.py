"""V1 compatibility shim — re-exports SpeakerDB from V2 backend.speakers.db.

app.py imports `from speaker_db import SpeakerDB`. Phase 1 moved this to
backend/speakers/db.py and deleted the original file.
"""
try:
    from backend.speakers.db import SpeakerDB  # noqa: F401
except ImportError:
    # Stub for environments where backend is unavailable
    class SpeakerDB:
        """Stub SpeakerDB when V2 backend is unavailable."""
        def __init__(self, *args, **kwargs): pass
        def get_speakers(self, *args, **kwargs): return []
        def add_speaker(self, *args, **kwargs): pass
        def rename_speaker(self, *args, **kwargs): pass
