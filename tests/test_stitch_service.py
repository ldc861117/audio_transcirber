"""
Tests for StitchService — LLM-based overlap transcript stitching.
"""

import unittest
from unittest.mock import MagicMock, patch, call


class TestStitchService(unittest.TestCase):

    def _make_mock_client(self, return_text: str):
        """Create a mock OpenAI-style client that returns `return_text`."""
        client = MagicMock()
        choice = MagicMock()
        choice.message.content = return_text
        response = MagicMock()
        response.choices = [choice]
        client.chat.completions.create.return_value = response
        return client

    # ── stitch_pair ──────────────────────────────────────────────

    def test_stitch_pair_calls_llm(self):
        from services.stitch_service import stitch_pair
        expected = "完整拼接后的文本"
        client = self._make_mock_client(expected)

        result = stitch_pair("前半段文本", "后半段文本", client, "test-model")

        self.assertEqual(result, expected)
        client.chat.completions.create.assert_called_once()
        kwargs = client.chat.completions.create.call_args
        self.assertEqual(kwargs.kwargs["model"], "test-model")
        # Verify prompt contains both texts
        user_msg = kwargs.kwargs["messages"][1]["content"]
        self.assertIn("前半段文本", user_msg)
        self.assertIn("后半段文本", user_msg)

    # ── stitch_transcripts ───────────────────────────────────────

    def test_empty_list_returns_empty(self):
        from services.stitch_service import stitch_transcripts
        client = self._make_mock_client("")
        self.assertEqual(stitch_transcripts([], client, "m"), "")

    def test_single_transcript_returns_as_is(self):
        from services.stitch_service import stitch_transcripts
        client = self._make_mock_client("")
        self.assertEqual(stitch_transcripts(["hello"], client, "m"), "hello")
        client.chat.completions.create.assert_not_called()

    def test_two_transcripts_calls_llm_once(self):
        from services.stitch_service import stitch_transcripts
        merged = "A和B拼接后的结果"
        client = self._make_mock_client(merged)

        result = stitch_transcripts(["片段A", "片段B"], client, "test-model")

        self.assertEqual(result, merged)
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_three_transcripts_calls_llm_twice(self):
        from services.stitch_service import stitch_transcripts
        client = MagicMock()

        # First call returns A+B merged, second call returns A+B+C merged
        choice1 = MagicMock()
        choice1.message.content = "AB合并"
        resp1 = MagicMock()
        resp1.choices = [choice1]

        choice2 = MagicMock()
        choice2.message.content = "ABC合并"
        resp2 = MagicMock()
        resp2.choices = [choice2]

        client.chat.completions.create.side_effect = [resp1, resp2]

        result = stitch_transcripts(["A", "B", "C"], client, "m")

        self.assertEqual(result, "ABC合并")
        self.assertEqual(client.chat.completions.create.call_count, 2)

    def test_filters_empty_transcripts(self):
        from services.stitch_service import stitch_transcripts
        client = self._make_mock_client("merged")

        # Empty strings and whitespace-only should be filtered
        result = stitch_transcripts(["hello", "", "   ", "world"], client, "m")

        self.assertEqual(result, "merged")
        # Only one valid pair (hello, world), so 1 call
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_all_empty_returns_empty(self):
        from services.stitch_service import stitch_transcripts
        client = self._make_mock_client("")
        result = stitch_transcripts(["", "  ", ""], client, "m")
        self.assertEqual(result, "")
        client.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
