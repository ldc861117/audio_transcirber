"""V1 compatibility shim — re-exports Task model from V2 backend.tasks.models.

app.py imports `from models.task import Task`. Phase 1 moved models to
backend/tasks/models.py and deleted this file.
"""
try:
    from backend.tasks.models import Task  # noqa: F401
except ImportError:
    Task = None
