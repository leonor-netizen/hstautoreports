import unittest

from scripts.export_sheet_pdf import build_export_url, parse_google_sheet_url


class ExportSheetPdfTests(unittest.TestCase):
    def test_parse_google_sheet_url_with_query_gid(self):
        url = "https://docs.google.com/spreadsheets/d/abc123/edit?gid=999#gid=999"
        sheet_id, gid = parse_google_sheet_url(url)
        self.assertEqual(sheet_id, "abc123")
        self.assertEqual(gid, "999")

    def test_parse_google_sheet_url_with_fragment_gid(self):
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=777"
        sheet_id, gid = parse_google_sheet_url(url)
        self.assertEqual(sheet_id, "abc123")
        self.assertEqual(gid, "777")

    def test_build_export_url(self):
        export_url = build_export_url("abc123", "42")
        self.assertIn("/spreadsheets/d/abc123/export?", export_url)
        self.assertIn("format=pdf", export_url)
        self.assertIn("gid=42", export_url)


if __name__ == "__main__":
    unittest.main()
