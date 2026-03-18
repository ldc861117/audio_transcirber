import pytest
from flask import Flask
from backend.db.base import db, init_db
from backend.auth.models import User
from backend.tasks.service import TaskService
from backend.tasks.models import Task

# Need to import Subscription to satisfy User model relationship
from backend.subscriptions.models import Subscription

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    init_db(app)
    return app

@pytest.fixture(autouse=True)
def setup_database(app):
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(username="testuser", email="test@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        yield
        db.session.remove()
        db.drop_all()

def test_create_task(app):
    with app.app_context():
        user = User.query.first()
        task = TaskService.create_task(
            task_id="task123",
            user_id=user.id,
            filename="test.mp3",
            file_size_mb=1.5,
            provider="openai",
            model="whisper-1"
        )

        assert task.id == "task123"
        assert task.user_id == user.id
        assert task.filename == "test.mp3"
        assert task.status == "queued"

def test_get_task(app):
    with app.app_context():
        user = User.query.first()
        TaskService.create_task("task123", user.id, "test.mp3", 1.5)

        task = TaskService.get_task("task123", user.id)
        assert task is not None
        assert task.id == "task123"

        # Test wrong user
        task_wrong_user = TaskService.get_task("task123", 999)
        assert task_wrong_user is None

def test_update_task(app):
    with app.app_context():
        user = User.query.first()
        TaskService.create_task("task123", user.id, "test.mp3", 1.5)

        success = TaskService.update_task("task123", user.id, status="done", transcript="Hello world")
        assert success is True

        task = TaskService.get_task("task123", user.id)
        assert task.status == "done"
        assert task.transcript == "Hello world"

def test_list_tasks(app):
    with app.app_context():
        user = User.query.first()
        TaskService.create_task("task1", user.id, "test1.mp3", 1.0)
        TaskService.create_task("task2", user.id, "test2.mp3", 2.0)

        result = TaskService.list_tasks(user.id)
        assert len(result["items"]) == 2
        assert result["total"] == 2

def test_delete_task(app):
    with app.app_context():
        user = User.query.first()
        TaskService.create_task("task123", user.id, "test.mp3", 1.5)

        success = TaskService.delete_task("task123", user.id)
        assert success is True

        task = TaskService.get_task("task123", user.id)
        assert task is None
