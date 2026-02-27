import unittest
import io
from services.export_service import ExportService

class TestExportService(unittest.TestCase):
    def setUp(self):
        self.service = ExportService()
        self.transcript = "Hello world.\nThis is a test."
        self.speakers = [
            {
                "label": "Speaker 1",
                "segments": [
                    {"start": 0.0, "end": 2.5, "text": "Hello world."}
                ]
            },
            {
                "label": "Speaker 2",
                "segments": [
                    {"start": 2.5, "end": 5.0, "text": "This is a test."}
                ]
            }
        ]
        self.metadata = {"filename": "test_audio", "file_size_mb": 1.2}

    def test_export_srt_with_speakers(self):
        srt = self.service.export_srt(self.transcript, self.speakers)
        self.assertIn("1", srt)
        self.assertIn("00:00:00,000 --> 00:00:02,500", srt)
        self.assertIn("【Speaker 1】Hello world.", srt)
        self.assertIn("2", srt)
        self.assertIn("00:00:02,500 --> 00:00:05,000", srt)
        self.assertIn("【Speaker 2】This is a test.", srt)

    def test_export_srt_without_speakers(self):
        srt = self.service.export_srt(self.transcript)
        self.assertIn("1", srt)
        self.assertIn("00:00:00,000 --> 00:00:05,000", srt)
        # It splits by \n\n usually, our transcript has \n.
        # Let's adjust transcript to have \n\n for this test
        srt2 = self.service.export_srt("Part 1\n\nPart 2")
        self.assertIn("1", srt2)
        self.assertIn("Part 1", srt2)
        self.assertIn("2", srt2)
        self.assertIn("Part 2", srt2)

    def test_export_word(self):
        docx_bytes = self.service.export_word(self.transcript, self.metadata, self.speakers)
        self.assertIsInstance(docx_bytes, bytes)
        self.assertTrue(len(docx_bytes) > 0)
        # Word files are zip files, they start with PK
        self.assertTrue(docx_bytes.startswith(b"PK"))

    def test_export_pdf(self):
        pdf_bytes = self.service.export_pdf(self.transcript, self.metadata, self.speakers)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_degraded_handling(self):
        # No speakers, no metadata
        docx_bytes = self.service.export_word(self.transcript)
        self.assertTrue(docx_bytes.startswith(b"PK"))
        
        pdf_bytes = self.service.export_pdf(self.transcript)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

if __name__ == "__main__":
    unittest.main()
