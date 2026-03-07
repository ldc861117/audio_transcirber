import unittest
from backend.app import create_app

class TestTranscriptionAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.client = self.app.test_client()

    def test_health_check(self):
        response = self.client.get('/api/v2/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_transcription_upload_no_file(self):
        # Should return 400 Bad Request
        response = self.client.post('/api/v2/transcriptions/upload')
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json)

    def test_providers_list(self):
        response = self.client.get('/api/v2/transcriptions/providers')
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json)

if __name__ == '__main__':
    unittest.main()
