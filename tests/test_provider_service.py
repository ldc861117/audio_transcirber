import unittest
import os
from services.provider_service import ProviderService

class TestProviderService(unittest.TestCase):
    def setUp(self):
        self.ps = ProviderService()

    def test_load_config(self):
        config = self.ps.get_all_providers()
        self.assertIn('gemini', config)
        self.assertIn('zhipu', config)

    def test_get_model_limits(self):
        # Known model
        limits = self.ps.get_model_limits('gemini', 'gemini-3-flash-preview')
        self.assertEqual(limits['max_input_mb'], 100.0)
        self.assertEqual(limits['max_input_minutes'], 120.0)

        # Another known model
        limits = self.ps.get_model_limits('zhipu', 'glm-asr-2512')
        self.assertEqual(limits['max_input_mb'], 25.0)
        self.assertEqual(limits['max_input_minutes'], 30.0)

        # Unknown model
        limits = self.ps.get_model_limits('gemini', 'unknown-model')
        self.assertEqual(limits['max_input_mb'], 20.0)
        self.assertEqual(limits['max_input_minutes'], 10.0)

    def test_get_optimal_chunk_params(self):
        # Small file + Gemini 3 -> skip_split=True
        params = self.ps.get_optimal_chunk_params('gemini', 'gemini-3-flash-preview', 50.0, 60.0)
        self.assertTrue(params['skip_split'])
        self.assertEqual(params['max_minutes'], 120)
        self.assertEqual(params['max_mb'], 100)

        # Large file + Gemini 3 -> skip_split=False
        params = self.ps.get_optimal_chunk_params('gemini', 'gemini-3-flash-preview', 150.0, 60.0)
        self.assertFalse(params['skip_split'])

        # Long duration + Gemini 3 -> skip_split=False
        params = self.ps.get_optimal_chunk_params('gemini', 'gemini-3-flash-preview', 50.0, 150.0)
        self.assertFalse(params['skip_split'])

        # Normal file + Old model -> skip_split depends on limits
        params = self.ps.get_optimal_chunk_params('gemini', 'gemini-2.5-flash', 10.0, 5.0)
        self.assertTrue(params['skip_split'])
        
        params = self.ps.get_optimal_chunk_params('gemini', 'gemini-2.5-flash', 30.0, 5.0)
        self.assertFalse(params['skip_split'])

    def test_has_server_key(self):
        # Mock environment variable
        os.environ['GEMINI_API_KEY'] = 'test-key'
        self.assertTrue(self.ps.has_server_key('gemini'))
        
        if 'ZHIPU_API_KEY' in os.environ:
            del os.environ['ZHIPU_API_KEY']
        self.assertFalse(self.ps.has_server_key('zhipu'))

if __name__ == '__main__':
    unittest.main()
