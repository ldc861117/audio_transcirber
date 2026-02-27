import unittest
import numpy as np
from speaker_v2 import aggregate_embeddings, smart_threshold, cosine_similarity

class TestDiarization(unittest.TestCase):
    def test_aggregate_embeddings(self):
        emb1 = np.array([1.0, 0.0])
        emb2 = np.array([0.0, 1.0])
        avg = aggregate_embeddings([emb1, emb2])
        # Expected: normalized [0.5, 0.5] -> [0.7071, 0.7071]
        expected = np.array([0.70710678, 0.70710678])
        np.testing.assert_array_almost_equal(avg, expected)

    def test_aggregate_embeddings_none(self):
        self.assertIsNone(aggregate_embeddings([]))
        self.assertIsNone(aggregate_embeddings([None]))

    def test_smart_threshold_clear_winner(self):
        emb = np.array([1.0, 0.0])
        candidates = [
            {'similarity': 0.85, 'name': 'Alice'},
            {'similarity': 0.60, 'name': 'Bob'}
        ]
        threshold = smart_threshold(emb, candidates)
        # diff = 0.25 > 0.15, returns max(0.60, 0.85 - 0.05) = 0.80
        self.assertAlmostEqual(threshold, 0.80)

    def test_smart_threshold_close_call(self):
        emb = np.array([1.0, 0.0])
        candidates = [
            {'similarity': 0.75, 'name': 'Alice'},
            {'similarity': 0.73, 'name': 'Bob'}
        ]
        threshold = smart_threshold(emb, candidates)
        # diff = 0.02 < 0.03, returns min(0.85, 0.75 + 0.05) = 0.80
        self.assertAlmostEqual(threshold, 0.80)

    def test_cosine_similarity(self):
        a = np.array([1.0, 0.0])
        b = np.array([1.0, 0.0])
        self.assertAlmostEqual(cosine_similarity(a, b), 1.0)
        
        c = np.array([0.0, 1.0])
        self.assertAlmostEqual(cosine_similarity(a, c), 0.0)

if __name__ == '__main__':
    unittest.main()
