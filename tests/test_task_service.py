"""
Tests for TaskService.
"""

import os
import unittest
from services.task_service import TaskService
from db.task_db import DB_PATH

class TestTaskService(unittest.TestCase):
    def setUp(self):
        # Ensure a clean database for each test
        if DB_PATH.exists():
            DB_PATH.unlink()
        from db.task_db import init_task_db
        init_task_db()

    def tearDown(self):
        if DB_PATH.exists():
            DB_PATH.unlink()

    def test_create_and_get_task(self):
        task_id = "test_task_1"
        user_id = 1
        TaskService.create_task(task_id, user_id, "test.mp3", 10.5)
        
        task = TaskService.get_task(task_id, user_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["id"], task_id)
        self.assertEqual(task["filename"], "test.mp3")
        self.assertEqual(task["file_size_mb"], 10.5)
        self.assertEqual(task["status"], "queued")

    def test_update_task(self):
        task_id = "test_task_2"
        user_id = 1
        TaskService.create_task(task_id, user_id, "test.mp3", 10.5)
        
        TaskService.update_task(task_id, status="done", transcript="Hello world")
        
        task = TaskService.get_task(task_id, user_id)
        self.assertEqual(task["status"], "done")
        self.assertEqual(task["transcript"], "Hello world")

    def test_list_tasks_and_search(self):
        user_id = 1
        TaskService.create_task("task1", user_id, "apple.mp3", 1.0)
        TaskService.create_task("task2", user_id, "banana.mp3", 2.0)
        
        # List all
        res = TaskService.list_tasks(user_id)
        self.assertEqual(res["total"], 2)
        
        # Search
        res = TaskService.list_tasks(user_id, search="apple")
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["filename"], "apple.mp3")

    def test_user_isolation(self):
        TaskService.create_task("task_user1", 1, "file1.mp3", 1.0)
        TaskService.create_task("task_user2", 2, "file2.mp3", 1.0)
        
        # User 1 should not see User 2's task
        task = TaskService.get_task("task_user2", 1)
        self.assertIsNone(task)
        
        res = TaskService.list_tasks(1)
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["id"], "task_user1")

    def test_delete_task(self):
        task_id = "task_to_delete"
        user_id = 1
        TaskService.create_task(task_id, user_id, "test.mp3", 1.0)
        
        self.assertTrue(TaskService.delete_task(task_id, user_id))
        self.assertIsNone(TaskService.get_task(task_id, user_id))

if __name__ == "__main__":
    unittest.main()
