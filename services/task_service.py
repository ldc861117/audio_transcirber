"""V1 compatibility shim — re-exports TaskService from V2 backend.tasks.service.

The V1 monolith (app.py) imports `from services.task_service import TaskService`.
Phase 1 moved TaskService to backend/tasks/service.py and deleted this file.
This shim restores compatibility so the desktop app can start.
"""
try:
    from backend.tasks.service import TaskService  # noqa: F401
except ImportError:
    # If backend.tasks isn't available (e.g., pure V1 env), provide a stub
    class TaskService:
        """Stub TaskService when V2 backend is unavailable."""
        @staticmethod
        def create_task(**kwargs): pass
        @staticmethod
        def get_task(task_id, user_id): return None
        @staticmethod
        def list_tasks(**kwargs): return {"items": [], "total": 0}
        @staticmethod
        def update_task(task_id, user_id, **kwargs): pass
