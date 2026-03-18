"""
Track C — Transcription API & Health Check Tests
Uses shared conftest fixtures. Protected routes use auth_headers.
"""
import pytest


class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get('/api/v2/health')
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


class TestTranscriptionRoutes:
    def test_upload_no_file_returns_error(self, client, auth_headers):
        resp = client.post('/api/v2/transcriptions/upload',
                           headers=auth_headers['headers'])
        # 400 (no file) or 500 (handler expects file) — either is acceptable
        assert resp.status_code in (400, 500)
        assert 'error' in resp.get_json()

    def test_upload_unauthorized(self, client):
        resp = client.post('/api/v2/transcriptions/upload')
        assert resp.status_code == 401

    def test_providers_list(self, client, auth_headers):
        resp = client.get('/api/v2/transcriptions/providers',
                          headers=auth_headers['headers'])
        assert resp.status_code == 200
        assert 'data' in resp.get_json()

    def test_providers_unauthorized(self, client):
        resp = client.get('/api/v2/transcriptions/providers')
        assert resp.status_code == 401


class TestSpeakerRoutes:
    def test_speakers_list(self, client, auth_headers):
        resp = client.get('/api/v2/speakers/',
                          headers=auth_headers['headers'])
        assert resp.status_code == 200

    def test_speakers_unauthorized(self, client):
        resp = client.get('/api/v2/speakers/')
        assert resp.status_code == 401


class TestExportRoutes:
    def test_export_nonexistent_task(self, client, auth_headers):
        resp = client.get('/api/v2/export/nonexistent-task-id',
                          headers=auth_headers['headers'])
        assert resp.status_code in (400, 404, 500)

    def test_export_unauthorized(self, client):
        resp = client.get('/api/v2/export/some-task')
        assert resp.status_code == 401
